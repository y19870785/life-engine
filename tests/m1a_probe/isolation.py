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
        if current.exists() and current.resolve() != current.absolute():
            raise ValueError("PATH_ALIAS_DENIED")
        if current == stop:
            break
        if current == current.parent:
            raise ValueError("PATH_OUTSIDE_ALLOWED_ROOT")
        current = current.parent


def register_fixture(root: Path) -> None:
    root = root.absolute()
    if root.parent != TEMP or not root.name.startswith("m1a-synthetic-"):
        raise ValueError("NOT_EXCLUSIVE_TEMP_FIXTURE")
    _no_links(root, TEMP)
    marker = root / MARKER
    if marker.exists():
        raise ValueError("FIXTURE_ALREADY_REGISTERED")
    marker.write_text(json.dumps({"kind": "M1A_SYNTHETIC_V1", "root": str(root)}), encoding="utf-8")


def fixture_path(path: Path) -> Path:
    path = path.absolute()
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
    if data != {"kind": "M1A_SYNTHETIC_V1", "root": str(root)}:
        raise ValueError("INVALID_FIXTURE_MARKER")
    return path


def evidence_sink(path: Path) -> Path:
    path = path.absolute()
    root = EVIDENCE.absolute()
    if root.exists() and root.resolve() != root:
        raise ValueError("EVIDENCE_ROOT_ALIAS_DENIED")
    if path.parent != root or not path.name.startswith("run-"):
        raise ValueError("EVIDENCE_DESTINATION_DENIED")
    _no_links(path, root)
    return path
