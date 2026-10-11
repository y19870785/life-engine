"""Losslessly package synthetic evidence after checking every raw-file hash."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

from isolation import evidence_sink, guard_evidence_root, guarded_files


ROOT = Path(__file__).resolve().parents[2] / "docs" / "planning" / "evidence" / "M1-A-PROBE"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pack(directory: Path) -> dict:
    guard_evidence_root()
    directory = evidence_sink(directory)
    if directory.is_symlink() or directory.parent != ROOT.absolute():
        raise RuntimeError("outside evidence root")
    manifest_path = directory / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    listed = {item["path"]: item["sha256"] for item in manifest["files"]}
    for name in listed:
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or "\\" in name or name != relative.as_posix():
            raise RuntimeError(f"unsafe manifest path: {name}")
    files = guarded_files(directory)
    actual = {p.relative_to(directory).as_posix() for p in files}
    for path in files:
        if not path.resolve().is_relative_to(directory.resolve()):
            raise RuntimeError(f"escaped evidence entry: {path}")
    if actual != set(listed) | {"run-manifest.json"}:
        raise RuntimeError(f"unlisted evidence files: {directory.name}")
    for name, expected in listed.items():
        if sha((directory / name).read_bytes()) != expected:
            raise RuntimeError(f"source checksum mismatch: {name}")
    archive = ROOT / f"{directory.name}.zip"
    if archive.exists() or archive.is_symlink():
        raise RuntimeError(f"archive already exists: {archive}")
    external = ROOT / f"{directory.name}.manifest.json"
    if external.exists() or external.is_symlink():
        raise RuntimeError(f"manifest already exists: {external}")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for name in sorted(actual):
            output.write(directory / name, arcname=name)
    with zipfile.ZipFile(archive) as check:
        if set(check.namelist()) != actual:
            raise RuntimeError("archive entry list mismatch")
        for name, expected in listed.items():
            if sha(check.read(name)) != expected:
                raise RuntimeError(f"archive checksum mismatch: {name}")
        if check.read("run-manifest.json") != manifest_path.read_bytes():
            raise RuntimeError("manifest bytes mismatch")
    external.write_bytes(manifest_path.read_bytes())
    return {"run": directory.name, "archive": archive.name, "sha256": sha(archive.read_bytes()),
            "entries": len(actual), "verified": True}


if __name__ == "__main__":
    print(json.dumps([pack(ROOT / name) for name in sys.argv[1:]], indent=2))
