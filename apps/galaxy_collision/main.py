#!/usr/bin/env python3
"""
Galaxien-Kollision - Startskript mit Debug-Output
"""

import os
import sys

# Kivy-Config VOR Import
os.environ["KIVY_NO_ARGS"] = "1"

from kivy.config import Config

Config.set("graphics", "fullscreen", "auto")
Config.set("graphics", "width", "1920")
Config.set("graphics", "height", "1080")
Config.set("input", "mouse", "mouse,multitouch_on_demand")

# Kivy importieren
import kivy

kivy.require("2.0.0")

# Pfad setzen
sys.path.insert(0, os.path.dirname(__file__))

# === FONTS INITIALISIEREN ===
print("=" * 50)
print("[MAIN] Initialisiere Schriftarten...")
from ui.fonts import get_font_name, init_fonts, is_unicode_available

success = init_fonts()
print(f"[MAIN] Font-Name: {get_font_name()}")
print(f"[MAIN] Unicode verfügbar: {is_unicode_available()}")
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
