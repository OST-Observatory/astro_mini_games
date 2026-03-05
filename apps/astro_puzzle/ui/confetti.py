"""Confetti animation when puzzle is solved."""

import random

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget


CONFETTI_COLORS = [
    (1, 0.3, 0.3, 1),   # red
    (1, 0.8, 0.2, 1),   # gold
    (0.3, 0.8, 0.3, 1),  # Green
    (0.3, 0.6, 1, 1),   # blue
    (1, 0.5, 0.8, 1),   # pink
    (0.9, 0.9, 0.2, 1), # yellow
]


class ConfettiPiece(Widget):
    """A confetti piece as colored area."""

    def __init__(self, color, size=(8, 8), **kwargs):
        super().__init__(**kwargs)
        self.size = size
        self.size_hint = (None, None)
        with self.canvas.before:
            Color(*color)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class ConfettiOverlay(FloatLayout):
    """Fullscreen confetti, falls from above."""

    def __init__(self, on_done=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.on_done = on_done
        self._pieces = []
        self._anim_count = 0

    def collide_point(self, x, y):
        """Pass through touch."""
        return False

    def start(self):
        """Start the confetti animation."""
        w, h = Window.size
        center_x, center_y = w / 2, h / 2
        n = 120

        for _ in range(n):
            color = random.choice(CONFETTI_COLORS)
            pw = random.randint(4, 15)
            ph = random.randint(4, 15)
            piece = ConfettiPiece(color=color, size=(pw, ph))
            # Start: above, randomly distributed
            start_x = random.uniform(0.1 * w, 0.9 * w)
            start_y = random.uniform(h * 0.6, h + 30)
            piece.pos = (start_x - pw / 2, start_y - ph / 2)
            # Target: below, with lateral drift
            end_x = start_x + random.uniform(-w * 0.3, w * 0.3)
            end_y = random.uniform(-50, -20)
            self.add_widget(piece)
            self._pieces.append(piece)
            anim = Animation(
                x=end_x - pw / 2,
                y=end_y,
                duration=random.uniform(5.0, 10.0),
            )
            anim.bind(on_complete=self._on_piece_done)
            anim.start(piece)
            self._anim_count += 1

    def _on_piece_done(self, anim, widget):
        self._anim_count -= 1
        try:
            if widget.parent:
                self.remove_widget(widget)
        except Exception:
            pass
        if self._anim_count <= 0 and self.on_done:
            Clock.schedule_once(lambda dt: self._finish(), 0)

    def _finish(self):
        if self.parent:
            self.parent.remove_widget(self)
        if self.on_done:
            self.on_done()
