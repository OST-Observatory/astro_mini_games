"""Load star data for HR diagram."""

import csv
from pathlib import Path


def load_stars(path: Path = None) -> list:
    """Load stars from stars_hr.csv."""
    if path is None:
        path = Path(__file__).parent.parent / "data" / "stars_hr.csv"
    stars = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                stars.append({
                    "bv": float(row.get("bv", 0)),
                    "absmag": float(row.get("absmag", 0)),
                    "name": row.get("name", ""),
                    "spect": row.get("spect", ""),
                    "mass": row.get("mass", ""),
                    "lifetime": row.get("lifetime", ""),
                })
            except (ValueError, KeyError):
                pass
    return stars
