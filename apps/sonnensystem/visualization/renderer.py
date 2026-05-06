"""Solar system: top-down view of ecliptic, real ephemerides."""

import math
from datetime import datetime, timedelta, timezone

from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics.vertex_instructions import Point
from kivy.uix.widget import Widget

from shared.i18n import tr

from simulation.ephemeris import get_orbit_samples, get_positions_at
from simulation.planet_data import (
    SUN_RADIUS_KM,
    body_color_rgba,
    body_radius_km,
    get_dwarf_planets_with_data,
    get_planets_with_data,
)
from visualization.belt_particles import (
    belt_phase_rad,
    belt_screen_points_flat,
    build_ring_particles,
    build_spherical_shell_particles,
    cloud_xy_screen_points_flat,
)
from visualization.camera import NEPTUNE_AU, SolarCamera
from visualization.touch_handler import SolarTouchHandler

_BELT_PRESETS = {
    "asteroid": {
        "enabled": True,
        "count": 240,
        "seed": 41,
        "r_min_au": 2.0,
        "r_max_au": 3.4,
        "jitter_au": 0.08,
        "rotation_deg_per_year": 2.5,
        "rad_per_day": None,
        "pointsize": 2.5,
        "rgba": [0.55, 0.52, 0.48, 0.85],
    },
    "kuiper": {
        "enabled": True,
        "count": 100,
        "seed": 73,
        "r_min_au": 41.0,
        "r_max_au": 50.0,
        "jitter_au": 0.5,
        "rotation_deg_per_year": 0.0,
        "rad_per_day": None,
        "pointsize": 2.0,
        "rgba": [0.38, 0.42, 0.55, 0.65],
    },
}

_OORT_PRESET = {
    "enabled": True,
    "reference_au": 100000.0,
    "outer_view_au": 105000.0,
    "outer_view_margin": 1.08,
    "min_zoom_factor": 0.055,
    "r_min_au": 2500.0,
    "r_max_au": 100000.0,
    "count": 14000,
    "seed": 911,
    "rotation_deg_per_year": 0.012,
    "rad_per_day": None,
    "pointsize": 1.75,
    "rgba": [0.34, 0.40, 0.52, 0.42],
}


