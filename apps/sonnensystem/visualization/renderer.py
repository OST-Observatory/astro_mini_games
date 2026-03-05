"""Solar system: top-down view of ecliptic, real ephemerides."""

from datetime import datetime, timedelta, timezone

from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.widget import Widget

from simulation.ephemeris import get_orbit_samples, get_positions_at
from simulation.planet_data import (
    SUN_RADIUS_KM,
    PLANET_RADII_KM,
    PLANET_COLORS,
    get_planets_with_data,
)
from visualization.camera import SolarCamera
from visualization.touch_handler import SolarTouchHandler


class SolarSystemRenderer(Widget):
    """Pure top-down view of the ecliptic plane with Skyfield ephemerides."""

    def __init__(self, config: dict, on_planet_tap=None, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.on_planet_tap = on_planet_tap
        self.planets = get_planets_with_data()
        self.camera = SolarCamera(800, 600)  # updated on bind(size)
        touch_cfg = config.get("touch", {})
        self.touch_handler = SolarTouchHandler(
            self.camera, pinch_enabled=touch_cfg.get("pinch_enabled", True)
        )
        self._tap_tolerance = max(touch_cfg.get("tap_tolerance_px", 40), 40)
        self._multi_touch_used = False

        disp_cfg = config.get("display", {})
        self._ref_height = disp_cfg.get("reference_height", 720)
        self._min_planet_r = max(disp_cfg.get("min_planet_radius_px", 24), 16)
        self._sun_core = disp_cfg.get("sun_core_factor", 48)
        self._orbit_width = max(disp_cfg.get("orbit_line_base_width", 2), 1)

        self.show_planet_labels = True
        self.size_mode = "vergroessert"
        self.sim_date = datetime.now(timezone.utc)
        self.time_scale = 10.0
        self.paused = False
        self._orbit_cache = {}

        self.bind(size=self._on_size, pos=self._draw)
        Clock.schedule_interval(self._update, 1 / 30)

    def _on_size(self, *args):
        if self.width > 0 and self.height > 0:
            self.camera.resize(self.width, self.height)
        self._draw()

    def _scale_factor(self) -> float:
        if self.height <= 0:
            return 1.0
        return max(1.0, min(self.width, self.height) / self._ref_height)

    def _zoom_factor(self) -> float:
        """Factor from zoom: >1 = zoomed in."""
        if not hasattr(self.camera, "_initial_scale") or self.camera._initial_scale <= 0:
            return 1.0
        return self.camera.scale / self.camera._initial_scale

    def _planet_radius_px(self, name: str, is_sun: bool = False) -> float:
        zf = self._zoom_factor()
        if is_sun:
            r_km = SUN_RADIUS_KM
        else:
            r_km = PLANET_RADII_KM.get(name, 6371)

        # Sun size: always limited to ~10% of 1 AU (inside Mercury orbit)
        max_sun_px = 0.1 * self.camera.scale
        sun_px = max(3, max_sun_px)
        if is_sun:
            return sun_px

        ratio = r_km / SUN_RADIUS_KM

        if self.size_mode == "massstab":
            # Scale: planets strictly proportional to sun, correct size ratio.
            # No zf multiplication – scaling comes from camera.scale.
            r_px = ratio * sun_px
            return max(1.0, r_px)
        else:
            # Enlarged: planets visible, size scales with zoom.
            # Base proportional to sun, then with zf for zoom adjustment.
            base = ratio * 200  # Earth size ~2 px at zf=1
            r_px = base * zf
            return max(2.0, min(r_px, 48))

    def _update(self, dt):
        if not self.paused:
            self.sim_date += timedelta(days=dt * self.time_scale)
        self._draw()

    def _draw(self, *args):
        self.canvas.clear()
        if self.width <= 0 or self.height <= 0:
            return

        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        sf = self._scale_factor()
        orbit_width = max(1, int(sf * 2))

        positions = get_positions_at(self.sim_date)

        # Orbits – Kepler ellipses, computed once, stay fixed
        for p in self.planets:
            name = p["name"]
            if name not in self._orbit_cache:
                self._orbit_cache[name] = get_orbit_samples(
                    name, self.sim_date, num_points=80
                )
            pts = self._orbit_cache[name]
            if len(pts) >= 4:
                points = []
                for x, y, z in pts:
                    sx, sy = self.camera.world_to_screen(x, y, cx, cy)
                    points.extend([sx, sy])
                self.canvas.add(Color(0.35, 0.45, 0.6, 0.6))
                self.canvas.add(Line(points=points, width=orbit_width))

        # Sun (glow + core, compact inside Mercury orbit)
        sun_r = self._planet_radius_px("", is_sun=True)
        glow = sun_r + 6
        self.canvas.add(Color(1.0, 0.92, 0.6, 0.4))
        self.canvas.add(
            Ellipse(pos=(cx - glow, cy - glow), size=(glow * 2, glow * 2))
        )
        self.canvas.add(Color(1.0, 0.88, 0.4, 1))
        self.canvas.add(
            Ellipse(pos=(cx - sun_r, cy - sun_r), size=(sun_r * 2, sun_r * 2))
        )

        # Planets
        self._planet_positions = []
        for name, x, y, z in positions:
            color = PLANET_COLORS.get(name, [1, 1, 1, 1])
            sx, sy = self.camera.world_to_screen(x, y, cx, cy)
            r = self._planet_radius_px(name)
            self._planet_positions.append((name, sx, sy, r * 2, color))
            self.canvas.add(Color(1, 1, 1, 0.3))
            self.canvas.add(Ellipse(pos=(sx - r - 2, sy - r - 2), size=(r * 2 + 4, r * 2 + 4)))
            self.canvas.add(Color(*color))
            self.canvas.add(Ellipse(pos=(sx - r, sy - r), size=(r * 2, r * 2)))

        # Planet names next to planets
        if self.show_planet_labels:
            font_size = max(11, int(13 * sf * min(2.0, self._zoom_factor())))
            for p_name, sx, sy, pr, _ in self._planet_positions:
                label = CoreLabel(
                    text=p_name,
                    font_name="Roboto",
                    font_size=font_size,
                    color=(0.95, 0.95, 1.0, 0.95),
                )
                label.refresh()
                tex = label.texture
                if tex and tex.size[0] > 0:
                    lx = sx + pr / 2 + 6
                    ly = sy - tex.size[1] / 2
                    self.canvas.add(Color(0.95, 0.95, 1.0, 0.95))
                    self.canvas.add(Rectangle(texture=tex, pos=(lx, ly), size=tex.size))

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        touch.ud["down_pos"] = touch.pos
        self.touch_handler.on_down(touch.uid, touch.x, touch.y)
        if len(self.touch_handler._touches) >= 2:
            self._multi_touch_used = True
        touch.grab(self)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        self.touch_handler.on_move(touch.uid, touch.x, touch.y)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_up(touch)
        touch.ungrab(self)
        down = touch.ud.get("down_pos", touch.pos)
        dist = ((touch.pos[0] - down[0]) ** 2 + (touch.pos[1] - down[1]) ** 2) ** 0.5
        self.touch_handler.on_up(touch.uid)

        if (
            not self._multi_touch_used
            and len(self.touch_handler._touches) == 0
            and dist < self._tap_tolerance
            and hasattr(self, "_planet_positions")
        ):
            for name, px, py, pr, _ in self._planet_positions:
                d = ((touch.pos[0] - px) ** 2 + (touch.pos[1] - py) ** 2) ** 0.5
                if d < pr / 2 + self._tap_tolerance and self.on_planet_tap:
                    self.on_planet_tap(name)
                    break
        if len(self.touch_handler._touches) == 0:
            self._multi_touch_used = False
        return True
