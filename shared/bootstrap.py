"""
Bootstrap for apps - log redirect before Kivy import.
Each app main.py calls setup_logging() before the first Kivy import.
"""

import os
import sys
from pathlib import Path


def setup_logging():
    """Redirects stdout/stderr to astro.log (production, without --dev)."""
    if "--dev" in sys.argv or os.environ.get("ASTRO_DEV", "0") == "1":
        return
    log_dir = Path.home() / ".local" / "share" / "astro_mini_games"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "astro.log"
    try:
        log_file = open(log_path, "a", encoding="utf-8", buffering=1)
        sys.stdout = log_file
        sys.stderr = log_file
    except OSError:
        sys.stdout = open(os.devnull, "w")
        sys.stderr = sys.stdout