class SolarSystemRenderer(Widget):
    """Pure top-down view of the ecliptic plane with Skyfield ephemerides."""

    def __init__(
        self,
        config: dict,
        on_planet_tap=None,
        on_region_changed=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.config = config
        self.on_planet_tap = on_planet_tap
        self.on_region_changed = on_region_changed
        self.planets = get_planets_with_data()
        self.dwarf_planets = get_dwarf_planets_with_data()
        cam_cfg = config.get("camera") or {}
        self._inner_cam_profile = {
            "reference_au": NEPTUNE_AU,
            "outer_view_au": cam_cfg.get("outer_view_au"),
            "outer_view_margin": float(cam_cfg.get("outer_view_margin", 1.05)),
            "min_zoom_factor": 0.12,
        }
        self.camera = SolarCamera(
            800,
            600,
            reference_au=self._inner_cam_profile["reference_au"],
            min_zoom_factor=self._inner_cam_profile["min_zoom_factor"],
            outer_view_au=self._inner_cam_profile["outer_view_au"],
            outer_view_margin=self._inner_cam_profile["outer_view_margin"],
        )
        self._oort_cam_profile, self._oort_layer = self._build_oort_from_config()
        self.space_region = "inner"
        self._cam_stash_inner: tuple[float, float] | None = None
        self._cam_stash_oort: tuple[float, float] | None = None
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
        self._orbit_width_min = float(disp_cfg.get("orbit_line_width_min", 1.0))
        _max = disp_cfg.get("orbit_line_width_max")
        self._orbit_width_max = (
            float(_max) if _max is not None else float("inf")
        )
        if self._orbit_width_max < self._orbit_width_min:
            self._orbit_width_min, self._orbit_width_max = (
                self._orbit_width_max,
                self._orbit_width_min,
            )

        self.show_planet_labels = True
        self.size_mode = "vergroessert"
        self.sim_date = datetime.now(timezone.utc)
        self.time_scale = 10.0
        self.paused = False
        self._orbit_cache = {}
        self._belt_layers = self._build_belt_layers()
        self._lp_anchor_touch = None

        self.bind(size=self._on_size, pos=self._draw)
        Clock.schedule_interval(self._update, 1 / 30)

    def _on_size(self, *args):
        if self.width > 0 and self.height > 0:
            self.camera.resize(self.width, self.height)
        self._draw()

    def _build_belt_layers(self) -> list[dict]:
        belts_cfg = self.config.get("belts")
        if belts_cfg is None:
            belts_cfg = {}
        layers: list[dict] = []
        for key in ("asteroid", "kuiper"):
            preset = _BELT_PRESETS[key].copy()
            raw = belts_cfg.get(key)
            if isinstance(raw, dict):
                preset.update(raw)
                if (
                    "jitter_au" not in raw
                    and raw.get("thickness_jitter_au") is not None
                ):
                    preset["jitter_au"] = raw["thickness_jitter_au"]
            if not preset.get("enabled", True):
                continue
            _ju = preset.get("jitter_au")
            jitter_au_val = float(_ju if _ju is not None else 0.0)
            particles = build_ring_particles(
                float(preset["r_min_au"]),
                float(preset["r_max_au"]),
                int(preset["count"]),
                int(preset["seed"]),
                jitter_au=jitter_au_val,
            )
            rad_pd = preset.get("rad_per_day")
            r_lo = float(preset["r_min_au"])
            r_hi = float(preset["r_max_au"])
            layers.append(
                {
                    "particles": particles,
                    "deg_per_year": float(preset.get("rotation_deg_per_year") or 0.0),
                    "rad_per_day": (
                        float(rad_pd) if rad_pd is not None else None
                    ),
                    "pointsize": float(preset["pointsize"]),
                    "rgba": [float(c) for c in preset["rgba"]],
                    "r_min_au": r_lo,
                    "r_max_au": r_hi,
                    "info_key": (
                        "belt_asteroid" if key == "asteroid" else "belt_kuiper"
                    ),
                }
            )
        return layers

    def _build_oort_from_config(self) -> tuple[dict, dict | None]:
        raw = self.config.get("oort")
        if raw is None:
            raw = {}
        preset = _OORT_PRESET.copy()
        if isinstance(raw, dict):
            preset.update(raw)
        cam_profile = {
            "reference_au": float(preset["reference_au"]),
            "outer_view_au": preset.get("outer_view_au"),
            "outer_view_margin": float(preset.get("outer_view_margin", 1.08)),
            "min_zoom_factor": float(preset.get("min_zoom_factor", 0.055)),
        }
        if not preset.get("enabled", True):
            return cam_profile, None
        particles_xy = build_spherical_shell_particles(
            float(preset["r_min_au"]),
            float(preset["r_max_au"]),
            int(preset["count"]),
            int(preset["seed"]),
        )
        rad_pd = preset.get("rad_per_day")
        layer = {
            "particles_xy": particles_xy,
            "deg_per_year": float(preset.get("rotation_deg_per_year") or 0.0),
            "rad_per_day": float(rad_pd) if rad_pd is not None else None,
            "pointsize": float(preset["pointsize"]),
            "rgba": [float(c) for c in preset["rgba"]],
            "r_min_au": float(preset["r_min_au"]),
            "r_max_au": float(preset["r_max_au"]),
            "info_key": "belt_oort",
        }
        return cam_profile, layer

    def toggle_space_region(self):
        if self._oort_layer is None:
            return
        self.set_space_region("oort" if self.space_region == "inner" else "inner")

    def set_space_region(self, region: str):
        region = "oort" if region == "oort" else "inner"
        if region == "oort" and self._oort_layer is None:
            return
        if region == self.space_region:
            return

        if self.space_region == "inner":
            self._cam_stash_inner = (self.camera.scale, self.camera.angle)
        else:
            self._cam_stash_oort = (self.camera.scale, self.camera.angle)

        self.space_region = region

        if region == "inner":
            p = self._inner_cam_profile
            self.camera.apply_profile(
                p["reference_au"],
                outer_view_au=p["outer_view_au"],
                outer_view_margin=p["outer_view_margin"],
                min_zoom_factor=p["min_zoom_factor"],
                preserve_zoom_ratio=False,
            )
            if self._cam_stash_inner is not None:
                sc, an = self._cam_stash_inner
                self.camera.angle = an
                self.camera.scale = max(
                    self.camera.min_scale,
                    min(self.camera.max_scale, sc),
                )
            else:
                self.camera.reset_view()
        else:
            p = self._oort_cam_profile
            self.camera.apply_profile(
                p["reference_au"],
                outer_view_au=p["outer_view_au"],
                outer_view_margin=p["outer_view_margin"],
                min_zoom_factor=p["min_zoom_factor"],
                preserve_zoom_ratio=False,
            )
            if self._cam_stash_oort is not None:
                sc, an = self._cam_stash_oort
                self.camera.angle = an
                self.camera.scale = max(
                    self.camera.min_scale,
                    min(self.camera.max_scale, sc),
                )
            else:
                self.camera.angle = 0.0
                self.camera.scale = self.camera._initial_scale

        if self.on_region_changed:
            self.on_region_changed(self.space_region)
        self._draw()

    def _cancel_long_press(self, touch):
        cb = touch.ud.pop("long_press_cb", None)
        if cb is not None:
            Clock.unschedule(cb)

    def _schedule_long_press(self, touch):
        def cb(dt):
            touch.ud.pop("long_press_cb", None)
            self._long_press_region_toggle(touch)

        touch.ud["long_press_cb"] = cb
        Clock.schedule_once(cb, 0.55)

    def _long_press_region_toggle(self, touch):
        if self._oort_layer is None:
            return
        if touch.grab_current is not self:
            return
        if self._multi_touch_used:
            return
        down = touch.ud.get("down_pos", touch.pos)
        if math.hypot(touch.x - down[0], touch.y - down[1]) > self._tap_tolerance:
            return
        self.toggle_space_region()

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
            r_km = body_radius_km(name)

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
            r_px = max(1.0, r_px)
        else:
            # Enlarged: planets visible, size scales with zoom.
            # Base proportional to sun, then with zf for zoom adjustment.
            base = ratio * 200  # Earth size ~2 px at zf=1
            r_px = base * zf
            r_px = max(2.0, min(r_px, 48))

        # Dwarf planets / small bodies stay visible when enlarged
        if r_km < 2800:
            floor = 4.5 if self.size_mode != "massstab" else 2.0
            r_px = max(r_px, floor)
        return r_px

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

        if self.space_region == "oort":
            self._draw_oort(cx, cy)
            return

        sf = self._scale_factor()
        zf = self._zoom_factor()
        orbit_width = sf * self._orbit_width / zf
        orbit_width = max(
            self._orbit_width_min,
            min(self._orbit_width_max, orbit_width),
        )

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

        dwarf_orbit_width = max(1.0, orbit_width * 0.58)
        for p in self.dwarf_planets:
            name = p["name"]
            if name not in self._orbit_cache:
                n_orbit = 168 if name == "Sedna" else 96
                self._orbit_cache[name] = get_orbit_samples(
                    name, self.sim_date, num_points=n_orbit
                )
            pts = self._orbit_cache[name]
            if len(pts) >= 4:
                points = []
                for x, y, z in pts:
                    sx, sy = self.camera.world_to_screen(x, y, cx, cy)
                    points.extend([sx, sy])
                if name == "Sedna":
                    c = body_color_rgba("Sedna")
                    self.canvas.add(Color(c[0], c[1], c[2], 0.82))
                    self.canvas.add(Line(points=points, width=dwarf_orbit_width))
                else:
                    self.canvas.add(Color(0.46, 0.36, 0.52, 0.52))
                    self.canvas.add(Line(points=points, width=dwarf_orbit_width))

        # Belt pseudo-particles (after orbit lines, before Sun/planets)
        for layer in self._belt_layers:
            particles = layer["particles"]
            if not particles:
                continue
            phase = belt_phase_rad(
                self.sim_date,
                layer["deg_per_year"],
                layer["rad_per_day"],
            )
            flat = belt_screen_points_flat(
                particles,
                phase,
                self.camera.world_to_screen,
                cx,
                cy,
            )
            if len(flat) < 4:
                continue
            rgba = layer["rgba"]
            self.canvas.add(Color(rgba[0], rgba[1], rgba[2], rgba[3]))
            self.canvas.add(
                Point(points=flat, pointsize=layer["pointsize"])
            )

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

        # Major planets first, then dwarf planets (drawn on top)
        self._planet_positions = []
        major_names = {p["name"] for p in self.planets}
        dwarf_names = {p["name"] for p in self.dwarf_planets}

        def draw_sphere(name: str, x: float, y: float, z: float):
            color = body_color_rgba(name)
            sx, sy = self.camera.world_to_screen(x, y, cx, cy)
            r = self._planet_radius_px(name)
            self._planet_positions.append((name, sx, sy, r * 2, color))
            self.canvas.add(Color(1, 1, 1, 0.3))
            self.canvas.add(Ellipse(pos=(sx - r - 2, sy - r - 2), size=(r * 2 + 4, r * 2 + 4)))
            self.canvas.add(Color(*color))
            self.canvas.add(Ellipse(pos=(sx - r, sy - r), size=(r * 2, r * 2)))

        for name, x, y, z in positions:
            if name in major_names:
                draw_sphere(name, x, y, z)
        for name, x, y, z in positions:
            if name in dwarf_names:
                draw_sphere(name, x, y, z)
        # Planet names next to planets and dwarfs
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

    def _draw_oort_inner_rim(self, cx: float, cy: float, r_au: float):
        n = 128
        pts: list[float] = []
        for i in range(n + 1):
            t = 2 * math.pi * i / n
            sx, sy = self.camera.world_to_screen(
                r_au * math.cos(t), r_au * math.sin(t), cx, cy
            )
            pts.extend([sx, sy])
        self.canvas.add(Color(0.42, 0.48, 0.58, 0.32))
        self.canvas.add(Line(points=pts, width=1))

    def _draw_oort(self, cx: float, cy: float):
        """Schematic spherical Oort cloud (separate camera scale)."""
        self._planet_positions = []

        # Sedna orbit as shared AU scale reference (no central Sun in this view)
        if "Sedna" not in self._orbit_cache:
            self._orbit_cache["Sedna"] = get_orbit_samples(
                "Sedna", self.sim_date, num_points=168
            )
        sed_pts = self._orbit_cache["Sedna"]
        sed_oort_label: tuple | None = None  # (texture, pos, color tuple length 4)
        if len(sed_pts) >= 4:
            sed_line: list[float] = []
            ap_idx = 0
            ap_r2 = -1.0
            for i, (x, y, z) in enumerate(sed_pts):
                sx, sy = self.camera.world_to_screen(x, y, cx, cy)
                sed_line.extend([sx, sy])
                r2 = x * x + y * y
                if r2 > ap_r2:
                    ap_r2 = r2
                    ap_idx = i
            c = body_color_rgba("Sedna")
            self.canvas.add(Color(c[0], c[1], c[2], 0.88))
            self.canvas.add(Line(points=sed_line, width=1.35))

            # Label offset in AU (Orbit liegt bei Startzoom nur wenige px vom Zentrum).
            ax, ay, _ = sed_pts[ap_idx]
            au_r = math.hypot(ax, ay)
            if au_r > 1e-9:
                ux, uy = ax / au_r, ay / au_r
                bump_au = max(au_r * 0.12, 120.0)
                lxw, lyw = ax + ux * bump_au, ay + uy * bump_au
                lsx, lsy = self.camera.world_to_screen(lxw, lyw, cx, cy)
                rdx = lsx - cx
                rdy = lsy - cy
                rnm = math.hypot(rdx, rdy)
                if rnm > 1e-6:
                    rdx /= rnm
                    rdy /= rnm
                    px = -rdy
                    py = rdx
                    sf = self._scale_factor()
                    side = max(14.0, 18.0 * sf)
                    lx = lsx + px * side
                    ly = lsy + py * side
                    lbl_rgba = (
                        min(1.0, c[0] * 0.55 + 0.45),
                        min(1.0, c[1] * 0.55 + 0.45),
                        min(1.0, c[2] * 0.55 + 0.55),
                        1.0,
                    )
                    lbl = CoreLabel(
                        text=tr("sonnensystem.sedna_orbit_label"),
                        font_name="Roboto",
                        font_size=max(13, int(16 * sf)),
                        bold=True,
                        color=lbl_rgba,
                    )
                    lbl.refresh()
                    tex = lbl.texture
                    if tex and tex.size[0] > 0:
                        tw, th = tex.size
                        sed_oort_label = (
                            tex,
                            (lx, ly - th / 2),
                            lbl_rgba,
                            tex.size,
                        )

        layer = self._oort_layer
        if layer and layer["particles_xy"]:
            phase = belt_phase_rad(
                self.sim_date,
                layer["deg_per_year"],
                layer["rad_per_day"],
            )
            flat = cloud_xy_screen_points_flat(
                layer["particles_xy"],
                phase,
                self.camera.world_to_screen,
                cx,
                cy,
            )
            if len(flat) >= 4:
                rgba = layer["rgba"]
                self.canvas.add(Color(rgba[0], rgba[1], rgba[2], rgba[3]))
                self.canvas.add(Point(points=flat, pointsize=layer["pointsize"]))
            self._draw_oort_inner_rim(cx, cy, layer["r_min_au"])

        if sed_oort_label is not None:
            tex, pos, rgba4, tsize = sed_oort_label
            self.canvas.add(Color(rgba4[0], rgba4[1], rgba4[2], rgba4[3]))
            self.canvas.add(Rectangle(texture=tex, pos=pos, size=tsize))

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        touch.ud["down_pos"] = touch.pos
        self.touch_handler.on_down(touch.uid, touch.x, touch.y)
        n = len(self.touch_handler._touches)
        if n == 1 and self._oort_layer is not None:
            self._lp_anchor_touch = touch
            self._schedule_long_press(touch)
        elif n >= 2:
            if self._lp_anchor_touch is not None:
                self._cancel_long_press(self._lp_anchor_touch)
                self._lp_anchor_touch = None
            self._multi_touch_used = True
        touch.grab(self)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        self.touch_handler.on_move(touch.uid, touch.x, touch.y)
        if touch is self._lp_anchor_touch:
            down = touch.ud.get("down_pos", touch.pos)
            if (
                math.hypot(touch.x - down[0], touch.y - down[1])
                > self._tap_tolerance
            ):
                self._cancel_long_press(touch)
                self._lp_anchor_touch = None
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_up(touch)
        if touch is self._lp_anchor_touch:
            self._cancel_long_press(touch)
            self._lp_anchor_touch = None
        touch.ungrab(self)
        down = touch.ud.get("down_pos", touch.pos)
        dist = ((touch.pos[0] - down[0]) ** 2 + (touch.pos[1] - down[1]) ** 2) ** 0.5
        self.touch_handler.on_up(touch.uid)

        if (
            not self._multi_touch_used
            and len(self.touch_handler._touches) == 0
            and dist < self._tap_tolerance
            and hasattr(self, "_planet_positions")
            and self.on_planet_tap
        ):
            tapped = False
            for name, px, py, pr, _ in self._planet_positions:
                d = ((touch.pos[0] - px) ** 2 + (touch.pos[1] - py) ** 2) ** 0.5
                if d < pr / 2 + self._tap_tolerance:
                    self.on_planet_tap(name)
                    tapped = True
                    break
            if (
                not tapped
                and self.width > 0
                and self.height > 0
                and self.space_region == "inner"
            ):
                cx = self.x + self.width / 2
                cy = self.y + self.height / 2
                x_au, y_au = self.camera.screen_to_world_au(
                    touch.pos[0], touch.pos[1], cx, cy
                )
                r = math.hypot(x_au, y_au)
                pad_au = max(
                    6.0 / self.camera.scale,
                    0.12,
                )
                for layer in self._belt_layers:
                    lo = layer["r_min_au"] - pad_au
                    hi = layer["r_max_au"] + pad_au
                    if lo <= r <= hi:
                        self.on_planet_tap(layer["info_key"])
                        break
            elif (
                not tapped
                and self.space_region == "oort"
                and self._oort_layer
            ):
                cx = self.x + self.width / 2
                cy = self.y + self.height / 2
                x_au, y_au = self.camera.screen_to_world_au(
                    touch.pos[0], touch.pos[1], cx, cy
                )
                r = math.hypot(x_au, y_au)
                ol = self._oort_layer
                pad_au = max(
                    80.0 / self.camera.scale,
                    ol["r_max_au"] * 0.015,
                )
                lo = ol["r_min_au"] - pad_au
                hi = ol["r_max_au"] + pad_au
                if lo <= r <= hi:
                    self.on_planet_tap(ol["info_key"])
        if len(self.touch_handler._touches) == 0:
            self._multi_touch_used = False
        return True
