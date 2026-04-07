"""
Base class for Astro apps with ready signal, inactivity timeout, and usage statistics.
"""

import os
import sys
import time
import yaml
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label

from shared.config_path import get_launcher_config_path
from shared.debug_keys import try_debug_tty2
from shared.usage_stats import write_usage_stats


def signal_ready():
    """Creates the ready file when ASTRO_READY_FILE is set."""
    path = os.environ.get("ASTRO_READY_FILE")
    if path:
        Path(path).touch()


def is_idle_timeout_disabled() -> bool:
    """
    True when inactivity return-to-launcher should be off (local testing).

    - CLI: ``--no-idle-timeout`` (works with ``KIVY_NO_ARGS``; Kivy does not consume it.)
    - Env: ``ASTRO_NO_IDLE_TIMEOUT=1`` (or ``true`` / ``yes``) when the launcher cannot pass args.
    """
    env = os.environ.get("ASTRO_NO_IDLE_TIMEOUT", "").strip().lower()
    if env in ("1", "true", "yes", "on"):
        return True
    return "--no-idle-timeout" in sys.argv


def _load_inactivity_config():
    """Loads inactivity config from config.yaml or config_default.yaml."""
    config_path = get_launcher_config_path()
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        inc = data.get("inactivity", {})
        cfg = {
            "enabled": inc.get("enabled", False),
            "timeout_sec": inc.get("timeout_sec", 120),
            "warning_sec": inc.get("warning_sec", 10),
        }
    except (OSError, yaml.YAMLError):
        cfg = {"enabled": False, "timeout_sec": 120, "warning_sec": 10}

    if is_idle_timeout_disabled():
        cfg = {**cfg, "enabled": False}
    return cfg


class AstroApp(App):
    """Base class for all Astro apps. Signals readiness to the wrapper."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._usage_start_time = None
        self._idle_timer_event = None
        self._idle_warning_event = None
        self._idle_warning_overlay = None
        self._idle_warning_sec_left = 0
        self._idle_countdown_event = None

    def on_start(self):
        super().on_start()
        signal_ready()

        # Usage stats (only when ASTRO_APP_ID is set, e.g. with exec)
        app_id = os.environ.get("ASTRO_APP_ID")
        if app_id:
            self._usage_start_time = time.time()

        # Inactivity timeout
        self._setup_idle_timeout()

    def on_stop(self):
        # Finalize usage stats
        app_id = os.environ.get("ASTRO_APP_ID")
        if app_id and self._usage_start_time is not None:
            write_usage_stats(app_id, self._usage_start_time, time.time())

        self._cancel_idle_timer()
        super().on_stop()

    def _setup_idle_timeout(self):
        """Sets up inactivity timer and event handlers."""
        config = _load_inactivity_config()
        self._idle_config = config

        if Window:
            Window.bind(on_touch_down=self._on_idle_reset)
            # Always keyboard: Debug shortcut Ctrl+Alt+O+P + Idle reset
            Window.bind(on_keyboard=self._on_keyboard)

        if not config["enabled"]:
            return

        self._idle_timeout_sec = config["timeout_sec"]
        self._idle_warning_sec = config["warning_sec"]
        self._reset_idle_timer()

    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        """Debug Ctrl+Alt+O+P -> tty2; otherwise reset idle timer."""
        if try_debug_tty2(key, modifier):
            return True
        self._on_idle_reset()
        return False

    def _on_idle_reset(self, *args):
        """Touch/input - reset timer, close warning overlay."""
        if self._idle_warning_overlay and self.root:
            self.root.remove_widget(self._idle_warning_overlay)
            self._idle_warning_overlay = None
        if self._idle_countdown_event:
            self._idle_countdown_event.cancel()
            self._idle_countdown_event = None
        self._reset_idle_timer()

    def _reset_idle_timer(self):
        """Restarts the idle timer."""
        self._cancel_idle_timer()
        cfg = getattr(self, "_idle_config", None)
        if not cfg or not cfg.get("enabled"):
            return
        self._idle_timer_event = Clock.schedule_once(
            self._on_idle_timeout, cfg["timeout_sec"]
        )

    def _cancel_idle_timer(self):
        """Cancel all idle-related scheduled events."""
        if self._idle_timer_event:
            self._idle_timer_event.cancel()
            self._idle_timer_event = None
        if self._idle_warning_event:
            self._idle_warning_event.cancel()
            self._idle_warning_event = None
        if self._idle_countdown_event:
            self._idle_countdown_event.cancel()
            self._idle_countdown_event = None

    def _on_idle_timeout(self, dt):
        """After timeout_sec without input – show warning overlay."""
        self._idle_timer_event = None
        cfg = getattr(self, "_idle_config", None)
        if not cfg:
            return
        self._idle_warning_sec_left = cfg["warning_sec"]
        self._show_idle_warning_overlay()

    def _show_idle_warning_overlay(self):
        """Shows the warning overlay and starts countdown."""
        if not self.root:
            return
        if self._idle_warning_overlay:
            self.root.remove_widget(self._idle_warning_overlay)

        overlay = FloatLayout(size=self.root.size)
        with overlay.canvas.before:
            Color(0, 0, 0, 0.7)
            overlay._bg_rect = Rectangle(pos=overlay.pos, size=overlay.size)
        overlay.bind(size=lambda o, v: setattr(o._bg_rect, "size", v))

        msg = f"Zurück zum Launcher in {self._idle_warning_sec_left} Sek?\nTippen zum Abbrechen"
        lbl = Label(
            text=msg,
            font_size="28sp",
            color=(1, 1, 1, 1),
            halign="center",
            valign="center",
            size_hint=(0.8, 0.3),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        lbl.bind(size=lbl.setter("text_size"))
        overlay.add_widget(lbl)

        self.root.add_widget(overlay)
        self._idle_warning_overlay = overlay
        self._idle_countdown_event = Clock.schedule_interval(
            self._idle_warning_countdown, 1.0
        )

    def _idle_warning_countdown(self, dt):
        """Countdown in warning overlay - stop app at 0."""
        self._idle_warning_sec_left -= 1
        if self._idle_warning_sec_left <= 0:
            self._cancel_idle_timer()
            if self._idle_warning_overlay and self.root:
                self.root.remove_widget(self._idle_warning_overlay)
                self._idle_warning_overlay = None
            self.stop()
            return

        # Update label
        if self._idle_warning_overlay and self._idle_warning_overlay.children:
            lbl = self._idle_warning_overlay.children[0]
            lbl.text = (
                f"Zurück zum Launcher in {self._idle_warning_sec_left} Sek?\n"
                "Tippen zum Abbrechen"
            )
