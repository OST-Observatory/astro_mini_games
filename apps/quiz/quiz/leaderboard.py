"""Leaderboard for Astro-Quiz - persisted in JSON."""

import json
from datetime import datetime
from pathlib import Path

LEADERBOARD_PATH = Path.home() / ".local" / "share" / "astro_mini_games" / "quiz_leaderboard.json"
TOP_N = 10


def _ensure_dir():
    LEADERBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_leaderboard() -> list:
    """Load the leaderboard. Returns list of dicts: {name, points, correct, total, date}."""
    _ensure_dir()
    if not LEADERBOARD_PATH.exists():
        return []
    try:
        with open(LEADERBOARD_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("scores", [])
    except (json.JSONDecodeError, OSError):
        return []


def save_leaderboard(scores: list):
    """Save the leaderboard. scores: sorted by points descending."""
    _ensure_dir()
    with open(LEADERBOARD_PATH, "w", encoding="utf-8") as f:
        json.dump({"scores": scores}, f, ensure_ascii=False, indent=2)


def add_score(name: str, points: int, correct: int, total: int) -> int:
    """
    Add an entry and save. Returns the achieved rank (1-based).
    """
    name = (name or "Unbekannt").strip()[:50] or "Unbekannt"
    scores = load_leaderboard()
    entry = {
        "name": name,
        "points": points,
        "correct": correct,
        "total": total,
        "date": datetime.now().isoformat(),
    }
    scores.append(entry)
    scores.sort(key=lambda x: -x["points"])
    save_leaderboard(scores)
    for i, s in enumerate(scores, 1):
        if s == entry:
            return i
    return len(scores)


def get_top_scores(limit: int = TOP_N) -> list:
    """Return the top entries (already sorted)."""
    scores = load_leaderboard()
    return scores[:limit]
