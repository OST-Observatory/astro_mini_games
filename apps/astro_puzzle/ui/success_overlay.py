"""Success overlay: puzzle solved!"""

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

from ui.theme import Colors, MIN_TOUCH_TARGET
from ui.rounded_button import RoundedButton
from shared.i18n import tr


def _font():
    from shared.fonts import get_safe_font
    return get_safe_font()


class SuccessOverlay(FloatLayout):
    """Shows 'Fertig!', confetti and buttons."""

    def __init__(self, on_restart=None, on_next_image=None, on_back=None, **kwargs):
        super().__init__(**kwargs)
        self.on_restart = on_restart
        self.opacity = 0
        self.disabled = True

        self._title_lbl = Label(
            text=tr("astro_puzzle.done"),
            font_name=_font(),
            font_size="48sp",
            bold=True,
            color=Colors.ACCENT,
            size_hint=(0.5, 0.3),
            pos_hint={"center_x": 0.5, "center_y": 0.65},
        )
        self.add_widget(self._title_lbl)

        btn_h = MIN_TOUCH_TARGET + 16
        self._restart_btn = RoundedButton(
            text=tr("astro_puzzle.play_again"),
            font_name=_font(),
            font_size="24sp",
            size_hint=(None, None),
            size=(250, btn_h),
            pos_hint={"center_x": 0.5, "center_y": 0.4},
            background_color=Colors.ACCENT,
        )
        self._restart_btn.bind(on_release=lambda x: self._do_restart())
        self.add_widget(self._restart_btn)

    def apply_i18n(self):
        self._title_lbl.text = tr("astro_puzzle.done")
        self._restart_btn.text = tr("astro_puzzle.play_again")

    def collide_point(self, x, y):
        """Pass through touch when disabled (hidden)."""
        if self.disabled:
            return False
        return super().collide_point(x, y)

    def on_touch_down(self, touch):
        """When disabled, do not notify children."""
        if self.disabled:
            return False
        return super().on_touch_down(touch)

    def _do_restart(self):
        self._hide()
        if self.on_restart:
            self.on_restart()

    def _hide(self):
        self.opacity = 0
        self.disabled = True

    def hide(self):
        """Hide overlay (callable from outside)."""
        self._hide()

    def show(self, root_layout):
        """Show overlay and start confetti."""
        from ui.confetti import ConfettiOverlay
        self.opacity = 1
        self.disabled = False
        confetti = ConfettiOverlay(on_done=None)
        root_layout.add_widget(confetti)
        confetti.start()
