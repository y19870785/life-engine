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

from isolation import TEMP, evidence_sink, fixture_path

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "docs" / "planning" / "evidence" / "M1-A-PROBE"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def source_hashes() -> dict[str, str]:
    sources = sorted((REPO / "tests" / "m1a_probe").glob("*.py"))
    sources.append(REPO / "tests" / "test_m1a_probe_primitives.py")
    return {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}


def stop_tree(process: subprocess.Popen) -> bool:
    if os.name == "nt":
        stopped = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                 capture_output=True, text=True, timeout=10).returncode == 0
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
            stopped = True
        except ProcessLookupError:
            stopped = True
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        stopped = False
    return stopped


def preserve_leftovers(target: Path, before: set[Path]) -> list[str]:
    copied = []
    for candidate in sorted(TEMP.glob("m1a-synthetic-*")):
        if candidate in before or not candidate.is_dir():
            continue
        try:
            fixture_path(candidate / ".m1a-probe-owned.json")
        except (ValueError, OSError, KeyError):
            continue
        if any(p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())
               for p in candidate.rglob("*")):
            continue
        destination = target / "timeout-raw" / candidate.name
        shutil.copytree(candidate, destination, symlinks=False)
        copied.append(candidate.name)
    return copied


def main() -> int:
    if EVIDENCE.is_symlink() or (EVIDENCE.exists() and EVIDENCE.resolve() != EVIDENCE.absolute()):
        raise RuntimeError("evidence root is a symlink")
    evidence_root = EVIDENCE.resolve()
    evidence_root.mkdir(parents=True, exist_ok=True)
    run_name = datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    target = evidence_root / run_name
    evidence_sink(target)
    target.mkdir(exist_ok=False)
    env = dict(os.environ)
    env["M1A_PROBE_EVIDENCE_ROOT"] = str(target)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, "-B", "-X", "utf8", "-m", "unittest", "discover",
           "-s", "tests", "-p", "test_m1a_probe_*.py", "-v"]
    before = set(TEMP.glob("m1a-synthetic-*"))
    code_before = source_hashes()
    timeout = False
    process = subprocess.Popen(cmd, cwd=REPO, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True,
                               **({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt"
                                  else {"start_new_session": True}))
    try:
        stdout, stderr = process.communicate(timeout=180)
        stopped = True
    except subprocess.TimeoutExpired as exc:
        timeout = True
        stopped = stop_tree(process)
        stdout, stderr = process.communicate(timeout=10)
        prior_out = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        prior_err = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        stdout = prior_out + (stdout or "")
        stderr = prior_err + (stderr or "")
    leftovers = preserve_leftovers(target, before) if stopped else []
    code_after = source_hashes()
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
        "utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "python": sys.version,
        "sqlite": sqlite3.sqlite_version, "sqlite_vfs": "default sqlite3 VFS; exact VFS name not exposed",
        "filesystem": "local temporary directory; physical filesystem not established",
        "program": cmd,
        "exit_code": process.returncode,
        "timed_out": timeout,
        "worker_tree_stopped": stopped,
        "leftover_fixture_copies": leftovers,
        "source_sha256_before": code_before,
        "source_sha256_after": code_after,
        "source_unchanged": code_before == code_after,
        "files": files,
        "claim_limit": "E0 process behavior only; E1/E2/E3 and real admission NOT_PROVEN",
    }
    (target / "run-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(target)
    print(stderr)
    return 1 if timeout or not stopped or code_before != code_after else process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
