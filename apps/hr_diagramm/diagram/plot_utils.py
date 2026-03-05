"""Coordinate transformation for HR diagram."""


def data_to_screen(bv: float, absmag: float, width: float, height: float,
                   bv_min: float = -0.5, bv_max: float = 2.0,
                   mag_min: float = -7, mag_max: float = 16,
                   margin: float = 0.1) -> tuple:
    """
    (bv, absmag) -> (x, y) in pixels.
    X: bv (left=hot, right=cool)
    Y: absmag (bottom=bright, top=dim - inverted for diagram)
    """
    usable_w = width * (1 - 2 * margin)
    usable_h = height * (1 - 2 * margin)
    ox = width * margin
    oy = height * margin

    x = ox + (bv - bv_min) / (bv_max - bv_min) * usable_w
    # absmag: smaller = brighter; we want bright at top
    y = oy + (mag_max - absmag) / (mag_max - mag_min) * usable_h
    return (x, y)
