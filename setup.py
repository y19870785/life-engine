#!/usr/bin/env python3
"""Run directly with Python 3.11+; not a pip setup.py."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'runtime'))
from life_engine.deploy_cli import main
if __name__ == '__main__':
    raise SystemExit(main(ROOT))
