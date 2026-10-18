"""Unified character-story onboarding entry point."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine.character_onboarding import main

if __name__ == '__main__':
    raise SystemExit(main())
