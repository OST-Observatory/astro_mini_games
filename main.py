#!/usr/bin/env python3
"""
Astro-Launcher - Haupteinstiegspunkt
"""

import os
import sys

# ============================================
# WICHTIG: VOR allen Kivy-Imports!
# ============================================

# Kivy's Argument-Parser deaktivieren
os.environ["KIVY_NO_ARGS"] = "1"

# Entwicklungsmodus erkennen
DEV_MODE = "--dev" in sys.argv or os.environ.get("ASTRO_DEV", "0") == "1"

# Plattform-spezifisches GL-Backend
if sys.platform == "win32":
    os.environ["KIVY_GL_BACKEND"] = "angle_sdl2"

from kivy.config import Config

if DEV_MODE:
    # Laptop: Fenster mit fester Größe
    Config.set("graphics", "width", "1280")
    Config.set("graphics", "height", "720")
    Config.set("graphics", "resizable", "1")
    Config.set("graphics", "fullscreen", "0")

    # ============================================
    # Input-Provider komplett überschreiben
    # Entfernt MTD/Probesysfs die Probleme machen
    # ============================================
    Config.remove_section("input")
    Config.add_section("input")
    Config.set("input", "mouse", "mouse,multitouch_on_demand")

    print("🔧 Entwicklungsmodus aktiv")
else:
    # Pi: Vollbild
    Config.set("graphics", "fullscreen", "auto")
    print("🚀 Produktionsmodus aktiv")

# Jetzt erst die App importieren
from launcher.app import AstroLauncherApp

if __name__ == "__main__":
    AstroLauncherApp().run()
