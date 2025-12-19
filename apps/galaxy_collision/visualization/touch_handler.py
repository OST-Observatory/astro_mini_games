"""
Touch-Handler mit Debug-Ausgaben
"""


class TouchHandler:
    """
    Multi-Touch Handler

    WICHTIG: Aktiviere debug=True um Touch-Events zu sehen!
    """

    def __init__(self, camera):
        self.camera = camera
        self.debug = True  # AKTIVIERT für Debugging

        # Touch-Speicher: {uid: (x, y)}
        self._touches = {}

        # Pinch-State
        self._pinch_start_dist = None
        self._pinch_start_zoom = None

    def on_down(self, uid, x, y):
        """Neuer Touch"""
        self._touches[uid] = (x, y)

        if self.debug:
            print(
                f"[TOUCH] DOWN uid={uid}, pos=({x:.0f}, {y:.0f}), total={len(self._touches)}"
            )

        if len(self._touches) == 2:
            self._start_pinch()

    def on_move(self, uid, x, y):
        """Touch bewegt"""
        if uid not in self._touches:
            self.on_down(uid, x, y)
            return

        old_x, old_y = self._touches[uid]
        self._touches[uid] = (x, y)

        n = len(self._touches)

        if self.debug and n >= 2:
            print(
                f"[TOUCH] MOVE uid={uid}, total={n}, pinch_active={self._pinch_start_dist is not None}"
            )

        if n == 1:
            # Rotation
            dx = x - old_x
            dy = y - old_y
            self.camera.rotate(dx, dy)

        elif n >= 2 and self._pinch_start_dist is not None:
            # Pinch-Zoom
            self._update_pinch()

    def on_up(self, uid):
        """Touch beendet"""
        if uid in self._touches:
            del self._touches[uid]

        if self.debug:
            print(f"[TOUCH] UP uid={uid}, remaining={len(self._touches)}")

        if len(self._touches) < 2:
            self._pinch_start_dist = None
            self._pinch_start_zoom = None
        elif len(self._touches) >= 2:
            self._start_pinch()

    def _start_pinch(self):
        """Initialisiert Pinch"""
        dist = self._touch_distance()
        if dist > 20:
            self._pinch_start_dist = dist
            self._pinch_start_zoom = self.camera.distance
            if self.debug:
                print(
                    f"[TOUCH] PINCH START dist={dist:.0f}, zoom={self._pinch_start_zoom:.0f}"
                )

    def _update_pinch(self):
        """Aktualisiert Pinch-Zoom"""
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
        """Abstand zwischen ersten zwei Touches"""
        if len(self._touches) < 2:
            return 0

        pts = list(self._touches.values())
        dx = pts[1][0] - pts[0][0]
        dy = pts[1][1] - pts[0][1]
        return (dx * dx + dy * dy) ** 0.5

    def clear(self):
        self._touches.clear()
        self._pinch_start_dist = None
        self._pinch_start_zoom = None
