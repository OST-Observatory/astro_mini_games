"""RoundedButton - button with rounded corners."""

from kivy.graphics import Color, RoundedRectangle
from kivy.uix.button import Button

from ui.theme import RADIUS_MD


class RoundedButton(Button):
    """Button with rounded corners."""

    def __init__(self, radius=None, **kwargs):
        self._radius = radius if radius is not None else RADIUS_MD
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

    def set_display_color(self, color):
        """Set background color directly (e.g. for active/inactive state)."""
        self._display_color[:] = list(color)
        self._btn_color.rgba = color
