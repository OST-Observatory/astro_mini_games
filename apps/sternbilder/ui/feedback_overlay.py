"""Feedback overlay: correct/wrong with animation."""

from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label

from ui.theme import Colors


def _font():
    from shared.fonts import get_safe_font
    return get_safe_font()


class FeedbackOverlay(FloatLayout):
    """Shows brief feedback like 'Richtig: Orion' or 'Falsch'."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.opacity = 0
        self.label = Label(
            text="",
            font_name=_font(),
            font_size="28sp",
            bold=True,
            halign="center",
            valign="middle",
            size_hint=(0.6, 0.2),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self.add_widget(self.label)

    def show_correct(self, name: str):
        """Show correct answer feedback with constellation name."""
        self.label.text = f"Richtig!\n{name}"
        self.label.color = Colors.CORRECT
        self._animate()

    def show_wrong(self, name: str = ""):
        """Show wrong answer feedback, optionally with expected name."""
        self.label.text = f"Falsch{f': {name}' if name else ''}"
        self.label.color = Colors.WRONG
        self._animate()

    def _animate(self):
        self.opacity = 1
        anim = Animation(opacity=0, duration=1.5)
        anim.bind(on_complete=self._on_hidden)
        anim.start(self)

    def _on_hidden(self, *args):
        if self.parent:
            self.parent.remove_widget(self)
