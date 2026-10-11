"""Reject paths outside self-created, disposable M1-A synthetic fixtures."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile


MARKER = ".m1a-probe-owned.json"
TEMP = Path(tempfile.gettempdir()).resolve()
REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "docs" / "planning" / "evidence" / "M1-A-PROBE"


def _no_links(path: Path, stop: Path) -> None:
    current = path
    while True:
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError("LINK_OR_JUNCTION_DENIED")
        if current == stop:
            break
        if current == current.parent:
            raise ValueError("PATH_OUTSIDE_ALLOWED_ROOT")
        current = current.parent


def register_fixture(root: Path) -> None:
    root = root.absolute()
    _no_links(root, Path(root.anchor))
    root = root.resolve()
    if root.parent != TEMP or not root.name.startswith("m1a-synthetic-"):
        raise ValueError("NOT_EXCLUSIVE_TEMP_FIXTURE")
    _no_links(root, Path(root.anchor))
    marker = root / MARKER
    if not root.is_dir() or any(root.iterdir()):
        raise ValueError("FIXTURE_ALREADY_REGISTERED")
    marker.write_text(json.dumps({"kind": "M1A_SYNTHETIC_V1", "root": str(root),
                                  "run_id": os.environ.get("M1A_PROBE_RUN_ID", "TRANSIENT")}), encoding="utf-8")


def fixture_path(path: Path, *, expected_run_id: str | None = None) -> Path:
    path = path.absolute()
    _no_links(path, Path(path.anchor))
    path = path.resolve()
    candidate = path
    while candidate != TEMP and candidate != candidate.parent:
        if candidate.parent == TEMP and candidate.name.startswith("m1a-synthetic-"):
            root = candidate
            break
        candidate = candidate.parent
    else:
        raise ValueError("PATH_OUTSIDE_EXCLUSIVE_TEMP")
    _no_links(path, root)
    marker = root / MARKER
    if not marker.is_file() or marker.is_symlink():
        raise ValueError("UNREGISTERED_FIXTURE")
    data = json.loads(marker.read_text(encoding="utf-8"))
    if data != {"kind": "M1A_SYNTHETIC_V1", "root": str(root),
                "run_id": expected_run_id or os.environ.get("M1A_PROBE_RUN_ID", "TRANSIENT")}:
        raise ValueError("INVALID_FIXTURE_MARKER")
    return path


def guard_evidence_root(root: Path = EVIDENCE) -> Path:
    root = root.absolute()
    _no_links(root, Path(root.anchor))
    return root.resolve()


def evidence_sink(path: Path) -> Path:
    path = path.absolute()
    _no_links(path, Path(path.anchor))
    path = path.resolve()
    root = guard_evidence_root()
    if path.parent != root or not path.name.startswith("run-"):
        raise ValueError("EVIDENCE_DESTINATION_DENIED")
    _no_links(path, root)
    return path
