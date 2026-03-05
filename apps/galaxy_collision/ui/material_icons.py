"""
Material Icons for Galaxy-Collision.
Font: MaterialIcons-Regular.ttf (project fonts or launcher)
"""

from pathlib import Path

# Project root: apps/galaxy_collision -> parent.parent
_APP_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _APP_ROOT.parent.parent

# Material Icons Font
FONT_CANDIDATES = [
    _PROJECT_ROOT / "fonts" / "MaterialIcons-Regular.ttf",
    _APP_ROOT / "assets" / "fonts" / "MaterialIcons-Regular.ttf",
    Path("/usr/share/fonts/truetype/material-design-icons/MaterialIcons-Regular.ttf"),
]

# Material Icons codepoints (hex from MaterialIcons-Regular.codepoints)
ICONS = {
    "play_arrow": "\ue037",
    "pause": "\ue034",
    "replay": "\ue042",
    "zoom_in": "\ue8ff",
    "zoom_out": "\ue900",
    "rotate_left": "\ue419",
    "rotate_right": "\ue41a",
    "speed": "\ue9e4",
}

_MATERIAL_ICONS_REGISTERED = False


def init_material_icons() -> str | None:
    """Register Material Icons with Kivy. Returns font name or None on error."""
    global _MATERIAL_ICONS_REGISTERED
    if _MATERIAL_ICONS_REGISTERED:
        return "MaterialIcons"

    for path in FONT_CANDIDATES:
        if path.exists():
            try:
                from kivy.core.text import LabelBase
                LabelBase.register(name="MaterialIcons", fn_regular=str(path))
                _MATERIAL_ICONS_REGISTERED = True
                return "MaterialIcons"
            except Exception as e:
                print(f"[MaterialIcons] Fehler beim Laden von {path}: {e}")
                continue
    return None


# Fallback character if Material Icons font not loaded (DejaVuSans compatible)
FALLBACK = {
    "play_arrow": "\u25b6",   # ▶
    "pause": "\u23f8",        # ⏸
    "replay": "\u21bb",       # ↻
    "zoom_in": "+",
    "zoom_out": "\u2212",     # −
    "rotate_left": "\u21ba",  # ↺
    "rotate_right": "\u2937",  # ↷
    "speed": "\u26a1",        # ⚡
}


def get_icon(name: str) -> str:
    """Return the icon character. Uses fallback when Material Icons not loaded."""
    if _MATERIAL_ICONS_REGISTERED:
        return ICONS.get(name, FALLBACK.get(name, "?"))
    return FALLBACK.get(name, "?")


def get_icon_font() -> str:
    """Return the font name for Material Icons (or DejaVu as fallback)."""
    name = init_material_icons()
    return name if name else "DejaVuSans"
