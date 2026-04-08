"""Locale: ASTRO_LANG env, YAML catalogs, config persistence."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Callable

import yaml

_LOG = logging.getLogger(__name__)

SUPPORTED_LOCALES = ("de", "en", "es")
ASTRO_LANG_ENV = "ASTRO_LANG"
_DEFAULT_LOCALE = "de"

_catalogs: dict[str, dict[str, str]] = {}
_locale_callbacks: list[Callable[[str], None]] = []


def _package_root() -> Path:
    # shared/i18n/__init__.py -> package root (same level as main.py, locales/)
    return Path(__file__).resolve().parent.parent.parent


def _locale_user_path() -> Path:
    """Per-user language choice; never touches deployment ``config.yaml``."""
    return Path.home() / ".local" / "share" / "astro_mini_games" / "locale.yaml"


def _read_user_saved_locale() -> str | None:
    path = _locale_user_path()
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        loc = data.get("locale")
        if loc is None and isinstance(data.get("i18n"), dict):
            loc = data["i18n"].get("locale")
        loc = str(loc or "").strip().lower()
        return loc if loc in SUPPORTED_LOCALES else None
    except (OSError, yaml.YAMLError) as e:
        _LOG.debug("Could not read user locale file: %s", e)
        return None


def get_config_locale(project_root: Path | None = None) -> str:
    """``i18n.locale`` from the active launcher YAML (``config.yaml`` or ``config_default.yaml``)."""
    root = project_root or _package_root()
    from shared.config_path import get_launcher_config_path

    try:
        with open(get_launcher_config_path(root), "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        loc = str((data.get("i18n") or {}).get("locale", _DEFAULT_LOCALE)).lower().strip()
        if loc in SUPPORTED_LOCALES:
            return loc
    except (OSError, yaml.YAMLError) as e:
        _LOG.debug("Could not read config locale: %s", e)
    return _DEFAULT_LOCALE


def resolve_effective_locale(project_root: Path | None = None) -> str:
    """
    Effective locale: user ``locale.yaml`` first (in-app / launcher switches), then
    ``ASTRO_LANG``, then ``i18n.locale`` in launcher config, else ``de``.

    The file is checked before env so a stale ``ASTRO_LANG`` inherited from an old
    launcher or wrapper process does not override the language saved when the user
    switched inside an app.
    """
    saved = _read_user_saved_locale()
    if saved:
        return saved
    env = os.environ.get(ASTRO_LANG_ENV, "").strip().lower()
    if env in SUPPORTED_LOCALES:
        return env
    root = project_root or _package_root()
    return get_config_locale(root)


def ensure_locale_env(project_root: Path | None = None, *, notify: bool = False) -> str:
    """Set ``ASTRO_LANG``, load catalog; optionally notify registered locale callbacks."""
    prev = get_locale()
    loc = resolve_effective_locale(project_root)
    os.environ[ASTRO_LANG_ENV] = loc
    _load_catalog(loc)
    if notify and loc != prev:
        for cb in list(_locale_callbacks):
            try:
                cb(loc)
            except Exception as e:
                _LOG.warning("locale callback failed: %s", e)
    return loc


def _flatten(prefix: str, node, out: dict[str, str]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            nk = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, dict):
                _flatten(nk, v, out)
            elif v is not None:
                out[nk] = str(v)
    elif node is not None and prefix:
        out[prefix] = str(node)


def _load_catalog(locale: str) -> None:
    root = _package_root()
    path = root / "locales" / f"{locale}.yaml"
    fallback_path = root / "locales" / f"{_DEFAULT_LOCALE}.yaml"
    flat: dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        _flatten("", raw, flat)
    except (OSError, yaml.YAMLError) as e:
        _LOG.debug("Locale file missing or invalid %s: %s", path, e)
    if locale != _DEFAULT_LOCALE:
        try:
            with open(fallback_path, "r", encoding="utf-8") as f:
                raw_fb = yaml.safe_load(f) or {}
            fb: dict[str, str] = {}
            _flatten("", raw_fb, fb)
            for k, v in fb.items():
                flat.setdefault(k, v)
        except (OSError, yaml.YAMLError):
            pass
    _catalogs[locale] = flat


def get_locale() -> str:
    v = os.environ.get(ASTRO_LANG_ENV, "").strip().lower()
    if v in SUPPORTED_LOCALES:
        return v
    return _DEFAULT_LOCALE


def register_locale_callback(cb: Callable[[str], None]) -> None:
    if cb not in _locale_callbacks:
        _locale_callbacks.append(cb)


def unregister_locale_callback(cb: Callable[[str], None]) -> None:
    try:
        _locale_callbacks.remove(cb)
    except ValueError:
        pass


def set_locale(code: str, project_root: Path | None = None) -> str:
    """Persist locale to user state file only; update env, reload catalog, notify callbacks."""
    code = (code or _DEFAULT_LOCALE).strip().lower()
    if code not in SUPPORTED_LOCALES:
        code = _DEFAULT_LOCALE
    _persist_user_locale(code)
    os.environ[ASTRO_LANG_ENV] = code
    _load_catalog(code)
    for cb in list(_locale_callbacks):
        try:
            cb(code)
        except Exception as e:
            _LOG.warning("locale callback failed: %s", e)
    return code


def revert_to_config_locale(project_root: Path | None = None) -> str:
    """
    Remove user ``locale.yaml`` and apply ``i18n.locale`` from the launcher config file
    (updates ``ASTRO_LANG``, catalogs, and registered callbacks if the locale changes).
    """
    root = project_root or _package_root()
    path = _locale_user_path()
    try:
        if path.is_file():
            path.unlink()
    except OSError as e:
        _LOG.warning("Could not remove user locale file: %s", e)

    loc = get_config_locale(root)
    prev = get_locale()
    os.environ[ASTRO_LANG_ENV] = loc
    _load_catalog(loc)
    if loc != prev:
        for cb in list(_locale_callbacks):
            try:
                cb(loc)
            except Exception as e:
                _LOG.warning("locale callback failed: %s", e)
    return loc


def _persist_user_locale(locale: str) -> None:
    path = _locale_user_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                {"locale": locale},
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
    except OSError as e:
        _LOG.warning("Could not write user locale file %s: %s", path, e)


def tr(key: str, **kwargs) -> str:
    """Translate a dotted key; format with kwargs when placeholders exist."""
    loc = get_locale()
    if loc not in _catalogs:
        _load_catalog(loc)
    catalog = _catalogs.get(loc, {})
    s = catalog.get(key)
    if s is None:
        _LOG.debug("Missing translation key: %s locale=%s", key, loc)
        if _DEFAULT_LOCALE not in _catalogs:
            _load_catalog(_DEFAULT_LOCALE)
        s = _catalogs.get(_DEFAULT_LOCALE, {}).get(key, key)
    if kwargs:
        try:
            return s.format(**kwargs)
        except (KeyError, ValueError):
            return s
    return str(s)


def pick_localized_field(value, locale: str | None = None) -> str:
    """Resolve config Option A: str or dict with de/en/es."""
    loc = locale or get_locale()
    if isinstance(value, dict):
        v = value.get(loc) or value.get(_DEFAULT_LOCALE)
        if v is not None:
            return str(v)
        for x in value.values():
            return str(x) if x is not None else ""
        return ""
    if value is None:
        return ""
    return str(value)


def denormalize_apps_list(apps: list, locale: str | None = None) -> list:
    """Copy app entries with name/description resolved for the current locale."""
    loc = locale or get_locale()
    out = []
    for app in apps:
        if not isinstance(app, dict):
            continue
        d = dict(app)
        d["name"] = pick_localized_field(app.get("name"), loc)
        d["description"] = pick_localized_field(app.get("description"), loc)
        out.append(d)
    return out
