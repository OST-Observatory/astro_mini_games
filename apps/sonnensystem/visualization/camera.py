"""Camera: pure top-down view of ecliptic, zoom = pixels per AU."""

import math

NEPTUNE_AU = 30  # ~30 AU for scaling


class SolarCamera:
    """
    Pure top-down view of the ecliptic plane.
    (x, y) in AU, z ignored. scale = pixels per AU.

    When ``outer_view_au`` is set, ``min_scale`` is capped so that at maximum
    zoom-out the viewport half-extent in AU is at least ``outer_view_au`` ×
    ``outer_view_margin`` (fits Kuiper ~50 AU + pad; hook for Oort later).
    Uses half the smaller window dimension as visible radius (conservative).
    """

    def __init__(
        self,
        view_width: float,
        view_height: float,
        reference_au: float = NEPTUNE_AU,
        min_zoom_factor: float = 0.12,
        outer_view_au: float | None = None,
        outer_view_margin: float = 1.05,
    ):
        self.view_width = view_width
        self.view_height = view_height
        self.angle = 0.0
        self.reference_au = max(float(reference_au), 1e-6)
        self._min_zoom_factor = float(min_zoom_factor)
        self.outer_view_au = outer_view_au
        self.outer_view_margin = max(outer_view_margin, 1.0)
        self._update_scale_limits()
        self.scale = self._initial_scale

    def _update_scale_limits(self):
        """Initial scale so ``reference_au`` fits in ~85% of the smaller view dimension."""
        r = 0.425 * min(self.view_width, self.view_height)
        self._initial_scale = r / self.reference_au
        legacy_min = self._initial_scale * self._min_zoom_factor
        self.min_scale = legacy_min
        if self.outer_view_au and self.outer_view_au > 0:
            half_dim = 0.5 * min(self.view_width, self.view_height)
            cap = half_dim / (self.outer_view_au * self.outer_view_margin)
            self.min_scale = min(self.min_scale, cap)
        self.max_scale = self._initial_scale * 10.0
        if not hasattr(self, "scale") or self.scale <= 0:
            self.scale = self._initial_scale

    def apply_profile(
        self,
        reference_au: float,
        outer_view_au: float | None = None,
        outer_view_margin: float = 1.05,
        min_zoom_factor: float = 0.12,
        preserve_zoom_ratio: bool = True,
    ):
        """
        Switch scale baseline (e.g. inner system vs Oort schematic view).
        If preserve_zoom_ratio, keeps scale / initial_scale similar across profile change.
        """
        old_initial = getattr(self, "_initial_scale", None)
        old_scale = getattr(self, "scale", None)
        zr = (
            old_scale / old_initial
            if (
                preserve_zoom_ratio
                and old_initial
                and old_initial > 0
                and old_scale
                and old_scale > 0
            )
            else None
        )
        self.reference_au = max(float(reference_au), 1e-6)
        self._min_zoom_factor = float(min_zoom_factor)
        self.outer_view_au = outer_view_au
        self.outer_view_margin = max(float(outer_view_margin), 1.0)
        self._update_scale_limits()
        if zr is not None:
            self.scale = max(
                self.min_scale,
                min(self.max_scale, self._initial_scale * zr),
            )
        else:
            self.scale = self._initial_scale

    def resize(self, w: float, h: float):
        """Update view size and adjust scale to match reference."""
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

    def screen_to_world_au(
        self, sx: float, sy: float, center_x: float, center_y: float
    ) -> tuple[float, float]:
        """Inverse of ``world_to_screen``: screen px → heliocentric ecliptic (AU)."""
        if self.scale <= 0:
            return (0.0, 0.0)
        rx = (sx - center_x) / self.scale
        ry = (sy - center_y) / self.scale
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        x_au = rx * cos_a + ry * sin_a
        y_au = -rx * sin_a + ry * cos_a
        return (float(x_au), float(y_au))

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
