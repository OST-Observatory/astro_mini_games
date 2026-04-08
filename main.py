#!/usr/bin/env python3
"""
Astro Launcher - main entry point.
"""

import os
import sys
from pathlib import Path

from shared.config_path import get_launcher_config_path
from shared.i18n import ensure_locale_env

PROJECT_ROOT = Path(__file__).resolve().parent

# Locale before any Kivy / app imports (catalog + ASTRO_LANG for subprocesses)
ensure_locale_env(PROJECT_ROOT)

# ============================================
# IMPORTANT: BEFORE any Kivy imports!
# ============================================

# Disable Kivy's argument parser
os.environ["KIVY_NO_ARGS"] = "1"

# Detect development mode
DEV_MODE = "--dev" in sys.argv or os.environ.get("ASTRO_DEV", "0") == "1"


def _use_wrapper():
    """Checks if wrapper mode is active (option C)."""
    try:
        import yaml

        config_path = get_launcher_config_path(PROJECT_ROOT)
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("launcher", {}).get("use_wrapper", False)
    except Exception:
        return False

# Production: stdout/stderr to log file, clear console
if not DEV_MODE:
    log_dir = Path.home() / ".local" / "share" / "astro_mini_games"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "astro.log"
    try:
        log_file = open(log_path, "a", encoding="utf-8", buffering=1)
        sys.stdout = log_file
        sys.stderr = log_file
    except OSError:
        pass  # Fallback: suppress output
        sys.stdout = open(os.devnull, "w")
        sys.stderr = sys.stdout

    # Clear console (boot output disappears)
    from shared.console_utils import clear_console
    clear_console()

# Platform-specific GL backend
if sys.platform == "win32":
    os.environ["KIVY_GL_BACKEND"] = "angle_sdl2"

from kivy.config import Config

if DEV_MODE:
    # Laptop: window with fixed size
    Config.set("graphics", "width", "1280")
    Config.set("graphics", "height", "720")
    Config.set("graphics", "resizable", "1")
    Config.set("graphics", "fullscreen", "0")

    # ============================================
    # Completely override input provider
    # Removes MTD/Probesysfs that cause problems
    # ============================================
    Config.remove_section("input")
    Config.add_section("input")
    Config.set("input", "mouse", "mouse,multitouch_on_demand")

    print("Development mode")
else:
    # Pi: fullscreen, hide cursor (touchscreen)
    Config.set("graphics", "fullscreen", "auto")
    Config.set("graphics", "show_cursor", "0")
    print("Production mode")

# Now import the app
from launcher.app import AstroLauncherApp


def run_launcher():
    """Starts the launcher. exec() so launcher inherits tty1 (systemd/Kiosk)."""
    os.environ["ASTRO_LAUNCHER_ONLY"] = "1"
    os.execv(sys.executable, [sys.executable, str(PROJECT_ROOT / "main.py"), "--launcher-only"])


if __name__ == "__main__":
    if "--launcher-only" in sys.argv or os.environ.get("ASTRO_LAUNCHER_ONLY") == "1":
        AstroLauncherApp().run()
    elif DEV_MODE:
        AstroLauncherApp().run()
    elif _use_wrapper():
        os.execv(sys.executable, [sys.executable, str(PROJECT_ROOT / "launch_wrapper.py"), "--launcher-first"])
    else:
        run_launcher()  # exec: launcher replaces this process
