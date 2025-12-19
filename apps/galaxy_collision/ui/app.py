"""
Hauptanwendung mit Touch-Debugging
"""

import sys
from pathlib import Path

import numpy as np
import yaml
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget

sys.path.insert(0, str(Path(__file__).parent.parent))
from simulation import Universe
from visualization.camera import Camera3D
from visualization.renderer import GalaxyRenderer
from visualization.touch_handler import TouchHandler


class GalaxyView(Widget):
    """Galaxien-Ansicht"""

    def __init__(self, **kwargs):
        self.universe = kwargs.pop("universe", None)
        self.color_config = kwargs.pop("color_config", {})
        camera_config = kwargs.pop("camera_config", {})

        super().__init__(**kwargs)

        self.camera = Camera3D(
            distance=camera_config.get("initial_distance", 200.0),
            min_distance=camera_config.get("min_distance", 50.0),
            max_distance=camera_config.get("max_distance", 600.0),
            rotation_speed=camera_config.get("rotation_speed", 0.3),
            zoom_speed=camera_config.get("zoom_speed", 10.0),
        )

        self.touch = TouchHandler(self.camera)
        self.touch.debug = True

        with self.canvas.before:
            Color(0.01, 0.01, 0.03, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)

        self.renderer = GalaxyRenderer(self.canvas, self.color_config)

        self.bind(pos=self._upd_bg, size=self._upd_bg)

        print("[APP] GalaxyView erstellt, Touch-Debug aktiviert")

    def _upd_bg(self, *a):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.renderer.set_size(self.width, self.height)

    def _update_data(self):
        if not self.universe:
            return
        pos, col = self.universe.get_render_data()

        # Prüfen ob 1 oder 2 Galaxien
        if self.universe.galaxy_b is not None:
            vel = np.vstack(
                [self.universe.galaxy_a.velocities, self.universe.galaxy_b.velocities]
            )
        else:
            vel = self.universe.galaxy_a.velocities

        n_a = self.universe.galaxy_a.particle_count
        self.renderer.update_data(pos, col, vel, n_a)

    def set_color_mode(self, mode):
        self.renderer.set_color_mode(mode)

    def update(self, dt):
        if self.universe:
            self.universe.step(dt)
            self._update_data()
        self.renderer.set_size(self.width, self.height)
        self.renderer.render(self.camera)

    # === TOUCH EVENTS ===

    def on_touch_down(self, touch):
        """Touch beginnt"""
        if not self.collide_point(*touch.pos):
            return False

        touch.grab(self)
        self.touch.on_down(touch.uid, touch.x, touch.y)
        return True

    def on_touch_move(self, touch):
        """Touch bewegt sich"""
        if touch.grab_current is not self:
            return False

        self.touch.on_move(touch.uid, touch.x, touch.y)
        return True

    def on_touch_up(self, touch):
        """Touch endet"""
        if touch.grab_current is not self:
            return False

        touch.ungrab(self)
        self.touch.on_up(touch.uid)

        if touch.is_double_tap:
            self.camera.reset()
            print("[APP] Kamera zurückgesetzt")

        return True


class GalaxyCollisionApp(App):
    """Hauptanwendung"""

    def build(self):
        self.title = "Galaxien-Kollision"

        self.config_data = self._load_config()
        self.universe = self._create_sim()

        root = FloatLayout()

        self.view = GalaxyView(
            universe=self.universe,
            color_config=self.config_data.get("colors", {}),
            camera_config=self.config_data.get("camera", {}),
            size_hint=(1, 1),
        )
        root.add_widget(self.view)

        from ui.controls import ControlPanel

        self.panel = ControlPanel(simulation=self.universe, config=self.config_data)
        self.panel.color_mode_callback = lambda m: self.view.set_color_mode(m)
        root.add_widget(self.panel)

        # Events
        Window.bind(on_keyboard=self._on_key)
        Window.bind(mouse_pos=self._on_mouse)
        Window.bind(on_scroll=self._on_scroll)

        self._mouse_in = False
        self._update_ev = Clock.schedule_interval(self._update, 1 / 60)

        print("[APP] Anwendung gestartet")
        return root

    def _load_config(self):
        p = Path(__file__).parent.parent / "config.yaml"
        try:
            with open(p) as f:
                cfg = yaml.safe_load(f)
                print(
                    f"[APP] Config geladen: galaxies.count = {cfg.get('galaxies', {}).get('count', 'NICHT GEFUNDEN')}"
                )
                return cfg
        except Exception as e:
            print(f"[APP] Config-Fehler: {e}")
            return {}

    def _create_sim(self):
        cfg = self.config_data
        sim = cfg.get("simulation", {})
        gal = cfg.get("galaxies", {})
        col = cfg.get("collision", {})

        def g(d, fb):
            return d.get("default", fb) if isinstance(d, dict) else (d or fb)

        # Galaxy count
        galaxy_count = gal.get("count", 2)
        print(f"[APP] Erstelle Simulation mit {galaxy_count} Galaxie(n)")

        return Universe(
            {
                "simulation": {
                    "gravitational_constant": sim.get("gravitational_constant", 1.0),
                    "softening_length": sim.get("softening_length", 0.5),
                    "dynamic_friction": sim.get("dynamic_friction", 0.02),
                    "max_dt": sim.get("max_dt", 0.05),
                    "merge": sim.get(
                        "merge",
                        {
                            "enabled": True,
                            "distance": 2.0,
                            "min_passages": 2,
                            "require_bound": True,
                            "max_relative_velocity_factor": 0.3,
                        },
                    ),
                },
                "time_scale": g(sim.get("time_scale"), 1.0),
                "galaxies": {
                    "count": galaxy_count,
                    "total_particles": g(gal.get("total_particles"), 20000),
                    "mass_ratio": g(gal.get("mass_ratio"), 1.0),
                    "total_mass": g(gal.get("total_mass"), 2.0),
                    "base_radius": gal.get("base_radius", 10.0),
                },
                "collision": {
                    "initial_distance": g(col.get("initial_distance"), 50.0),
                    "velocity_factor": g(col.get("velocity_factor"), 0.6),
                    "impact_parameter": g(col.get("impact_parameter"), 0.3),
                    "inclination": g(col.get("inclination"), 30.0),
                },
                "colors": cfg.get("colors", {}),
            }
        )

    def _update(self, dt):
        if self.view:
            self.view.update(dt)
        if self.panel and self.universe:
            self.panel.update_stats(self.universe.get_stats())

    def _on_mouse(self, win, pos):
        self._mouse_in = self.view and self.view.collide_point(*pos)

    def _on_scroll(self, win, sx, sy):
        if self._mouse_in and self.view:
            self.view.camera.zoom_scroll(sy)

    def _on_key(self, win, key, sc, cp, mod):
        if key == 27:  # ESC
            self.stop()
            return True
        if key == 32:  # Space
            if self.universe:
                self.universe.toggle_pause()
                self._upd_btn()
            return True
        if key == 114:  # R
            if self.panel:
                self.panel._on_reset(None)
            return True
        return False

    def _upd_btn(self):
        if not self.panel:
            return
        btn = self.panel.play_btn
        if self.universe.paused:
            btn.text = "▶ Start"
            btn.background_color = (0.2, 0.55, 0.2, 1)
        else:
            btn.text = "⏸ Pause"
            btn.background_color = (0.55, 0.45, 0.15, 1)

    def on_stop(self):
        if hasattr(self, "_update_ev"):
            self._update_ev.cancel()


if __name__ == "__main__":
    GalaxyCollisionApp().run()
