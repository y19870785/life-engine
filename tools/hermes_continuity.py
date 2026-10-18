"""Run the trusted local roleplay continuity service CLI."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from life_engine.character_continuity import main

if __name__ == '__main__':
    raise SystemExit(main())
