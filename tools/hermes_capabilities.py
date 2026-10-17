"""Run the owner-managed character capability CLI."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine.hermes_capabilities import configure, main

if __name__ == '__main__':
    raise SystemExit(main())