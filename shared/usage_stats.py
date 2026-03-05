"""
Usage statistics - shared logic for wrapper and base_app.
"""

import json
from datetime import datetime
from pathlib import Path


def write_usage_stats(app_id: str, start_ts: float, end_ts: float):
    """Writes usage statistics to ~/.local/share/astro_mini_games/usage.jsonl"""
    data_dir = Path.home() / ".local" / "share" / "astro_mini_games"
    data_dir.mkdir(parents=True, exist_ok=True)
    usage_file = data_dir / "usage.jsonl"

    entry = {
        "app_id": app_id,
        "start": datetime.fromtimestamp(start_ts).isoformat(),
        "end": datetime.fromtimestamp(end_ts).isoformat(),
        "duration_sec": round(end_ts - start_ts, 1),
    }

    try:
        with open(usage_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"⚠ Statistik konnte nicht geschrieben werden: {e}")
