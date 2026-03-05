"""Load stars and constellation data."""

import json
import random
from pathlib import Path


def load_config(path: Path = None) -> dict:
    """Load config.yaml."""
    if path is None:
        path = Path(__file__).parent.parent / "config.yaml"
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def load_stars(path: Path = None) -> list:
    """Load stars from stars.json."""
    if path is None:
        path = Path(__file__).parent.parent / "data" / "stars.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Constellations temporarily disabled (e.g. incomplete representation)
CONSTELLATIONS_DISABLED = ["Schlange"]


def load_constellations(path: Path = None) -> dict:
    """Load constellations from constellations.json."""
    if path is None:
        path = Path(__file__).parent.parent / "data" / "constellations.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if k not in CONSTELLATIONS_DISABLED}


def format_constellation_name(const_data: dict) -> str:
    """Returns the display name, e.g. 'Große Bärin (Ursa Major)'."""
    name = const_data.get("name", "")
    iau = const_data.get("iau_name", "")
    if iau:
        return f"{name} ({iau})"
    return name


def get_session_constellations(count: int, always_include: str = None) -> list:
    """
    Randomly select `count` constellations. If `always_include` is set
    (display format like 'Große Bärin (Ursa Major)'), that constellation
    is always included.
    """
    constellations = load_constellations()
    all_keys = list(constellations.keys())

    included_key = None
    if always_include:
        included_key = next(
            (k for k in all_keys
             if format_constellation_name(constellations[k]) == always_include),
            None
        )
    candidates = [c for c in all_keys if c != included_key]
    n_extra = max(0, count - (1 if included_key else 0))
    chosen = random.sample(candidates, min(n_extra, len(candidates)))
    result = ([included_key] if included_key else []) + chosen
    random.shuffle(result)
    return result


def get_star_ids_for_constellation(const_name: str) -> set:
    """Collect all star IDs that belong to a constellation."""
    constellations = load_constellations()
    data = constellations.get(const_name, {})
    pairs = data.get("star_pairs", [])
    ids = set()
    for a, b in pairs:
        ids.add(a)
        ids.add(b)
    return ids
