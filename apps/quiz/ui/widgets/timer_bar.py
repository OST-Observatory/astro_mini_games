"""Animated timer bar with color gradient (green → yellow → red)."""

from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget

from ui.theme import Colors, RADIUS_MD


class TimerBar(Widget):
    """Timer bar: 1.0 = full time, 0.0 = expired."""

    progress = NumericProperty(1.0)  # 1.0 = full, 0.0 = empty

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = 12
        self.bind(size=self._draw, pos=self._draw, progress=self._draw)

    def _draw(self, *args):
        self.canvas.before.clear()
        if self.width <= 0 or self.height <= 0:
            return

        # Background
        with self.canvas.before:
            Color(*Colors.BG_BUTTON)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[RADIUS_MD],
            )

            # Color choice based on progress
            p = self.progress
            if p > 0.5:
                r, g, b, a = Colors.TIMER_OK
            elif p > 0.25:
                r, g, b, a = Colors.TIMER_WARNING
            else:
                r, g, b, a = Colors.TIMER_DANGER

            Color(r, g, b, a)
            w = self.width * p
            if w > 0:
                RoundedRectangle(
                    pos=self.pos,
                    size=(w, self.height),
                    radius=[RADIUS_MD],
                )
