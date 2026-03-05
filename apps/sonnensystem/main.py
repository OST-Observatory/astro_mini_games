#!/usr/bin/env python3
"""Solar system - entry point"""

import os
import sys

os.environ["KIVY_NO_ARGS"] = "1"

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from shared.bootstrap import setup_logging
setup_logging()

DEV_MODE = "--dev" in sys.argv or os.environ.get("ASTRO_DEV", "0") == "1"

from kivy.config import Config

if DEV_MODE:
    Config.set("graphics", "width", "1280")
    Config.set("graphics", "height", "720")
    Config.set("graphics", "resizable", "1")
    Config.set("graphics", "fullscreen", "0")
else:
    Config.set("graphics", "fullscreen", "auto")
    Config.set("graphics", "width", "1920")
    Config.set("graphics", "height", "1080")

Config.set("graphics", "minimum_width", "400")
Config.set("graphics", "minimum_height", "500")
Config.set("input", "mouse", "mouse,multitouch_on_demand")

sys.path.insert(0, os.path.dirname(__file__))

from ui.app import SonnensystemApp

if __name__ == "__main__":
    SonnensystemApp().run()
