#!/usr/bin/env python3
"""Dependency-free entrypoint, also copied beside an agent's configuration."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "runtime"))
from life_engine.cli import main

if __name__ == "__main__":
    raise SystemExit(main(default_home=ROOT))
