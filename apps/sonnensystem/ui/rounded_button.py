"""RoundedButton - button with rounded corners."""

from pathlib import Path

from kivy.graphics import Color
from kivy.uix.button import Button

from ui.theme import Colors, BUTTON_RADIUS

_TRANSPARENT_BG = str(Path(__file__).parent / "transparent.png")


class RoundedButton(Button):
    """Button with rounded corners. Uses own background, Kivy button stays transparent."""

    def __init__(self, radius=None, **kwargs):
        self._radius = radius if radius is not None else BUTTON_RADIUS
        display_color = kwargs.pop("background_color", Colors.BG_BUTTON)
        kwargs["background_color"] = (0, 0, 0, 0)
        kwargs["background_normal"] = _TRANSPARENT_BG
        kwargs["background_down"] = _TRANSPARENT_BG
        super().__init__(**kwargs)
        self._display_color = list(display_color)
        with self.canvas.before:
            from kivy.graphics import RoundedRectangle
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
