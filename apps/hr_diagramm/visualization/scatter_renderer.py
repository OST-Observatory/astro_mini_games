"""Scatter plot renderer for HR diagram."""

from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.widget import Widget

from diagram.data_loader import load_stars
from diagram.plot_utils import data_to_screen


def bv_to_rgb(bv: float) -> tuple:
    """B-V to approximate RGB color (blue=hot, red=cool)."""
    # Simplified: bv -0.3 -> blue, 1.5 -> red
    t = max(0, min(1, (bv + 0.3) / 1.8))
    r = 0.3 + 0.7 * t
    g = 0.4 + 0.3 * t
    b = 1.0 - 0.9 * t
    return (r, g, b, 0.9)


class HRScatterRenderer(Widget):
    """Renders HR diagram with hit test."""

    def __init__(self, on_star_tap=None, **kwargs):
        super().__init__(**kwargs)
        self.on_star_tap = on_star_tap
        self.stars = load_stars()
        self.screen_positions = []
        self.highlighted_star = None
        self.bind(size=self._draw, pos=self._draw)

    def _draw(self, *args):
        self.canvas.clear()
        if self.width <= 0 or self.height <= 0:
            return

        self.screen_positions = []
        margin = 0.12

        # Achsen
        x0, y0 = self.x + self.width * margin, self.y + self.height * margin
        x1, y1 = self.x + self.width * (1 - margin), self.y + self.height * (1 - margin)
        self.canvas.add(Color(0.4, 0.45, 0.55, 0.8))
        self.canvas.add(Line(points=[x0, y0, x1, y0], width=1.5))
        self.canvas.add(Line(points=[x0, y0, x0, y1], width=1.5))

        # Sterne
        for star in self.stars:
            sx, sy = data_to_screen(
                star["bv"], star["absmag"],
                self.width, self.height,
                margin=margin,
            )
            px = self.x + sx
            py = self.y + sy
            self.screen_positions.append((star, px, py))

            r = 4 if star.get("name") else 2
            if self.highlighted_star is star:
                self.canvas.add(Color(1, 1, 0.3, 1))
                r = 8
            else:
                self.canvas.add(Color(*bv_to_rgb(star["bv"])))
            self.canvas.add(Ellipse(pos=(px - r / 2, py - r / 2), size=(r, r)))

    def find_star_at(self, x: float, y: float) -> dict:
        """Find star at (x,y), max distance 20px."""
        best = None
        best_d = 20
        for star, px, py in self.screen_positions:
            d = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
            if d < best_d:
                best_d = d
                best = star
        return best

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            star = self.find_star_at(touch.pos[0], touch.pos[1])
            if star and self.on_star_tap:
                self.on_star_tap(star)
            return True
        return super().on_touch_down(touch)
