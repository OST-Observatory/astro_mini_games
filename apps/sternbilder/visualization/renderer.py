"""Draw stars and constellation lines on canvas."""

from kivy.graphics import Color, Ellipse, Line
from kivy.uix.widget import Widget

from star_map.data_loader import (
    load_stars,
    load_constellations,
    load_config,
    get_star_ids_for_constellation,
)
from star_map.projection import ra_dec_to_xy, fit_projected_to_screen


class StarMapRenderer(Widget):
    """Widget that draws star map with constellations."""

    def __init__(self, center_ra=100, center_dec=30, on_tap=None, **kwargs):
        super().__init__(**kwargs)
        self.on_tap_callback = on_tap
        self.center_ra = center_ra
        self.center_dec = center_dec
        self.stars = load_stars()
        self.constellations = load_constellations()
        self.stars_by_id = {s["id"]: s for s in self.stars}
        self.screen_coords = {}
        self.mode = "learn"  # "learn" | "quiz"
        self.bottom_reserve_fraction = 0.0  # Space for buttons (e.g. 0.4 for MC)
        self.top_reserve_fraction = 0.0  # Space for label (e.g. 0.15 for tap quiz)
        self.highlighted_constellation = None
        self.display_only_constellation = None  # Only show this constellation (learn mode)
        self.highlight_asterism_pairs = False  # Highlight Big Dipper in Ursa Major
        self.session_constellations = None
        cfg = load_config()
        disp = cfg.get("display", {})
        self._r_min = disp.get("star_size_min", 1)
        self._r_max = disp.get("star_size_max", 8)
        self.bind(size=self._draw, pos=self._draw)

    def _draw(self, *args):
        self.canvas.clear()
        if self.width <= 0 or self.height <= 0:
            return

        stars_to_show = self.stars
        if self.display_only_constellation:
            star_ids = get_star_ids_for_constellation(self.display_only_constellation)
            stars_to_show = [s for s in self.stars if s["id"] in star_ids]
        elif self.session_constellations:
            star_ids = set()
            for cname in self.session_constellations:
                star_ids.update(get_star_ids_for_constellation(cname))
            stars_to_show = [s for s in self.stars if s["id"] in star_ids]

        # Project all stars to display (stereographic)
        projected = []
        for s in stars_to_show:
            x, y = ra_dec_to_xy(s["ra"], s["dec"], self.center_ra, self.center_dec)
            projected.append((x, y))

        reserve_bottom = self.height * max(0.0, min(1.0, self.bottom_reserve_fraction))
        reserve_top = self.height * max(0.0, min(1.0, self.top_reserve_fraction))
        usable_h = self.height - reserve_bottom - reserve_top
        scale, offset_x, offset_y = fit_projected_to_screen(
            projected, self.width, usable_h
        )
        offset_y += reserve_bottom

        def to_screen(x, y):
            sx = offset_x + x * scale
            sy = offset_y + y * scale
            return (sx, sy)

        self.screen_coords = {}
        for s, (x, y) in zip(stars_to_show, projected):
            self.screen_coords[s["id"]] = to_screen(x, y)
        for s in self.stars:
            if s["id"] not in self.screen_coords:
                x, y = ra_dec_to_xy(s["ra"], s["dec"], self.center_ra, self.center_dec)
                self.screen_coords[s["id"]] = to_screen(x, y)

        mag_min = min(s.get("mag", 3) for s in stars_to_show) if stars_to_show else 3
        mag_max = max(s.get("mag", 4) for s in stars_to_show) if stars_to_show else 4
        flux_max = 10 ** (-0.4 * mag_min)
        flux_min = 10 ** (-0.4 * mag_max)
        flux_range = max(flux_max - flux_min, 1e-10)

        if self.display_only_constellation and self.display_only_constellation in self.constellations:
            constellations_to_draw = [(self.display_only_constellation, self.constellations[self.display_only_constellation])]
        elif self.session_constellations:
            constellations_to_draw = [
                (n, self.constellations[n])
                for n in self.session_constellations
                if n in self.constellations
            ]
        else:
            constellations_to_draw = list(self.constellations.items())

        for const_name, const_data in constellations_to_draw:
            pairs = const_data.get("star_pairs", [])
            bd_pairs = set()
            if self.highlight_asterism_pairs and const_name == "Große Bärin":
                bd = const_data.get("big_dipper_pairs", [])
                bd_pairs = {tuple(sorted([a, b])) for a, b in bd}

            for a, b in pairs:
                pa = self.screen_coords.get(a)
                pb = self.screen_coords.get(b)
                if not pa or not pb:
                    continue
                key = tuple(sorted([a, b]))
                is_big_dipper = key in bd_pairs
                is_highlight = self.highlighted_constellation == const_name
                if is_highlight or is_big_dipper:
                    self.canvas.add(Color(1.0, 0.85, 0.3, 1))
                    w = 2.5 if is_big_dipper else 1.5
                else:
                    self.canvas.add(Color(0.6, 0.7, 1.0, 0.8))
                    w = 1.5
                self.canvas.add(Line(points=[pa[0], pa[1], pb[0], pb[1]], width=w))

        for s, (x, y) in zip(stars_to_show, projected):
            sx, sy = to_screen(x, y)
            self.screen_coords[s["id"]] = (sx, sy)

            mag = s.get("mag", 3)
            flux = 10 ** (-0.4 * mag)
            flux_norm = (flux - flux_min) / flux_range
            r = self._r_min + flux_norm * (self._r_max - self._r_min)
            r = max(self._r_min, min(self._r_max, r))
            self.canvas.add(Color(1, 1, 1, 0.95))
            self.canvas.add(Ellipse(pos=(sx - r / 2, sy - r / 2), size=(r, r)))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_tap_callback:
                self.on_tap_callback(touch.pos[0], touch.pos[1])
            return True
        return super().on_touch_down(touch)
