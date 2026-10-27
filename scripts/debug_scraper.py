"""Run with python -m scripts.debug_scraper (or python scripts/debug_scraper.py)."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._diagnostics import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
