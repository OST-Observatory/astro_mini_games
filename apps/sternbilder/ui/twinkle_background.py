"""Subtle twinkling star field behind menu screens (under the star map)."""

import math
import random

from kivy.clock import Clock
from kivy.graphics import Color, Ellipse
from kivy.uix.widget import Widget


class TwinkleStarsBackground(Widget):
    """Fullscreen layer; touches pass through. Visible when star map opacity is 0."""

    def __init__(self, star_count: int = 130, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self._star_count = star_count
        self._stars = []  # list of dicts with color, ellipse, phase, speed, amp, base
        self._clock_ev = None
        self._t0 = 0.0
        self.bind(size=self._redraw_field, pos=self._redraw_field)

    def collide_point(self, x, y):
        return False

    def _cancel_clock(self):
        if self._clock_ev is not None:
            self._clock_ev.cancel()
            self._clock_ev = None

    def on_parent(self, widget, parent):
        if parent is None:
            self._cancel_clock()
        else:
            self._ensure_clock()

    def _ensure_clock(self):
        if self._clock_ev is None and self.parent is not None:
            self._t0 = Clock.get_boottime()
            self._clock_ev = Clock.schedule_interval(self._tick, 1.0 / 20.0)

    def _redraw_field(self, *args):
        self._cancel_clock()
        self.canvas.clear()
        self._stars.clear()
        w, h = self.width, self.height
        if w <= 1 or h <= 1:
            return
        random.seed(42)
        for _ in range(self._star_count):
            nx = random.uniform(0.02, 0.98)
            ny = random.uniform(0.02, 0.98)
            r = random.uniform(1.0, 3.6)
            phase = random.uniform(0, math.tau)
            speed = random.uniform(0.8, 2.6)
            amp = random.uniform(0.22, 0.52)
            base = random.uniform(0.38, 0.78)
            br = random.uniform(0.88, 1.0)
            bg = random.uniform(0.9, 1.0)
            bb = random.uniform(0.96, 1.0)
            px = self.x + nx * w - r
            py = self.y + ny * h - r
            sz = r * 2
            with self.canvas:
                col = Color(br, bg, bb, base)
                el = Ellipse(pos=(px, py), size=(sz, sz))
            self._stars.append(
                {
                    "color": col,
                    "ellipse": el,
                    "phase": phase,
                    "speed": speed,
                    "amp": amp,
                    "base": base,
                    "nx": nx,
                    "ny": ny,
                    "r": r,
                    "br": br,
                    "bg": bg,
                    "bb": bb,
                }
            )
        random.seed()
        self._ensure_clock()

    def _tick(self, dt):
        if not self._stars or self.width <= 1:
            return
        t = Clock.get_boottime() - self._t0
        w, h = self.width, self.height
        for s in self._stars:
            a = s["base"] + s["amp"] * math.sin(s["phase"] + t * s["speed"])
            a = max(0.22, min(0.98, a))
            s["color"].rgba = [s["br"], s["bg"], s["bb"], a]
            r = s["r"]
            px = self.x + s["nx"] * w - r
            py = self.y + s["ny"] * h - r
            s["ellipse"].pos = (px, py)

    def on_stop_app(self):
        """Call from App.on_stop to cancel the clock."""
        self._cancel_clock()
