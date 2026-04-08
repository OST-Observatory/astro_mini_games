"""Load stars and constellation data."""

import json
import random
import unicodedata
from pathlib import Path

import yaml

from shared.i18n import SUPPORTED_LOCALES, get_locale


def load_config(path: Path = None) -> dict:
    """Load config.yaml."""
    if path is None:
        path = Path(__file__).parent.parent / "config.yaml"
    try:
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


# App locales -> YAML field (constellation_names.yaml)
_LOCALE_TO_NAME_FIELD = {"de": "german", "en": "english", "es": "spanish"}

# Standard IAU / JSON iau_name -> exact ``latin`` in YAML when spelling differs
_IAU_TO_YAML_LATIN: dict[str, str] = {
    "Ursa Major": "Ursa Maior",
}

_names_by_exact_latin: dict[str, dict] | None = None
_names_by_norm_latin: dict[str, dict] | None = None


def _norm_latin_key(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().replace(" ", "")


def _load_constellation_name_rows(path: Path | None = None) -> None:
    """Populate caches from constellation_names.yaml."""
    global _names_by_exact_latin, _names_by_norm_latin
    if _names_by_exact_latin is not None:
        return
    if path is None:
        path = Path(__file__).parent.parent / "data" / "constellation_names.yaml"
    _names_by_exact_latin = {}
    _names_by_norm_latin = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError):
        return
    for row in raw.get("constellations") or []:
        if not isinstance(row, dict):
            continue
        lat = row.get("latin")
        if not lat:
            continue
        _names_by_exact_latin[str(lat)] = row
        _names_by_norm_latin[_norm_latin_key(str(lat))] = row


def lookup_constellation_name_row(iau_name: str) -> dict | None:
    """
    Row from constellation_names.yaml for the given IAU designation
    (matches JSON ``iau_name``; Latin in parentheses follows YAML ``latin``).
    """
    if not iau_name:
        return None
    _load_constellation_name_rows()
    if not _names_by_exact_latin:
        return None
    yaml_latin = _IAU_TO_YAML_LATIN.get(iau_name, iau_name)
    if yaml_latin in _names_by_exact_latin:
        return _names_by_exact_latin[yaml_latin]
    nk = _norm_latin_key(iau_name)
    if nk in _names_by_norm_latin:
        return _names_by_norm_latin[nk]
    nk2 = _norm_latin_key(yaml_latin)
    if nk2 in _names_by_norm_latin:
        return _names_by_norm_latin[nk2]
    return None


def format_constellation_name(const_data: dict, locale: str | None = None) -> str:
    """
    Localized name plus Latin IAU designation, e.g. ``Great Bear (Ursa Maior)``.

    Vernacular comes from ``constellation_names.yaml`` for the active locale;
    the parenthetical is always YAML ``latin`` (or JSON ``iau_name`` if unknown).
    """
    loc = locale if locale is not None else get_locale()
    field = _LOCALE_TO_NAME_FIELD.get(loc, "english")
    iau = (const_data.get("iau_name") or "").strip()
    row = lookup_constellation_name_row(iau)
    latin = (row.get("latin") if row else None) or iau
    name_loc = row.get(field) if row else None
    if not name_loc:
        name_loc = (const_data.get("name") or "").strip() or latin
    return f"{name_loc} ({latin})"


def get_session_constellations(
    count: int,
    always_include: str | None = None,
    always_include_iau: str | None = None,
) -> list:
    """
    Randomly select ``count`` constellations.

    ``always_include_iau``: IAU designation as in JSON ``iau_name`` (e.g. ``Ursa Major``);
    stable across languages.

    ``always_include``: legacy full display string; matched against
    :func:`format_constellation_name` for de/en/es, or ``Name (Iau)`` parsing.
    """
    constellations = load_constellations()
    all_keys = list(constellations.keys())

    included_key = None
    if always_include_iau:
        t = always_include_iau.strip().lower()
        included_key = next(
            (
                k
                for k in all_keys
                if (constellations[k].get("iau_name") or "").strip().lower() == t
            ),
            None,
        )
    if included_key is None and always_include:
        included_key = next(
            (
                k
                for k in all_keys
                if format_constellation_name(constellations[k]) == always_include
            ),
            None,
        )
        if included_key is None:
            for loc in SUPPORTED_LOCALES:
                included_key = next(
                    (
                        k
                        for k in all_keys
                        if format_constellation_name(constellations[k], locale=loc)
                        == always_include
                    ),
                    None,
                )
                if included_key:
                    break
        if included_key is None and "(" in always_include:
            inner = always_include.strip().rsplit("(", 1)[-1].rstrip(")").strip()
            if inner:
                t = inner.lower()
                included_key = next(
                    (
                        k
                        for k in all_keys
                        if (constellations[k].get("iau_name") or "").strip().lower()
                        == t
                    ),
                    None,
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
