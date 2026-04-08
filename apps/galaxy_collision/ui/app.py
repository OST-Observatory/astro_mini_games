"""
Main application with touch debugging and adaptive layout.
"""

import sys
from pathlib import Path

import numpy as np
import yaml
from shared.base_app import AstroApp
from shared.i18n import tr
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Ellipse, InstructionGroup, RoundedRectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.properties import BooleanProperty, ObjectProperty

sys.path.insert(0, str(Path(__file__).parent.parent))
from simulation import Universe
from visualization.camera import Camera3D
from visualization.renderer import GalaxyRenderer
from visualization.touch_handler import TouchHandler
from ui.controls import ControlPanel
from ui.fonts import get_font_name
from ui.onscreen_controls import OnScreenControls
from ui.theme import is_touch_layout, Colors, SPACING_MD, RADIUS_LG, DRAWER_WIDTH
from ui.symbols import S
from kivy.uix.label import Label


class StatusOverlay(FloatLayout):
    """Compact status display (t, d, N, Merged)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (160, 52)
        self.pos_hint = {"x": 0.01, "top": 0.98}
        self.label = Label(
            text="",
            font_name=get_font_name(),
            font_size="11sp",
            color=(1, 1, 1, 0.9),
            size_hint=(1, 1),
            halign="left",
            valign="top",
            padding=(SPACING_MD, SPACING_MD),
        )
        self.label.bind(size=lambda l, s: setattr(l, "text_size", (s[0] - 16, None)))
        self.add_widget(self.label)
        with self.canvas.before:
            Color(0, 0, 0, 0.45)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[RADIUS_LG])
        self.bind(pos=lambda *a: setattr(self.bg, "pos", self.pos),
                 size=lambda *a: setattr(self.bg, "size", self.size))

    def update_stats(self, stats):
        """Update displayed simulation stats (time, distance, particle count, merge status)."""
        t = stats.get("time", 0)
        d = stats.get("distance", 0)
        n = stats.get("particles", 0)
        is_merged = stats.get("is_merged", False)
        merge_time = stats.get("merge_time", 0)
        galaxy_count = stats.get("galaxy_count", 2)
        if galaxy_count == 1:
            self.label.text = f"t={t:.1f}  N={n}"
            self.label.color = (0.4, 0.8, 1, 0.95)
        elif is_merged:
            self.label.text = f"t={t:.1f}  N={n}\n{S.STAR} {tr('galaxy.overlay_merged_short', t=merge_time)}"
            self.label.color = (0.9, 0.7, 1, 0.95)
        else:
            self.label.text = f"t={t:.1f}  d={d:.1f}  N={n}"
            self.label.color = (0.9, 0.9, 0.9, 0.95)


class DrawerBackdrop(Widget):
    """Semi-transparent backdrop; tap closes drawer."""
    drawer_close_callback = ObjectProperty(None)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.drawer_close_callback:
                self.drawer_close_callback()
            return True
        return False


class GalaxyView(Widget):
    """Galaxy view."""

    swipe_open_drawer_callback = ObjectProperty(None)
    long_press_callback = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.universe = kwargs.pop("universe", None)
        self.color_config = kwargs.pop("color_config", {})
        camera_config = kwargs.pop("camera_config", {})
        self.swipe_open_drawer_callback = kwargs.pop("swipe_open_drawer_callback", None)
        self.long_press_callback = kwargs.pop("long_press_callback", None)

        super().__init__(**kwargs)
        self._swipe_start_x = None
        self._swipe_threshold = 50

        self.camera = Camera3D(
            distance=camera_config.get("initial_distance", 200.0),
            min_distance=camera_config.get("min_distance", 50.0),
            max_distance=camera_config.get("max_distance", 600.0),
            rotation_speed=camera_config.get("rotation_speed", 0.3),
            zoom_speed=camera_config.get("zoom_speed", 10.0),
        )

        # Touch handler
        touch_debug = camera_config.get("touch_debug", False)
        self.touch = TouchHandler(
            self.camera,
            debug=touch_debug,
            long_press_callback=self.long_press_callback,
        )

        with self.canvas.before:
            Color(0.01, 0.01, 0.03, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)

        self.renderer = GalaxyRenderer(self.canvas, self.color_config)

        # Touch feedback: visual indicators for active touches
        self._touch_indicators = {}  # {uid: InstructionGroup}
        self._touch_feedback_enabled = camera_config.get("touch_feedback", True)

        self.bind(pos=self._upd_bg, size=self._upd_bg)

        debug_status = "aktiviert" if self.touch.debug else "deaktiviert"
        print(f"[APP] GalaxyView erstellt, Touch-Debug {debug_status}")

    def _upd_bg(self, *a):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.renderer.set_size(self.width, self.height)

    def _update_data(self):
        if not self.universe:
            return
        pos, col = self.universe.get_render_data()

        # Check if 1 or 2 galaxies
        if self.universe.galaxy_b is not None:
            vel = np.vstack(
                [self.universe.galaxy_a.velocities, self.universe.galaxy_b.velocities]
            )
        else:
            vel = self.universe.galaxy_a.velocities

        n_a = self.universe.galaxy_a.particle_count
        self.renderer.update_data(pos, col, vel, n_a)

    def set_color_mode(self, mode):
        """Set renderer color mode (distinct, realistic, velocity, merged)."""
        self.renderer.set_color_mode(mode)

    # Max. physics step per step (60 FPS). At low frame rate, multiple steps per frame 
    # are executed to maintain numerical stability.
    PHYSICS_MAX_DT = 1.0 / 60.0

    def update(self, dt):
        """Advance simulation, update render data and render frame."""
        if self.universe:
            remaining = min(dt, 10.0)  # Cap large dt (e.g. after pause)
            while remaining > 1e-9:
                step_dt = min(remaining, self.PHYSICS_MAX_DT)
                self.universe.step(step_dt)
                remaining -= step_dt
            self._update_data()
        self.renderer.set_size(self.width, self.height)
        self.renderer.render(self.camera)

    # === TOUCH EVENTS ===

    def on_touch_down(self, touch):
        """Touch begins."""
        if not self.collide_point(*touch.pos):
            return False

        touch.grab(self)
        self.touch.on_down(touch.uid, touch.x, touch.y)
        # Swipe from right: start in right 15% of width
        if self.swipe_open_drawer_callback and touch.x > self.width * 0.85:
            self._swipe_start_x = touch.x
        else:
            self._swipe_start_x = None

        # Add visual feedback
        if self._touch_feedback_enabled:
            self._add_touch_indicator(touch.uid, touch.x, touch.y)

        return True

    def on_touch_move(self, touch):
        """Touch moves."""
        if touch.grab_current is not self:
            return False

        # Swipe from right: leftward movement > threshold
        if (
            self._swipe_start_x is not None
            and self.swipe_open_drawer_callback
            and self._swipe_start_x - touch.x >= self._swipe_threshold
        ):
            self.swipe_open_drawer_callback()
            self._swipe_start_x = None  # Only once per gesture

        self.touch.on_move(touch.uid, touch.x, touch.y)
        return True

    def on_touch_up(self, touch):
        """Touch ends."""
        if touch.grab_current is not self:
            return False

        touch.ungrab(self)
        self.touch.on_up(touch.uid)
        self._swipe_start_x = None

        # Remove touch indicator
        if self._touch_feedback_enabled:
            self._remove_touch_indicator(touch.uid)

        if touch.is_double_tap:
            self.camera.reset()
            print("[APP] Camera reset")

        return True
    
    def _add_touch_indicator(self, uid, x, y):
        """Add visual touch indicator."""
        group = InstructionGroup()
        radius = 20
        
        # Outer ring
        Color(1.0, 1.0, 1.0, 0.3)
        group.add(Ellipse(pos=(x - radius, y - radius), size=(radius * 2, radius * 2)))
        
        # Inner point
        Color(0.5, 0.7, 1.0, 0.8)
        inner_radius = 8
        group.add(Ellipse(pos=(x - inner_radius, y - inner_radius), 
                         size=(inner_radius * 2, inner_radius * 2)))
        
        self.canvas.after.add(group)
        self._touch_indicators[uid] = group
    
    def _update_touch_indicator(self, uid, x, y):
        """Update touch indicator position."""
        if uid not in self._touch_indicators:
            return
        
        group = self._touch_indicators[uid]
        radius = 20
        inner_radius = 8
        
        # Update positions (Kivy Ellipse supports pos/size directly)
        for instr in group.children:
            if isinstance(instr, Ellipse):
                if instr.size[0] == radius * 2:
                    # Outer ring
                    instr.pos = (x - radius, y - radius)
                else:
                    # Inner point
                    instr.pos = (x - inner_radius, y - inner_radius)
    
    def _remove_touch_indicator(self, uid):
        """Remove touch indicator."""
        if uid in self._touch_indicators:
            group = self._touch_indicators[uid]
            self.canvas.after.remove(group)
            del self._touch_indicators[uid]


class GalaxyCollisionApp(AstroApp):
    """Main application."""

    # Left side: control panel / drawer is on the right; top-left has status overlay.
    language_switcher_pos_hint = {"x": 0.03, "top": 0.98}

    def _apply_locale(self):
        super()._apply_locale()
        if getattr(self, "panel", None):
            self.panel.apply_i18n()

    def build(self):
        """Build the galaxy collision UI: view, drawer, controls, status overlay."""
        self.title = "Galaxien-Kollision"

        self.config_data = self._load_config()
        self.universe = self._create_sim()

        ui_cfg = self.config_data.get("ui", {})
        layout_mode = ui_cfg.get("layout_mode", "auto")
        breakpoint_w = ui_cfg.get("breakpoint_width", 768)
        drawer_w = ui_cfg.get("drawer_width", 320)
        self._adaptive_quality = ui_cfg.get("adaptive_quality", True)

        win_w = Window.size[0]
        self._use_drawer = is_touch_layout(win_w, layout_mode, breakpoint_w)
        self._drawer_open = False
        self._drawer_width = drawer_w

        root = FloatLayout()

        self.view = GalaxyView(
            universe=self.universe,
            color_config=self.config_data.get("colors", {}),
            camera_config=self.config_data.get("camera", {}),
            size_hint=(1, 1),
            swipe_open_drawer_callback=self._open_drawer if self._use_drawer else None,
            long_press_callback=self._on_long_press,
        )
        root.add_widget(self.view)

        self.panel = ControlPanel(
            simulation=self.universe,
            config=self.config_data,
            use_drawer=self._use_drawer,
            drawer_width=drawer_w,
        )
        self.panel.color_mode_callback = lambda m: self.view.set_color_mode(m)

        if self._use_drawer:
            # Backdrop (invisible when drawer closed)
            self._backdrop = DrawerBackdrop(
                size_hint=(1, 1),
                drawer_close_callback=self._close_drawer,
            )
            with self._backdrop.canvas.before:
                Color(*Colors.BG_OVERLAY)
                self._backdrop_rect = Rectangle(pos=self._backdrop.pos, size=self._backdrop.size)
            self._backdrop.bind(pos=lambda *a: setattr(self._backdrop_rect, "pos", self._backdrop.pos),
                                size=lambda *a: setattr(self._backdrop_rect, "size", self._backdrop.size))
            self._backdrop.opacity = 0
            self._backdrop.disabled = True
            root.add_widget(self._backdrop)

            # Panel container (right, animated in/out)
            self._panel_container = FloatLayout(
                size_hint=(None, 1),
                width=drawer_w,
            )
            self.panel.size_hint_x = None
            self.panel.width = drawer_w
            self.panel.size_hint_y = 1
            self.panel.pos_hint = {"x": 0, "y": 0}
            self._panel_container.add_widget(self.panel)
            root.add_widget(self._panel_container)

            def _position_drawer(*args):
                rw, rh = root.size
                self._panel_container.size = (drawer_w, rh)
                self._panel_container.x = rw - drawer_w if self._drawer_open else rw
                self._panel_container.y = 0

            root.bind(size=_position_drawer)
            Clock.schedule_once(lambda dt: _position_drawer(), 0)

            # FAB settings
            fab_size = 56
            self._fab = Button(
                text=S.SETTINGS,
                font_name=get_font_name(),
                font_size="28sp",
                size_hint=(None, None),
                size=(fab_size, fab_size),
                pos_hint={"right": 1, "top": 0.92},
                background_color=(*Colors.NEUTRAL[:3], 0.9),
                background_normal="",
            )
            with self._fab.canvas.before:
                Color(*Colors.NEUTRAL[:3], 0.9)
                self._fab_bg = RoundedRectangle(
                    pos=self._fab.pos, size=self._fab.size, radius=[RADIUS_LG]
                )
            self._fab.bind(pos=lambda i, p: setattr(self._fab_bg, "pos", p),
                         size=lambda i, s: setattr(self._fab_bg, "size", s))
            self._fab.bind(on_release=lambda _: self._toggle_drawer())
            root.add_widget(self._fab)
        else:
            root.add_widget(self.panel)
            self._backdrop = None
            self._panel_container = None
            self._fab = None

        # Status overlay (top left)
        self.status_overlay = StatusOverlay()
        root.add_widget(self.status_overlay)

        # On-screen controls (status first, then bar – bar last for reliable touches)
        show_zoom = ui_cfg.get("show_zoom_buttons", True)
        self.onscreen_controls = OnScreenControls(
            simulation=self.universe,
            use_drawer=self._use_drawer,
            show_zoom_buttons=show_zoom,
        )
        root.add_widget(self.onscreen_controls)

        # Events
        Window.bind(on_keyboard=self._on_key)
        Window.bind(mouse_pos=self._on_mouse)
        Window.bind(on_scroll=self._on_scroll)

        self._mouse_in = False
        
        # FPS monitoring and adaptive rendering
        self._fps_history = []
        self._target_fps = 60.0
        self._current_fps = 60.0
        self._quality_level = 1.0  # 1.0 = full, 0.5 = reduced, etc.
        self._fps_update_interval = 1.0  # Seconds between FPS updates
        self._last_fps_update = 0.0
        self._frame_count = 0
        self._last_frame_time = 0.0
        import time
        self._last_frame_time = time.time()
        
        # Adaptive update rate
        self._update_ev = Clock.schedule_interval(self._update, 1 / self._target_fps)
        
        # FPS monitor
        Clock.schedule_interval(self._update_fps, self._fps_update_interval)

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
        print(f"[APP] Creating simulation with {galaxy_count} galaxy(ies)")

        return Universe(
            {
                "simulation": {
                    "gravitational_constant": sim.get("gravitational_constant", 1.0),
                    "softening_length": g(sim.get("softening_length"), 1.0),
                    "dynamic_friction": g(sim.get("dynamic_friction"), 0.01),
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
                    "velocity_factor": g(col.get("velocity_factor"), 0.5),
                    "impact_parameter": g(col.get("impact_parameter"), 0.3),
                    "inclination": g(col.get("inclination"), 30.0),
                },
                "colors": cfg.get("colors", {}),
            }
        )

    def _update(self, dt):
        import time
        current_time = time.time()
        
        # FPS calculation
        if self._last_frame_time > 0:
            frame_time = current_time - self._last_frame_time
            if frame_time > 0:
                instant_fps = 1.0 / frame_time
                self._fps_history.append(instant_fps)
                if len(self._fps_history) > 60:  # Last 60 frames
                    self._fps_history.pop(0)
        self._last_frame_time = current_time
        self._frame_count += 1
        
        if self._adaptive_quality:
            self._adjust_quality()
        
        if self.view:
            self.view.update(dt)
        if self.universe:
            stats = self.universe.get_stats()
            if self.panel:
                self.panel.update_stats(stats)
            if self.status_overlay:
                self.status_overlay.update_stats(stats)
    
    def _update_fps(self, dt):
        """Compute average FPS."""
        if len(self._fps_history) > 0:
            self._current_fps = sum(self._fps_history) / len(self._fps_history)
            # Debug output only when touch debug is enabled
            if self.view and hasattr(self.view, 'touch') and self.view.touch.debug:
                print(f"[FPS] Aktuell: {self._current_fps:.1f} FPS, Quality: {self._quality_level:.2f}")
    
    def _adjust_quality(self):
        """Adjust quality based on FPS."""
        if len(self._fps_history) < 10:  # Wait for enough data
            return
        
        avg_fps = sum(self._fps_history[-10:]) / 10
        
        # Ziel: 30-60 FPS
        if avg_fps < 25:
            # Too slow: reduce quality
            self._quality_level = max(0.3, self._quality_level - 0.05)
            if hasattr(self.view, 'renderer'):
                # Reduce particle count in renderer
                self.view.renderer.set_quality(self._quality_level)
        elif avg_fps > 55 and self._quality_level < 1.0:
            # Good: increase quality slowly
            self._quality_level = min(1.0, self._quality_level + 0.02)
            if hasattr(self.view, 'renderer'):
                self.view.renderer.set_quality(self._quality_level)
        
        # Adjust update rate
        if avg_fps < 30:
            # Reduce to 30 FPS if too slow
            new_target = 30.0
        elif avg_fps > 50:
            # Increase to 60 FPS if possible
            new_target = 60.0
        else:
            new_target = self._target_fps
        
        if abs(new_target - self._target_fps) > 5:
            self._target_fps = new_target
            if hasattr(self, '_update_ev'):
                self._update_ev.cancel()
                self._update_ev = Clock.schedule_interval(self._update, 1 / self._target_fps)

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

    def _open_drawer(self):
        if not self._use_drawer or self._drawer_open:
            return
        self._drawer_open = True
        self._backdrop.disabled = False
        rw = self.root.size[0]
        anim = Animation(x=rw - self._drawer_width, d=0.2, t="out_cubic")
        anim.start(self._panel_container)
        Animation(opacity=1, d=0.2).start(self._backdrop)

    def _close_drawer(self):
        if not self._use_drawer or not self._drawer_open:
            return
        self._drawer_open = False
        self._backdrop.disabled = True
        rw = self.root.size[0]
        anim = Animation(x=rw, d=0.2, t="out_cubic")
        anim.start(self._panel_container)
        Animation(opacity=0, d=0.2).start(self._backdrop)

    def _toggle_drawer(self):
        if self._drawer_open:
            self._close_drawer()
        else:
            self._open_drawer()

    def _on_long_press(self, x, y):
        """Long-press on GalaxyView: opens drawer (touch) or does nothing (desktop)."""
        if self._use_drawer and not self._drawer_open:
            self._open_drawer()

    def _upd_btn(self):
        """Sync play/pause button (OnScreenControls only)."""
        if hasattr(self, "onscreen_controls") and self.onscreen_controls:
            self.onscreen_controls.update_play_button(self.universe.paused)

    def on_stop(self):
        if hasattr(self, "_update_ev"):
            self._update_ev.cancel()


if __name__ == "__main__":
    GalaxyCollisionApp().run()
