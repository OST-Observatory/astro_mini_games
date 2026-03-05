"""Difficulty selection: configurable grid sizes."""

from kivy.uix.boxlayout import BoxLayout

from ui.theme import Colors, MIN_TOUCH_TARGET
from ui.rounded_button import RoundedButton


def _font():
    from shared.fonts import get_safe_font
    return get_safe_font()


class DifficultySelector(BoxLayout):
    """Buttons for grid size (e.g. 3x3, 4x4, 5x4)."""

    def __init__(self, grid_sizes=None, on_select=None, **kwargs):
        super().__init__(orientation="horizontal", spacing=16, **kwargs)
        self.on_select = on_select
        sizes = grid_sizes or [(3, 3), (4, 4)]
        for rows, cols in sizes:
            btn = RoundedButton(
                text=f"{rows}×{cols}",
                font_name=_font(),
                font_size="20sp",
                size_hint_y=None,
                height=MIN_TOUCH_TARGET,
                background_color=Colors.ACCENT,
            )
            btn.rows = rows
            btn.cols = cols
            btn.bind(on_release=self._on_choice)
            self.add_widget(btn)

    def _on_choice(self, instance):
        if self.on_select:
            self.on_select(instance.rows, instance.cols)
