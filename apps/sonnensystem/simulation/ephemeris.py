"""Planet positions via Skyfield (real ephemerides)"""

import math
from datetime import datetime, timezone

from simulation.planet_data import DWARF_PLANET_ORDER

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

# Pluto: DE421 + Kepler fallback; other dwarfs Kepler-only (not in DE421).

# Semi-major axis (AU), eccentricity, longitude of perihelion ϖ = Ω + ω (rad, mod 2π).
DWARF_ORBITAL_ELEMENTS = {
    "Ceres": (2.7675, 0.075823, math.radians((80.347 + 73.638) % 360)),
    "Pluto": (39.482, 0.24883, math.radians((110.287 + 113.763) % 360)),
    "Haumea": (43.218, 0.19126, math.radians((121.862 + 239.041) % 360)),
    "Makemake": (45.791, 0.15976, math.radians((307.482 + 297.454) % 360)),
    "Eris": (67.781, 0.43607, math.radians((35.952 + 151.639) % 360)),
    # Sedna (90377): schematic Kepler ellipse on ecliptic (~mean a, high e)
    "Sedna": (
        552.0,
        0.8545,
        math.radians((144.246 + 358.303) % 360),
    ),
}

DWARF_ORBITAL_PERIODS_YEARS = {
    "Ceres": 4.603,
    "Pluto": 248.09,
    "Haumea": 284.0,
    "Makemake": 306.2,
    "Eris": 558.07,
    "Sedna": 248.0 * ((552.0 / 39.482) ** 1.5),
}

# Mean anomaly at J2000 for Kepler propagation (Pluto filled from Skyfield).
DWARF_M0_RAD_J2000 = {
    "Ceres": math.radians(-43.6266),
    "Eris": math.radians(191.7357),
    "Haumea": math.radians(181.4242),
    "Makemake": math.radians(128.4508),
    "Sedna": math.radians(356.794),
}

DWARF_PLANET_SKYFIELD = [
    ("pluto barycenter", "Pluto"),
]


def _load():
    global _eph, _ts
    if _eph is None:
        from skyfield.api import load

        _ts = load.timescale()
        _eph = load("de421.bsp")
    return _eph, _ts


def _elements_and_period(name: str) -> tuple[tuple[float, float, float], float]:
    """Orbital elements (a, e, peri_rad) and period (years) for planet or dwarf."""
    if name in ORBITAL_ELEMENTS:
        return ORBITAL_ELEMENTS[name], ORBITAL_PERIODS_YEARS[name]
    if name in DWARF_ORBITAL_ELEMENTS:
        return DWARF_ORBITAL_ELEMENTS[name], DWARF_ORBITAL_PERIODS_YEARS[name]
    return (1.0, 0.0, 0.0), 1.0


def _ensure_m0_cache():
    """Compute M0 for all planets from Skyfield at J2000 (once)."""
    if _M0_CACHE:
        return
    eph, ts = _load()
    sun = eph["sun"]
    t_j2000 = ts.from_datetime(_J2000)
    for eph_key, name in PLANET_IDS:
        elem, _ = _elements_and_period(name)
        a, e = elem[0], elem[1]
        body = eph[eph_key]
        pos = (body - sun).at(t_j2000)
        x, y, _ = pos.ecliptic_xyz(epoch="date").au
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

    # Dwarf planets: Pluto matches Skyfield + ellipse model; others use fixed M0 @ J2000.
    for eph_key, name in DWARF_PLANET_SKYFIELD:
        elem, _ = _elements_and_period(name)
        a, e = elem[0], elem[1]
        body = eph[eph_key]
        pos = (body - sun).at(t_j2000)
        x, y, _ = pos.ecliptic_xyz(epoch="date").au
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

    for name in DWARF_PLANET_ORDER:
        if name in _M0_CACHE:
            continue
        _M0_CACHE[name] = DWARF_M0_RAD_J2000[name]


def _position_kepler(name: str, t_years: float) -> tuple:
    """Kepler position (x, y, z) in AU for a planet. t_years = years since J2000.
    Coordinates in ecliptic - same rotation as orbital ellipses."""
    from simulation.integrator import kepler_equation_solve

    _ensure_m0_cache()
    elem, T = _elements_and_period(name)
    a, e = elem[0], elem[1]
    peri = elem[2] if len(elem) > 2 else 0.0
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
    for name in DWARF_PLANET_ORDER:
        x, y, z = _position_kepler(name, t_years)
        result.append((name, x, y, z))
    return result


def get_positions_at(dt: datetime = None):
    """
    Return heliocentric ecliptic (x,y,z) in AU for major planets and dwarf planets.
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

    t_years = _years_since_j2000(dt)
    for eph_key, name in DWARF_PLANET_SKYFIELD:
        body = eph[eph_key]
        pos = (body - sun).at(t)
        x, y, z = pos.ecliptic_xyz(epoch="date").au
        result.append((name, float(x), float(y), float(z)))

    kepler_dwarfs = [n for n in DWARF_PLANET_ORDER if n != "Pluto"]
    for name in kepler_dwarfs:
        x, y, z = _position_kepler(name, t_years)
        result.append((name, float(x), float(y), float(z)))
    return result


def _orbit_ellipse_points(name: str, num_points: int) -> list:
    """Closed Kepler ellipse for all planets, oriented in ecliptic."""
    elem, _ = _elements_and_period(name)
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
