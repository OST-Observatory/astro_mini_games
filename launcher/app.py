"""
Hauptanwendungsklasse für den Astro-Launcher
"""

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
from launcher.widgets.tile import AppTile


class AstroLauncherApp(App):
    """Hauptanwendung"""

    apps = ListProperty([])
    config_data = DictProperty({})
    is_dev_mode = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_process = None
        self.process_check_event = None
        self.wiggle_event = None  # NEU
        self.app_tiles = []  # NEU: Referenzen zu den Kacheln
        self.is_dev_mode = (
            "--dev" in sys.argv or os.environ.get("ASTRO_DEV", "0") == "1"
        )

    def build(self):
        """Erstellt die UI"""
        self.load_config()

        self.title = self.config_data.get("launcher", {}).get("title", "Astro Launcher")

        kv_path = Path(__file__).parent.parent / "views" / "launcher.kv"
        print(f"📄 Lade KV-Datei: {kv_path}")

        if kv_path.exists():
            root = Builder.load_file(str(kv_path))
        else:
            print(f"✗ KV-Datei nicht gefunden: {kv_path}")
            return None

        if Window:
            Window.bind(on_keyboard=self.on_keyboard)

        return root

    def on_start(self):
        """Wird aufgerufen nachdem die UI aufgebaut ist"""
        if not self.root:
            print("⚠ Kein Root-Widget vorhanden")
            return

        try:
            grid = self.root.ids.app_grid
            starfield = self.root.ids.starfield
            print(f"✓ UI-Elemente gefunden")
        except (AttributeError, KeyError) as e:
            print(f"⚠ UI-Elemente nicht gefunden: {e}")
            return

        # Hintergrund konfigurieren
        bg_config = self.get_background_config()
        starfield.apply_config(bg_config)

        # Kacheln erstellen
        grid.clear_widgets()
        self.app_tiles = []  # Reset
        grid_config = self.get_grid_config()
        grid.cols = grid_config.get("cols", 3)

        for app_config in self.apps:
            tile = AppTile()
            tile.app_config = app_config
            grid.add_widget(tile)
            self.app_tiles.append(tile)  # Referenz speichern

        # Leere Platzhalter falls weniger als 6 Apps
        while len(grid.children) < 6:
            placeholder = Widget(size_hint=(1, 1))
            grid.add_widget(placeholder)

        print(f"✓ {len(self.apps)} App-Kacheln erstellt")

        # Wackel-Timer starten
        self._schedule_wiggle()

    def _schedule_wiggle(self):
        """Plant das nächste Kachel-Wackeln"""
        # Zufälliges Intervall zwischen 5 und 12 Sekunden
        wiggle_config = self.config_data.get("launcher", {}).get("wiggle", {})
        min_interval = wiggle_config.get("min_interval", 5)
        max_interval = wiggle_config.get("max_interval", 12)

        interval = random.uniform(min_interval, max_interval)
        self.wiggle_event = Clock.schedule_once(self._wiggle_random_tile, interval)

    def _wiggle_random_tile(self, dt):
        """Lässt eine zufällige Kachel wackeln"""
        if self.app_tiles and not self.current_process:
            # Nur Kacheln die nicht gerade wackeln
            available_tiles = [t for t in self.app_tiles if not t.is_wiggling]

            if available_tiles:
                tile = random.choice(available_tiles)
                tile.wiggle()
                print(f"🎯 Wackeln: {tile.app_name}")

        # Nächstes Wackeln planen
        self._schedule_wiggle()

    def load_config(self):
        """Lädt die Konfiguration aus config.yaml"""
        config_path = Path(__file__).parent.parent / "config.yaml"

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.config_data = yaml.safe_load(f)

            all_apps = self.config_data.get("apps", [])
            self.apps = [app for app in all_apps if app.get("enabled", True)]

            print(f"✓ {len(self.apps)} Apps geladen")

        except FileNotFoundError:
            print(f"⚠ config.yaml nicht gefunden: {config_path}")
            self.apps = []
        except Exception as e:
            print(f"✗ Fehler beim Laden der Config: {e}")
            self.apps = []

    def launch_app(self, app_config: dict):
        """Startet eine externe App"""
        command = app_config.get("command", "")
        app_name = app_config.get("name", "Unbekannt")

        if not command:
            print(f"⚠ Kein Kommando für {app_name} definiert")
            return

        print(f"🚀 Starte: {app_name}")
        print(f"   Kommando: {command}")

        # Wackeln pausieren
        if self.wiggle_event:
            self.wiggle_event.cancel()

        if not self.is_dev_mode:
            Window.minimize()

        try:
            self.current_process = subprocess.Popen(
                command, shell=True, cwd=Path(__file__).parent.parent
            )

            self.process_check_event = Clock.schedule_interval(self.check_process, 0.5)

        except Exception as e:
            print(f"✗ Fehler beim Starten: {e}")
            self.on_app_closed()

    def check_process(self, dt):
        """Prüft ob die gestartete App noch läuft"""
        if self.current_process is None:
            return

        poll = self.current_process.poll()

        if poll is not None:
            print(f"✓ App beendet (Exit-Code: {poll})")
            self.on_app_closed()

    def on_app_closed(self):
        """Wird aufgerufen wenn eine App beendet wurde"""
        if self.process_check_event:
            self.process_check_event.cancel()
            self.process_check_event = None

        self.current_process = None

        Window.restore()
        Window.raise_window()

        print("↩ Zurück zum Launcher")

        # Wackeln wieder starten
        self._schedule_wiggle()

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        """Tastatur-Events"""
        if key == 27:  # ESC
            if self.is_dev_mode:
                self.stop()
                return True

        if key == 292:  # F11
            Window.fullscreen = not Window.fullscreen
            return True

        return False

    def on_stop(self):
        """Aufräumen beim Beenden"""
        if self.wiggle_event:
            self.wiggle_event.cancel()
        if self.process_check_event:
            self.process_check_event.cancel()

    def get_background_config(self):
        """Gibt die Hintergrund-Konfiguration zurück"""
        return self.config_data.get("launcher", {}).get("background", {})

    def get_grid_config(self):
        """Gibt die Grid-Konfiguration zurück"""
        return self.config_data.get("launcher", {}).get(
            "grid", {"cols": 3, "rows": 2, "padding": 60, "spacing": 40}
        )
