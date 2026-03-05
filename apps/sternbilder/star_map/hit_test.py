"""Tap -> find nearest star / constellation."""


def find_constellation_at(stars: list, constellations: dict, stars_by_id: dict,
                          x: float, y: float, screen_coords: dict, max_dist: float = 40,
                          const_filter: list = None) -> str:
    """
    Finds the constellation closest to point (x, y).
    screen_coords: {star_id: (sx, sy)}
    const_filter: optional list of constellations, only check these
    """
    best_const = None
    best_dist = max_dist

    to_check = constellations.items()
    if const_filter:
        to_check = [(n, constellations[n]) for n in const_filter if n in constellations]

    for const_name, const_data in to_check:
        pairs = const_data.get("star_pairs", [])
        for a, b in pairs:
            sa = stars_by_id.get(a)
            sb = stars_by_id.get(b)
            if not sa or not sb:
                continue
            pa = screen_coords.get(a)
            pb = screen_coords.get(b)
            if not pa or not pb:
                continue
            # Distance from point to line a-b
            dist = _point_to_segment_dist(x, y, pa[0], pa[1], pb[0], pb[1])
            if dist < best_dist:
                best_dist = dist
                best_const = const_name

    return best_const


def _point_to_segment_dist(px, py, x1, y1, x2, y2) -> float:
    """Distance from point (px, py) to segment (x1, y1)-(x2, y2)."""
    dx = x2 - x1
    dy = y2 - y1
    len2 = dx * dx + dy * dy
    if len2 == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / len2))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return ((px - proj_x) ** 2 + (py - proj_y) ** 2) ** 0.5
