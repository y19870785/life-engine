"""Run E0 tests and preserve raw synthetic fixtures before test cleanup."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import sqlite3
import subprocess
import sys
import uuid

from isolation import TEMP, evidence_sink, fixture_path, guard_evidence_root

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "docs" / "planning" / "evidence" / "M1-A-PROBE"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def source_hashes() -> dict[str, str]:
    sources = sorted((REPO / "tests" / "m1a_probe").glob("*.py"))
    sources.append(REPO / "tests" / "test_m1a_probe_primitives.py")
    return {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}


def stop_tree(process: subprocess.Popen) -> bool:
    stopped = False
    try:
        if os.name == "nt":
            stopped = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                     capture_output=True, text=True, timeout=10).returncode == 0
        else:
            os.killpg(process.pid, signal.SIGKILL)
            stopped = True
    except (OSError, subprocess.TimeoutExpired, ProcessLookupError):
        stopped = False
    if process.poll() is None and not stopped:
        try:
            process.kill()
        except OSError:
            pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        stopped = False
    return stopped


def preserve_leftovers(target: Path, before: set[Path], run_id: str) -> list[str]:
    copied = []
    for candidate in sorted(TEMP.glob("m1a-synthetic-*")):
        if candidate in before or not candidate.is_dir():
            continue
        try:
            fixture_path(candidate / ".m1a-probe-owned.json", expected_run_id=run_id)
        except (ValueError, OSError, KeyError):
            continue
        if any(p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())
               for p in candidate.rglob("*")):
            continue
        destination = target / "timeout-raw" / candidate.name
        shutil.copytree(candidate, destination, symlinks=False)
        copied.append(candidate.name)
    return copied


def process_identity(pid: int) -> dict | None:
    """Read process identity and liveness without signaling or terminating it."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class FileTime(ctypes.Structure):
            _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetProcessTimes.argtypes = (wintypes.HANDLE, ctypes.POINTER(FileTime),
                                           ctypes.POINTER(FileTime), ctypes.POINTER(FileTime),
                                           ctypes.POINTER(FileTime))
        kernel.GetProcessTimes.restype = wintypes.BOOL
        kernel.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel.GetExitCodeProcess.restype = wintypes.BOOL
        kernel.QueryFullProcessImageNameW.argtypes = (wintypes.HANDLE, wintypes.DWORD,
                                                      wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD))
        kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            code = ctypes.get_last_error()
            if code in (87, 1168):  # INVALID_PARAMETER / NOT_FOUND: the PID has exited.
                return None
            raise OSError(code, f"OpenProcess({pid}) failed")
        try:
            created = FileTime()
            discarded = [FileTime() for _ in range(3)]
            if not kernel.GetProcessTimes(handle, ctypes.byref(created),
                                          *(ctypes.byref(x) for x in discarded)):
                raise OSError(ctypes.get_last_error(), "GetProcessTimes failed")
            exit_code = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                raise OSError(ctypes.get_last_error(), "GetExitCodeProcess failed")
            image = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(image))
            if not kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)):
                raise OSError(ctypes.get_last_error(), "QueryFullProcessImageNameW failed")
            return {"pid": pid, "created": (created.high << 32) | created.low,
                    "image": image.value.casefold(), "active": exit_code.value == 259}
        finally:
            kernel.CloseHandle(handle)
    stat_path = Path("/proc") / str(pid) / "stat"
    try:
        stat = stat_path.read_text(encoding="ascii")
        image = os.readlink(Path("/proc") / str(pid) / "exe")
    except FileNotFoundError:
        return None
    fields = stat.rsplit(")", 1)[1].strip().split()
    return {"pid": pid, "created": fields[19], "image": image,
            "active": fields[0] not in ("Z", "X")}


def live_registered_workers(target: Path, run_id: str) -> list[int]:
    live = []
    ledger = target / "worker-ledger.jsonl"
    if not ledger.exists():
        return live
    for line in ledger.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["run_id"] != run_id or not record["identity"]:
            raise ValueError("WORKER_LEDGER_IDENTITY_MISMATCH")
        current = process_identity(int(record["identity"]["pid"]))
        if current is not None and current["active"] and all(
                current[key] == record["identity"][key] for key in ("pid", "created", "image")):
            live.append(current["pid"])
    return sorted(set(live))


