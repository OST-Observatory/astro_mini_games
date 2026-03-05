"""
Touch handler with optimized performance.
"""

import os
import time

from kivy.clock import Clock


class TouchHandler:
    """
    Multi-touch handler with smoothing, dead zone, long-press.

    Debug can be enabled via environment variable KIVY_TOUCH_DEBUG=1
    """

    def __init__(self, camera, debug=None, long_press_callback=None):
        self.camera = camera
        self.long_press_callback = long_press_callback

        # Debug-Modus
        if debug is None:
            self.debug = os.environ.get("KIVY_TOUCH_DEBUG", "0") == "1"
        else:
            self.debug = debug

        # Touch storage: {uid: (x, y) or (x, y, timestamp)}
        self._touches = {}

        # Pinch-State
        self._pinch_start_dist = None
        self._pinch_start_zoom = None

        # Smoothing
        self._smoothing_factor = 0.7
        self._smoothed_positions = {}
        self._dead_zone = 3.0

        # Long-Press
        self._long_press_duration = 0.5
        self._long_press_move_threshold = 15
        self._long_press_fired = {}
        self._long_press_start_pos = {}  # {uid: (x, y)}
        self._long_press_events = {}  # {uid: ClockEvent}

    def on_down(self, uid, x, y):
        """New touch."""
        self._touches[uid] = (x, y)
        self._long_press_fired[uid] = False
        self._long_press_start_pos[uid] = (x, y)
        ev = Clock.schedule_once(
            lambda dt, u=uid: self._check_long_press(u),
            self._long_press_duration,
        )
        self._long_press_events[uid] = ev

        if self.debug:
            print(
                f"[TOUCH] DOWN uid={uid}, pos=({x:.0f}, {y:.0f}), total={len(self._touches)}"
            )

        if len(self._touches) == 2:
            self._start_pinch()

    def on_move(self, uid, x, y):
        """Touch moves with smoothing."""
        if uid not in self._touches:
            self.on_down(uid, x, y)
            return

        # Get old position (can have 2 or 3 values)
        old_touch = self._touches[uid]
        if len(old_touch) == 3:
            old_x, old_y, _ = old_touch
        else:
            old_x, old_y = old_touch
        
        # Smoothing anwenden
        if uid in self._smoothed_positions:
            smooth_x, smooth_y = self._smoothed_positions[uid]
            smooth_x = self._smoothing_factor * smooth_x + (1 - self._smoothing_factor) * x
            smooth_y = self._smoothing_factor * smooth_y + (1 - self._smoothing_factor) * y
        else:
            smooth_x, smooth_y = x, y
        
        self._smoothed_positions[uid] = (smooth_x, smooth_y)
        # Store only (x, y) for consistency
        self._touches[uid] = (x, y)

        n = len(self._touches)

        if self.debug and n >= 2:
            print(
                f"[TOUCH] MOVE uid={uid}, total={n}, pinch_active={self._pinch_start_dist is not None}"
            )

        if n == 1:
            # Long-Press: Bei zu viel Bewegung abbrechen
            if uid in self._long_press_start_pos:
                sx, sy = self._long_press_start_pos[uid]
                if abs(smooth_x - sx) > self._long_press_move_threshold or abs(smooth_y - sy) > self._long_press_move_threshold:
                    if uid in self._long_press_events:
                        self._long_press_events[uid].cancel()
                        del self._long_press_events[uid]
                    if uid in self._long_press_start_pos:
                        del self._long_press_start_pos[uid]

            # Rotation with dead zone
            dx = smooth_x - old_x
            dy = smooth_y - old_y
            if abs(dx) < self._dead_zone and abs(dy) < self._dead_zone:
                return
            self.camera.rotate(dx, dy)

        elif n >= 2 and self._pinch_start_dist is not None:
            # Pinch-Zoom
            self._update_pinch()

    def on_up(self, uid):
        """Touch ended."""
        if uid in self._touches:
            del self._touches[uid]
        if uid in self._smoothed_positions:
            del self._smoothed_positions[uid]
        if uid in self._long_press_events:
            self._long_press_events[uid].cancel()
            del self._long_press_events[uid]
        if uid in self._long_press_start_pos:
            del self._long_press_start_pos[uid]
        if uid in self._long_press_fired:
            del self._long_press_fired[uid]

        if self.debug:
            print(f"[TOUCH] UP uid={uid}, remaining={len(self._touches)}")

        if len(self._touches) < 2:
            self._pinch_start_dist = None
            self._pinch_start_zoom = None
        elif len(self._touches) >= 2:
            self._start_pinch()

    def _start_pinch(self):
        """Initialize pinch."""
        dist = self._touch_distance()
        if dist > 20:
            self._pinch_start_dist = dist
            self._pinch_start_zoom = self.camera.distance
            if self.debug:
                print(
                    f"[TOUCH] PINCH START dist={dist:.0f}, zoom={self._pinch_start_zoom:.0f}"
                )

    def _update_pinch(self):
        """Update pinch zoom."""
        if self._pinch_start_dist is None:
            return

        dist = self._touch_distance()
        if dist < 20:
            return

        scale = self._pinch_start_dist / dist
        new_zoom = self._pinch_start_zoom * scale
        new_zoom = max(
            self.camera.min_distance, min(self.camera.max_distance, new_zoom)
        )

        if self.debug:
            print(
                f"[TOUCH] PINCH dist={dist:.0f}, scale={scale:.2f}, zoom={new_zoom:.0f}"
            )

        self.camera.distance = new_zoom

    def _touch_distance(self) -> float:
        """Distance between first two touches."""
        if len(self._touches) < 2:
            return 0

        pts = list(self._touches.values())
        dx = pts[1][0] - pts[0][0]
        dy = pts[1][1] - pts[0][1]
        return (dx * dx + dy * dy) ** 0.5

    def _check_long_press(self, uid):
        """Called after _long_press_duration."""
        if uid not in self._long_press_events:
            return
        del self._long_press_events[uid]
        if uid not in self._touches or self._long_press_fired.get(uid, False):
            return
        self._long_press_fired[uid] = True
        x, y = self._touches[uid]
        if self.long_press_callback:
            self.long_press_callback(x, y)
        if self.debug:
            print(f"[TOUCH] LONG PRESS uid={uid}, pos=({x:.0f}, {y:.0f})")

    def clear(self):
        self._touches.clear()
        self._smoothed_positions.clear()
        self._pinch_start_dist = None
        self._pinch_start_zoom = None
        for ev in list(self._long_press_events.values()):
            try:
                ev.cancel()
            except Exception:
                pass
        self._long_press_events.clear()
        self._long_press_start_pos.clear()
        self._long_press_fired.clear()
    
    def set_smoothing(self, factor: float):
        """Set smoothing factor (0.0 = no smoothing, 1.0 = full smoothing)."""
        self._smoothing_factor = max(0.0, min(1.0, factor))
    
    def set_dead_zone(self, pixels: float):
        """Set dead zone in pixels."""
        self._dead_zone = max(0.0, pixels)