"""Camera: pure top-down view of ecliptic, zoom = pixels per AU."""

import math

NEPTUNE_AU = 30  # ~30 AU for scaling


class SolarCamera:
    """
    Pure top-down view of the ecliptic plane.
    (x, y) in AU, z ignored. scale = pixels per AU.
    """

    def __init__(self, view_width: float, view_height: float):
        self.view_width = view_width
        self.view_height = view_height
        self.angle = 0.0
        self._update_scale_limits()
        self.scale = self._initial_scale
        self._initial_scale = self.scale

    def _update_scale_limits(self):
        """Scale so Neptune (30 AU) fits in 85% of view."""
        r = 0.425 * min(self.view_width, self.view_height)
        self._initial_scale = r / NEPTUNE_AU
        self.min_scale = self._initial_scale * 0.12
        self.max_scale = self._initial_scale * 10.0
        if not hasattr(self, "scale") or self.scale <= 0:
            self.scale = self._initial_scale

    def resize(self, w: float, h: float):
        """Update view size and adjust scale to keep Neptune visible."""
        if w > 0 and h > 0:
            old_initial = getattr(self, "_initial_scale", None)
            old_scale = getattr(self, "scale", None)
            self.view_width = w
            self.view_height = h
            self._update_scale_limits()
            if old_initial and old_scale and old_initial > 0:
                ratio = self._initial_scale / old_initial
                self.scale = max(self.min_scale, min(self.max_scale, old_scale * ratio))

    def world_to_screen(self, x_au: float, y_au: float, center_x: float, center_y: float) -> tuple:
        """Transform (x,y) in AU to screen. z ignored - pure top-down view."""
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        rx = x_au * cos_a - y_au * sin_a
        ry = x_au * sin_a + y_au * cos_a
        sx = center_x + rx * self.scale
        sy = center_y + ry * self.scale
        return (sx, sy)

    def rotate(self, dx_pixels: float):
        """Rotate view by pixel delta (converted to radians)."""
        self.angle += dx_pixels * 0.008

    def rotate_by_angle(self, delta_rad: float):
        """Rotate view by given angle in radians."""
        self.angle += delta_rad

    def zoom(self, factor: float):
        """Zoom in/out by factor, clamped to min/max scale."""
        self.scale *= factor
        self.scale = max(self.min_scale, min(self.max_scale, self.scale))

    def reset_view(self):
        """Reset scale and rotation to initial values."""
        self.scale = self._initial_scale
        self.angle = 0.0
