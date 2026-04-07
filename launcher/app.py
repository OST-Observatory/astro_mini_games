"""
Main application class for the Astro Launcher.
"""

import json
import os
import random
import subprocess
import sys
from pathlib import Path

import yaml
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty, DictProperty, ListProperty
from kivy.uix.widget import Widget

from launcher.widgets.background import StarfieldBackground
from launcher.widgets.stats_overlay import StatsOverlay
from launcher.widgets.tile import AppTile
from shared.config_path import get_launcher_config_path
from shared.debug_keys import try_debug_tty2


class AstroLauncherApp(App):
    """Main application."""

    apps = ListProperty([])
    config_data = DictProperty({})
    is_dev_mode = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_process = None
        self.process_check_event = None
        self.wiggle_event = None
        self.app_tiles = []  # References to tiles
        self.is_dev_mode = (
            "--dev" in sys.argv or os.environ.get("ASTRO_DEV", "0") == "1"
        )

    def build(self):
        """Builds the UI."""
        self.load_config()

        kv_path = Path(__file__).parent.parent / "views" / "launcher.kv"
        print(f"📄 Loading KV file: {kv_path}")

        if kv_path.exists():
            root = Builder.load_file(str(kv_path))
        else:
            print(f"✗ KV file not found: {kv_path}")
            return None

        if Window:
            Window.bind(on_keyboard=self.on_keyboard)

        return root

    def on_start(self):
        """Called after the UI is built."""
        # Ready signal for wrapper (after "Back to Launcher")
        ready_file = os.environ.get("ASTRO_READY_FILE")
        if ready_file:
            Path(ready_file).touch()

        if not self.root:
            print("⚠ No root widget present")
            return

        try:
            grid = self.root.ids.app_grid
            starfield = self.root.ids.starfield
            print(f"✓ UI elements found")
        except (AttributeError, KeyError) as e:
            print(f"⚠ UI elements not found: {e}")
            return

        # Configure background
        bg_config = self.get_background_config()
        starfield.apply_config(bg_config)

        # Create tiles
        grid.clear_widgets()
        self.app_tiles = []  # Reset
        grid_config = self.get_grid_config()
        grid.cols = grid_config.get("cols", 3)

        for app_config in self.apps:
            tile = AppTile()
            tile.app_config = app_config
            grid.add_widget(tile)
            self.app_tiles.append(tile)  # Store reference

        # Empty placeholders if fewer than 6 apps
        while len(grid.children) < 6:
            placeholder = Widget(size_hint=(1, 1))
            grid.add_widget(placeholder)

        print(f"✓ {len(self.apps)} App-Kacheln erstellt")

        # Start wiggle timer
        self._schedule_wiggle()

        # 8x tap stats screen
        try:
            tap_area = self.root.ids.stats_tap_area
            tap_area.on_activate_callback = self._show_stats_overlay
        except (AttributeError, KeyError):
            pass

    def _show_stats_overlay(self):
        """Shows the usage statistics overlay."""
        if not self.root:
            return
        app_name_map = {a.get("id", ""): a.get("name", a.get("id", "?")) for a in self.apps}
        overlay = StatsOverlay(
            app_name_map=app_name_map,
            on_dismiss=lambda: self.root.remove_widget(overlay) if overlay in self.root.children else None,
        )
        overlay.size = self.root.size
        overlay.pos = self.root.pos
        self.root.bind(size=lambda o, v: setattr(overlay, "size", v))
        self.root.bind(pos=lambda o, v: setattr(overlay, "pos", v))
        self.root.add_widget(overlay)

    def _schedule_wiggle(self):
        """Schedules the next tile wiggle."""
        # Random interval between 5 and 12 seconds
        wiggle_config = self.config_data.get("launcher", {}).get("wiggle", {})
        min_interval = wiggle_config.get("min_interval", 5)
        max_interval = wiggle_config.get("max_interval", 12)

        interval = random.uniform(min_interval, max_interval)
        self.wiggle_event = Clock.schedule_once(self._wiggle_random_tile, interval)

    def _wiggle_random_tile(self, dt):
        """Makes a random tile wiggle."""
        if self.app_tiles and not self.current_process:
            # Only tiles that are not currently wiggling
            available_tiles = [t for t in self.app_tiles if not t.is_wiggling]

            if available_tiles:
                tile = random.choice(available_tiles)
                tile.wiggle()
                print(f"🎯 Wackeln: {tile.app_name}")

        # Schedule next wiggle
        self._schedule_wiggle()

    def load_config(self):
        """Loads configuration from config.yaml or config_default.yaml."""
        config_path = get_launcher_config_path()

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.config_data = yaml.safe_load(f)

            all_apps = self.config_data.get("apps", [])
            self.apps = [app for app in all_apps if app.get("enabled", True)]

            print(f"✓ {len(self.apps)} apps loaded (from {config_path.name})")

        except FileNotFoundError:
            print(
                f"⚠ No launcher config found: expected config.yaml or "
                f"config_default.yaml next to main.py ({config_path})"
            )
            self.apps = []
        except Exception as e:
            print(f"✗ Error loading config: {e}")
            self.apps = []

    def launch_app(self, app_config: dict):
        """Launches an external app."""
        command = app_config.get("command", "")
        app_name = app_config.get("name", "Unbekannt")
        app_id = app_config.get("id", "unknown")

        if not command:
            print(f"⚠ No command defined for {app_name}")
            return

        print(f"🚀 Starting: {app_name}")
        print(f"   Command: {command}")

        # Pause wiggle
        if self.wiggle_event:
            self.wiggle_event.cancel()

        from_wrapper = os.environ.get("ASTRO_LAUNCHER_FROM_WRAPPER") == "1"

        if self.is_dev_mode:
            # Dev: minimize window, monitor subprocess
            Window.minimize()
            try:
                self.current_process = subprocess.Popen(
                    command, shell=True, cwd=Path(__file__).parent.parent
                )
                self.process_check_event = Clock.schedule_interval(
                    self.check_process, 0.5
                )
            except Exception as e:
                print(f"✗ Error starting: {e}")
                self.on_app_closed()
        elif from_wrapper:
            # Launcher was started by wrapper: exec to app (like non-wrapper mode).
            # Same process = same display connection – fixes "every 2nd start fails".
            try:
                import time
                with open(Path("/tmp/astro_next_app.json"), "w", encoding="utf-8") as f:
                    json.dump(
                        {"app_id": app_id, "command": command, "name": app_name, "start_time": time.time()},
                        f,
                    )
            except OSError:
                pass
            # Exec like non-wrapper – no subprocess, no display handover
            def do_exec(_dt):
                project_root = Path(__file__).resolve().parent.parent
                venv_bin = str(Path(sys.executable).parent)
                os.environ["PATH"] = venv_bin + os.pathsep + os.environ.get("PATH", "")
                os.environ["ASTRO_APP_ID"] = app_id
                if sys.platform == "linux":
                    os.environ.setdefault("SDL_VIDEODRIVER", "kmsdrm")
                import shlex
                cmd = command.strip()
                parts = shlex.split(cmd) if cmd else []
                if not parts:
                    self.stop()
                    return
                # Python commands: "python apps/quiz/main.py"
                for prefix in ("python ", "python3 "):
                    if cmd.lower().startswith(prefix):
                        rest = cmd[len(prefix):].strip()
                        py_parts = shlex.split(rest) if rest else []
                        args = [sys.executable, "-u"] + py_parts
                        os.chdir(str(project_root))
                        os.execv(sys.executable, args)
                        return
                # Native executables: "./apps/NBodyTouch/build/NBodyApp" or "/path/app"
                exe = parts[0]
                if exe.startswith("./") or (not os.path.isabs(exe) and "/" in exe):
                    exe_path = str((project_root / exe.lstrip("./")).resolve())
                else:
                    exe_path = exe
                args = [exe_path] + parts[1:]
                os.chdir(str(project_root))
                try:
                    os.execv(exe_path, args)
                except OSError:
                    self.stop()

            Clock.schedule_once(do_exec, 0.1)
        else:
            # Production: start app directly via exec (replaces launcher process) –
            # same process = same display connection, no subprocess (Pi-KMS fix)
            def do_exec(_dt):
                project_root = Path(__file__).resolve().parent.parent
                venv_bin = str(Path(sys.executable).parent)
                os.environ["PATH"] = venv_bin + os.pathsep + os.environ.get("PATH", "")
                os.environ["ASTRO_APP_ID"] = app_id
                if sys.platform == "linux":
                    os.environ.setdefault("SDL_VIDEODRIVER", "kmsdrm")
                import shlex
                cmd = command.strip()
                parts = shlex.split(cmd) if cmd else []
                if not parts:
                    return
                for prefix in ("python ", "python3 "):
                    if cmd.lower().startswith(prefix):
                        rest = cmd[len(prefix):].strip()
                        py_parts = shlex.split(rest) if rest else []
                        args = [sys.executable, "-u"] + py_parts
                        os.chdir(str(project_root))
                        os.execv(sys.executable, args)
                        return
                # Native executables
                exe = parts[0]
                if exe.startswith("./") or (not os.path.isabs(exe) and "/" in exe):
                    exe_path = str((project_root / exe.lstrip("./")).resolve())
                else:
                    exe_path = exe
                args = [exe_path] + parts[1:]
                os.chdir(str(project_root))
                try:
                    os.execv(exe_path, args)
                except OSError:
                    pass
                os.execv(
                    sys.executable,
                    [sys.executable, str(project_root / "launch_wrapper.py"), app_id, command, app_name],
                )

            Clock.schedule_once(do_exec, 0)  # Next frame

    def check_process(self, dt):
        """Checks if the started app is still running."""
        if self.current_process is None:
            return

        poll = self.current_process.poll()

        if poll is not None:
            print(f"✓ App beendet (Exit-Code: {poll})")
            self.on_app_closed()

    def on_app_closed(self):
        """Called when an app has been closed."""
        if self.process_check_event:
            self.process_check_event.cancel()
            self.process_check_event = None

        self.current_process = None

        Window.restore()
        Window.raise_window()

        print("↩ Back to app overview")

        # Restart wiggle
        self._schedule_wiggle()

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        """Keyboard events."""
        if try_debug_tty2(key, modifier):
            return True
        if key == 27:  # ESC
            if self.is_dev_mode:
                self.stop()
                return True
        if key == 292:  # F11
            Window.fullscreen = not Window.fullscreen
            return True
        return False

    def on_stop(self):
        """Cleanup on exit."""
        if self.wiggle_event:
            self.wiggle_event.cancel()
        if self.process_check_event:
            self.process_check_event.cancel()

    def get_background_config(self):
        """Returns the background configuration."""
        return self.config_data.get("launcher", {}).get("background", {})

    def get_grid_config(self):
        """Returns the grid configuration."""
        return self.config_data.get("launcher", {}).get(
            "grid", {"cols": 3, "rows": 2, "padding": 60, "spacing": 40}
        )
