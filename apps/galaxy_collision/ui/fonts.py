"""
Schriftart-Konfiguration für Kivy mit Unicode-Support
"""

import os
from pathlib import Path

# Status-Variablen
_font_initialized = False
_font_name = "Roboto"  # Kivy-Default

# Pfade
ASSETS_DIR = Path(__file__).parent.parent / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
UNICODE_FONT_FILE = FONTS_DIR / "DejaVuSans.ttf"


def init_fonts() -> bool:
    """
    Initialisiert die Unicode-Schriftart für Kivy.

    MUSS vor dem Erstellen von Widgets aufgerufen werden!
    """
    global _font_initialized, _font_name

    if _font_initialized:
        return _font_name != "Roboto"

    from kivy.core.text import LabelBase

    # Suche nach Schriftart
    font_candidates = [
        UNICODE_FONT_FILE,
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
        Path.home() / ".local/share/fonts/DejaVuSans.ttf",
        Path.home() / ".fonts/DejaVuSans.ttf",
    ]

    font_path = None
    for candidate in font_candidates:
        if candidate.exists():
            font_path = candidate
            break

    if font_path:
        try:
            LabelBase.register(name="DejaVuSans", fn_regular=str(font_path))
            _font_name = "DejaVuSans"
            print(f"[Fonts] ✓ Unicode-Schriftart geladen: {font_path}")
        except Exception as e:
            print(f"[Fonts] ✗ Fehler beim Laden: {e}")
    else:
        print("[Fonts] ✗ Keine Unicode-Schriftart gefunden!")
        print(f"[Fonts]   Erwartet: {UNICODE_FONT_FILE}")

    _font_initialized = True
    return _font_name != "Roboto"


def get_font_name() -> str:
    """Gibt den Namen der zu verwendenden Schriftart zurück."""
    return _font_name


def is_unicode_available() -> bool:
    """Prüft ob Unicode-Schriftart verfügbar ist."""
    return _font_name != "Roboto"
