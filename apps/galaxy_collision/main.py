#!/usr/bin/env python3
"""
Galaxy collision - startup script with debug output.
"""

import os
import sys

os.environ["KIVY_NO_ARGS"] = "1"

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from shared.bootstrap import setup_logging
setup_logging()

from kivy.config import Config

Config.set("graphics", "fullscreen", "auto")
Config.set("graphics", "width", "1920")
Config.set("graphics", "height", "1080")
Config.set("graphics", "minimum_width", "400")
Config.set("graphics", "minimum_height", "300")
Config.set("input", "mouse", "mouse,multitouch_on_demand")

# Kivy importieren
import kivy

kivy.require("2.0.0")

sys.path.insert(0, os.path.dirname(__file__))

# === FONTS INITIALISIEREN ===
print("=" * 50)
print("[MAIN] Initialisiere Schriftarten...")
from ui.fonts import get_font_name, init_fonts, is_unicode_available

success = init_fonts()
print(f"[MAIN] Font-Name: {get_font_name()}")
print(f"[MAIN] Unicode available: {is_unicode_available()}")

# Material Icons for buttons
from ui.material_icons import init_material_icons
_mi = init_material_icons()
print(f"[MAIN] Material Icons: {'OK' if _mi else 'not available'}")
print("=" * 50)

# === SYMBOLE TESTEN ===
from ui.symbols import S

print(f"[MAIN] Test-Symbole: {S.PLAY} {S.PAUSE} {S.RESET} {S.SETTINGS}")
print("=" * 50)

# === APP STARTEN ===
print("[MAIN] Starte Anwendung...")
from ui.app import GalaxyCollisionApp

if __name__ == "__main__":
    GalaxyCollisionApp().run()
