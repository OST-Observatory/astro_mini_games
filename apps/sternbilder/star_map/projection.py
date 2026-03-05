"""RA/Dec -> 2D projection (stereographic)."""

import math


def ra_dec_to_xy(ra_deg: float, dec_deg: float, center_ra: float = 0, center_dec: float = 0) -> tuple:
    """
    Stereographic projection: (ra, dec) -> (x, y) normalized -1..1
    """
    ra_rad = math.radians(ra_deg - center_ra)
    dec_rad = math.radians(dec_deg)
    cen_dec_rad = math.radians(center_dec)

    # Stereographic
    cos_dec = math.cos(dec_rad)
    sin_dec = math.sin(dec_rad)
    cos_cen = math.cos(cen_dec_rad)
    sin_cen = math.sin(cen_dec_rad)

    k = 2 / (1 + sin_cen * sin_dec + cos_cen * cos_dec * math.cos(ra_rad))
    # RA increases to the left in standard view (from outside) -> negate x
    x = -k * cos_dec * math.sin(ra_rad)
    y = k * (cos_cen * sin_dec - sin_cen * cos_dec * math.cos(ra_rad))
    return (x, y)


def fit_projected_to_screen(
    points: list[tuple[float, float]],
    width: float,
    height: float,
    margin: float = 0.08,
) -> tuple[float, float, float]:
    """
    Find scale and offset so all points fit in the window.
    Returns (scale, offset_x, offset_y) for sx = offset_x + x * scale, sy = offset_y + y * scale
    """
    if not points:
        return (min(width, height) / 4, width / 2, height / 2)

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    range_x = x_max - x_min
    range_y = y_max - y_min

    usable_w = width * (1 - 2 * margin)
    usable_h = height * (1 - 2 * margin)

    if range_x < 1e-6:
        range_x = 1.0
    if range_y < 1e-6:
        range_y = 1.0

    scale = min(usable_w / range_x, usable_h / range_y)
    center_x = (x_min + x_max) / 2
    center_y = (y_min + y_max) / 2
    offset_x = width / 2 - center_x * scale
    offset_y = height / 2 - center_y * scale

    return (scale, offset_x, offset_y)
