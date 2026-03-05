"""Planet positions via Skyfield (real ephemerides)"""

import math
from datetime import datetime, timezone

_eph = None
_ts = None

# de421.bsp deckt 1899-07-29 bis 2053-10-09
_EPH_START = datetime(1899, 7, 29, tzinfo=timezone.utc)
_EPH_END = datetime(2053, 10, 9, tzinfo=timezone.utc)
_J2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

# Orbital elements (a in AU, e, longitude of perihelion ϖ in rad)
# ϖ = ω + Ω for orientation of ellipse in ecliptic (J2000)
ORBITAL_ELEMENTS = {
    "Merkur": (0.387, 0.206, math.radians(77.46)),
    "Venus": (0.723, 0.007, math.radians(130.16)),
    "Erde": (1.0, 0.017, math.radians(102.9)),
    "Mars": (1.52, 0.093, math.radians(334.22)),
    "Jupiter": (5.20, 0.048, math.radians(14.75)),
    "Saturn": (9.54, 0.056, math.radians(92.5)),
    "Uranus": (19.19, 0.046, math.radians(170.96)),
    "Neptun": (30.07, 0.009, math.radians(44.97)),
}

# Mean anomaly M0 at J2000 (computed from Skyfield on first Kepler call)
_M0_CACHE = {}

# Ephemeris keys and German names
PLANET_IDS = [
    ("mercury", "Merkur"),
    ("venus", "Venus"),
    ("earth", "Erde"),
    ("mars", "Mars"),
    ("jupiter barycenter", "Jupiter"),
    ("saturn barycenter", "Saturn"),
    ("uranus barycenter", "Uranus"),
    ("neptune barycenter", "Neptun"),
]

ORBITAL_PERIODS_YEARS = {
    "Merkur": 0.241,
    "Venus": 0.615,
    "Erde": 1.0,
    "Mars": 1.88,
    "Jupiter": 11.86,
    "Saturn": 29.46,
    "Uranus": 84.01,
    "Neptun": 164.8,
}


def _load():
    global _eph, _ts
    if _eph is None:
        from skyfield.api import load

        _ts = load.timescale()
        _eph = load("de421.bsp")
    return _eph, _ts


def _ensure_m0_cache():
    """Compute M0 for all planets from Skyfield at J2000 (once)."""
    if _M0_CACHE:
        return
    eph, ts = _load()
    sun = eph["sun"]
    t_j2000 = ts.from_datetime(_J2000)
    for eph_key, name in PLANET_IDS:
        elem = ORBITAL_ELEMENTS.get(name, (1.0, 0.0, 0.0))
        a, e = elem[0], elem[1]
        T = ORBITAL_PERIODS_YEARS.get(name, 1.0)
        body = eph[eph_key]
        pos = (body - sun).at(t_j2000)
        x, y, _ = pos.ecliptic_xyz(epoch="date").au
        r = math.sqrt(x * x + y * y)
        nu = math.atan2(y, x)
        if abs(e) < 1e-10:
            E = nu
        else:
            E = 2 * math.atan2(
                math.tan(nu / 2) * math.sqrt(1 - e),
                math.sqrt(1 + e),
            )
        M = E - e * math.sin(E)
        _M0_CACHE[name] = M


def _position_kepler(name: str, t_years: float) -> tuple:
    """Kepler position (x, y, z) in AU for a planet. t_years = years since J2000.
    Coordinates in ecliptic - same rotation as orbital ellipses."""
    from simulation.integrator import kepler_equation_solve

    _ensure_m0_cache()
    elem = ORBITAL_ELEMENTS.get(name, (1.0, 0.0, 0.0))
    a, e = elem[0], elem[1]
    peri = elem[2] if len(elem) > 2 else 0.0
    T = ORBITAL_PERIODS_YEARS.get(name, 1.0)
    M0 = _M0_CACHE.get(name, 0.0)
    M = M0 + 2 * math.pi * (t_years / T)
    M = M % (2 * math.pi)
    E = kepler_equation_solve(M, e)
    nu = 2 * math.atan2(
        math.sqrt(1 + e) * math.sin(E / 2),
        math.sqrt(1 - e) * math.cos(E / 2),
    )
    r = a * (1 - e * e) / (1 + e * math.cos(nu))
    x = r * math.cos(nu)
    y = r * math.sin(nu)
    cos_p, sin_p = math.cos(peri), math.sin(peri)
    x_rot = x * cos_p - y * sin_p
    y_rot = x * sin_p + y * cos_p
    return (float(x_rot), float(y_rot), 0.0)


def _years_since_j2000(dt: datetime) -> float:
    return (dt - _J2000).total_seconds() / (365.25 * 86400)


def get_positions_kepler(dt: datetime):
    """Return positions of all planets via Kepler (for outside ephemeris range)."""
    t_years = _years_since_j2000(dt)
    result = []
    for _, name in PLANET_IDS:
        x, y, z = _position_kepler(name, t_years)
        result.append((name, x, y, z))
    return result


def get_positions_at(dt: datetime = None):
    """
    Return heliocentric ecliptic (x,y,z) in AU for all planets.
    dt: datetime (UTC), or None for current system time.
    In ephemeris range (1899-2053): Skyfield.
    Outside: Kepler fallback.
    Returns: list of (name, x_au, y_au, z_au)
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    if dt < _EPH_START or dt > _EPH_END:
        return get_positions_kepler(dt)

    eph, ts = _load()
    t = ts.from_datetime(dt)
    sun = eph["sun"]

    result = []
    for eph_key, name in PLANET_IDS:
        body = eph[eph_key]
        pos = (body - sun).at(t)
        x, y, z = pos.ecliptic_xyz(epoch="date").au
        result.append((name, float(x), float(y), float(z)))
    return result


def _orbit_ellipse_points(name: str, num_points: int) -> list:
    """Closed Kepler ellipse for all planets, oriented in ecliptic."""
    elem = ORBITAL_ELEMENTS.get(name, (1.0, 0.0, 0.0))
    a, e = elem[0], elem[1]
    peri = elem[2] if len(elem) > 2 else 0.0
    cos_p, sin_p = math.cos(peri), math.sin(peri)
    points = []
    for i in range(num_points):
        frac = i / max(1, num_points - 1) if num_points > 1 else 1.0
        nu = 2 * math.pi * frac
        r = a * (1 - e * e) / (1 + e * math.cos(nu))
        x = r * math.cos(nu)
        y = r * math.sin(nu)
        x_rot = x * cos_p - y * sin_p
        y_rot = x * sin_p + y * cos_p
        points.append((float(x_rot), float(y_rot), 0.0))
    return points


def get_orbit_samples(name: str, dt: datetime, num_points: int = 128):
    """
    Return points along the orbit as Kepler ellipse.
    All planets: fixed, closed ellipses - independent of ephemeris range.
    Returns: list of (x_au, y_au, z_au)
    """
    return _orbit_ellipse_points(name, num_points)
