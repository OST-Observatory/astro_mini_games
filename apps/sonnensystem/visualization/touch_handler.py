"""2-finger pinch for solar system zoom."""


class SolarTouchHandler:
    """
    Touch handler for 2D solar system: 1 finger = rotation, 2 fingers = pinch zoom.
    Camera must have .scale, .min_scale, .max_scale and .zoom(factor), .rotate(dx).
    """

    def __init__(self, camera, pinch_enabled=True):
        self.camera = camera
        self.pinch_enabled = pinch_enabled
        self._touches = {}
        self._pinch_start_dist = None
        self._pinch_start_scale = None

    def on_down(self, uid, x, y):
        """Handle touch down: track finger, start pinch if 2 fingers."""
        self._touches[uid] = (x, y)
        if len(self._touches) == 2 and self.pinch_enabled:
            self._start_pinch()

    def on_move(self, uid, x, y):
        """Handle touch move: 1 finger = rotate, 2 fingers = pinch zoom."""
        if uid not in self._touches:
            self.on_down(uid, x, y)
            return

        old_x, old_y = self._touches[uid]
        self._touches[uid] = (x, y)
        n = len(self._touches)

        if n == 1:
            dx = x - old_x
            self.camera.rotate(-dx)
        elif n >= 2 and self.pinch_enabled and self._pinch_start_dist is not None:
            self._update_pinch()

    def on_up(self, uid):
        """Handle touch up: remove finger, reset pinch if < 2 fingers."""
        if uid in self._touches:
            del self._touches[uid]
        if len(self._touches) < 2:
            self._pinch_start_dist = None
            self._pinch_start_scale = None
        elif len(self._touches) >= 2 and self.pinch_enabled:
            self._start_pinch()

    def _start_pinch(self):
        dist = self._touch_distance()
        if dist > 20:
            self._pinch_start_dist = dist
            self._pinch_start_scale = self.camera.scale

    def _update_pinch(self):
        if self._pinch_start_dist is None:
            return
        dist = self._touch_distance()
        if dist < 20:
            return
        factor = dist / self._pinch_start_dist
        new_scale = self._pinch_start_scale * factor
        new_scale = max(
            self.camera.min_scale,
            min(self.camera.max_scale, new_scale),
        )
        self.camera.scale = new_scale

    def _touch_distance(self) -> float:
        if len(self._touches) < 2:
            return 0
        pts = list(self._touches.values())
        dx = pts[1][0] - pts[0][0]
        dy = pts[1][1] - pts[0][1]
        return (dx * dx + dy * dy) ** 0.5
