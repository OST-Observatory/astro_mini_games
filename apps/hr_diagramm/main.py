#!/usr/bin/env python3
"""HR diagram - entry point"""

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
Config.set("graphics", "width", "950")
Config.set("graphics", "height", "700")
Config.set("graphics", "minimum_width", "400")
Config.set("graphics", "minimum_height", "400")
Config.set("input", "mouse", "mouse,multitouch_on_demand")

sys.path.insert(0, os.path.dirname(__file__))

from ui.app import HRDiagrammApp

if __name__ == "__main__":
    HRDiagrammApp().run()
