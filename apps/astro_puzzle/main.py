#!/usr/bin/env python3
"""Astro-Puzzle - entry point."""

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
Config.set("graphics", "width", "800")
Config.set("graphics", "height", "700")
Config.set("graphics", "minimum_width", "400")
Config.set("graphics", "minimum_height", "400")
Config.set("input", "mouse", "mouse,multitouch_on_demand")

from kivy.clock import Clock

Clock.max_iteration = 25  

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.dirname(__file__))

from ui.app import AstroPuzzleApp

if __name__ == "__main__":
    AstroPuzzleApp().run()