def settle_and_preserve(target: Path, before: set[Path], run_id: str,
                        runner_stopped: bool) -> tuple[list[str], list[int], bool]:
    live = live_registered_workers(target, run_id)
    settled = runner_stopped and not live
    return (preserve_leftovers(target, before, run_id) if settled else []), live, settled


def main() -> int:
    evidence_root = guard_evidence_root()
    evidence_root.mkdir(parents=True, exist_ok=True)
    run_name = datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    target = evidence_root / run_name
    evidence_sink(target)
    target.mkdir(exist_ok=False)
    run_id = uuid.uuid4().hex
    env = dict(os.environ)
    env["M1A_PROBE_EVIDENCE_ROOT"] = str(target)
    env["M1A_PROBE_RUN_ID"] = run_id
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, "-B", "-X", "utf8", "-m", "unittest", "discover",
           "-s", "tests", "-p", "test_m1a_probe_*.py", "-v"]
    before = set(TEMP.glob("m1a-synthetic-*"))
    code_before = source_hashes()
    runner_timeout = min(180, max(1, int(os.environ.get("M1A_PROBE_COLLECT_TIMEOUT_SECONDS", "180"))))
    timeout = False
    stopped = False
    process = None
    stdout = ""
    stderr = ""
    error = None
    try:
        process = subprocess.Popen(cmd, cwd=REPO, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True,
                                   **({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt"
                                      else {"start_new_session": True}))
        try:
            stdout, stderr = process.communicate(timeout=runner_timeout)
            stopped = True
        except subprocess.TimeoutExpired as first:
            timeout = True
            stopped = stop_tree(process)
            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired as second:
                stopped = False
                stdout = second.stdout or first.stdout or ""
                stderr = second.stderr or first.stderr or ""
    except BaseException as exc:
        error = repr(exc)
        if process is not None and process.poll() is None:
            stopped = stop_tree(process)
    finally:
        if process is not None and process.poll() is None:
            stopped = False
        try:
            leftovers, live_workers, stopped = settle_and_preserve(target, before, run_id, stopped)
        except BaseException as exc:
            leftovers = []
            live_workers = []
            stopped = False
            error = f"{error or ''}; preservation: {exc!r}"
        try:
            code_after = source_hashes()
        except BaseException as exc:
            code_after = {}
            error = f"{error or ''}; source hash: {exc!r}"
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        (target / "stdout.txt").write_text(stdout or "", encoding="utf-8")
        (target / "stderr.txt").write_text(stderr or "", encoding="utf-8")
        files = []
        for item in sorted(target.rglob("*")):
            if item.is_file() and item.name != "run-manifest.json":
                files.append({"path": item.relative_to(target).as_posix(),
                              "sha256": hashlib.sha256(item.read_bytes()).hexdigest(),
                              "size": item.stat().st_size})
        manifest = {
            "kind": "M1-A_SYNTHETIC_E0_ONLY",
            "base": "ca16d19e33bc274b0d3ac984c9761abb5a60e946",
            "worktree_head_before_commit": git("rev-parse", "HEAD"),
            "working_tree_clean": git("status", "--porcelain") == "",
            "run_id": run_id,
            "utc": datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(), "python": sys.version,
            "sqlite": sqlite3.sqlite_version, "sqlite_vfs": "default sqlite3 VFS; exact VFS name not exposed",
            "filesystem": "local temporary directory; physical filesystem not established",
            "program": cmd,
            "runner_timeout_seconds": runner_timeout,
            "exit_code": process.returncode if process is not None else None,
            "timed_out": timeout,
            "worker_tree_stopped": stopped,
            "live_registered_workers": live_workers,
            "leftover_fixture_copies": leftovers,
            "error": error,
            "source_sha256_before": code_before,
            "source_sha256_after": code_after,
            "source_unchanged": code_before == code_after,
            "files": files,
            "claim_limit": "E0 process behavior only; E1/E2/E3 and real admission NOT_PROVEN",
        }
        (target / "run-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(target)
    print(stderr)
    return 1 if timeout or not stopped or error or code_before != code_after else process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
