"""Run E0 tests and preserve raw synthetic fixtures before test cleanup."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys


REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "docs" / "planning" / "evidence" / "M1-A-PROBE"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def main() -> int:
    if EVIDENCE.is_symlink() or (EVIDENCE.exists() and EVIDENCE.resolve() != EVIDENCE.absolute()):
        raise RuntimeError("evidence root is a symlink")
    evidence_root = EVIDENCE.resolve()
    evidence_root.mkdir(parents=True, exist_ok=True)
    run_name = datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    target = evidence_root / run_name
    target.mkdir(exist_ok=False)
    env = dict(os.environ)
    env["M1A_PROBE_EVIDENCE_ROOT"] = str(target)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, "-B", "-X", "utf8", "-m", "unittest", "discover",
           "-s", "tests", "-p", "test_m1a_probe_*.py", "-v"]
    result = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True, timeout=180)
    (target / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (target / "stderr.txt").write_text(result.stderr, encoding="utf-8")
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
        "exit_code": result.returncode,
        "files": files,
        "claim_limit": "E0 process behavior only; E1/E2/E3 and real admission NOT_PROVEN",
    }
    (target / "run-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(target)
    print(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
