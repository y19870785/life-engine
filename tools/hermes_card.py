"""Run directly: python tools/hermes_card.py --help."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine.hermes_card_import import main

if __name__ == '__main__':
    raise SystemExit(main())
