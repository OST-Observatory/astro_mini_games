"""RoundedButton - button with rounded corners."""

from kivy.graphics import Color, RoundedRectangle
from kivy.uix.button import Button


class RoundedButton(Button):
    """Button with rounded corners."""

    def __init__(self, radius=10, **kwargs):
        self._radius = radius
        display_color = kwargs.pop("background_color", (0.5, 0.5, 0.6, 1))
        kwargs["background_color"] = (0, 0, 0, 0)
        kwargs["background_normal"] = ""
        kwargs["background_down"] = ""
        super().__init__(**kwargs)
        self._display_color = list(display_color)
        with self.canvas.before:
            self._btn_color = Color(*display_color)
            self._btn_rect = RoundedRectangle(
                pos=self.pos, size=self.size,
                radius=[self._radius] * 4,
            )
        self.bind(pos=self._update_rect, size=self._update_rect)
        self.bind(background_color=self._on_background_color)

    def _update_rect(self, *args):
        self._btn_rect.pos = self.pos
        self._btn_rect.size = self.size

    def _on_background_color(self, inst, value):
        if value != (0, 0, 0, 0):
            self._display_color[:] = value
            self._btn_color.rgba = value
            self.background_color = (0, 0, 0, 0)
