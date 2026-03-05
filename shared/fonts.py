"""
Shared font logic for apps (Pi-compatible).
Roboto is often not installed on Raspberry Pi OS Lite.
Always returns a valid font name - never None (Button.font_name does not allow None).
"""

from pathlib import Path

_FONT_CACHE: str | None = None

# Bundled font (included in project – always works)
_BUNDLED_FONT = Path(__file__).resolve().parent.parent / "fonts" / "DejaVuSans.ttf"


def get_safe_font() -> str:
    """
    Returns a valid font name (never None).
    Priority: bundled font → system fonts.
    """
    global _FONT_CACHE
    if _FONT_CACHE is not None:
        return _FONT_CACHE

    candidates = [
        ("DejaVuSans", [
            _BUNDLED_FONT,
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
            Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        ]),
        ("NotoSans", [
            Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
        ]),
    ]

    for name, paths in candidates:
        for p in paths:
            if p.exists():
                try:
                    from kivy.core.text import LabelBase
                    reg_name = f"AstroFont_{name}"
                    LabelBase.register(name=reg_name, fn_regular=str(p))
                    _FONT_CACHE = reg_name
                    return _FONT_CACHE
                except Exception:
                    pass

    # Fallback: Kivy Roboto (if bundled) – must never be None
    _FONT_CACHE = "Roboto"
    return _FONT_CACHE
