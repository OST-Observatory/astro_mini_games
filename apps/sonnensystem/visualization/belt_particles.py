"""Deterministic belt pseudo-particles (asteroid / Kuiper) – flat ecliptic, no ephemerides."""

from __future__ import annotations

import math
import random
from datetime import datetime, timezone

_EPOCH = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def build_ring_particles(
    r_min_au: float,
    r_max_au: float,
    count: int,
    seed: int,
    jitter_au: float = 0.0,
) -> list[tuple[float, float]]:
    """
    Build (r_au, theta0_rad) in ecliptic plane.
    Deterministic for fixed seed.
    """
    if count <= 0 or r_max_au <= r_min_au:
        return []
    rng = random.Random(seed)
    lo = r_min_au
    hi = r_max_au
    out: list[tuple[float, float]] = []
    for _ in range(count):
        r = rng.uniform(lo, hi)
        if jitter_au > 0:
            r += rng.uniform(-jitter_au, jitter_au)
            r = max(lo * 0.98, min(hi * 1.02, r))
        theta0 = rng.uniform(0.0, 2 * math.pi)
        out.append((r, theta0))
    return out


def rotation_phase_rad(sim_date: datetime, deg_per_year: float) -> float:
    """Phase added to theta0 from simulation date (years since J2000)."""
    if deg_per_year == 0.0:
        return 0.0
    dt = sim_date
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    days = (dt - _EPOCH).total_seconds() / 86400.0
    years = days / 365.25
    return math.radians(deg_per_year * years)


def belt_phase_rad(
    sim_date: datetime,
    deg_per_year: float = 0.0,
    rad_per_day: float | None = None,
) -> float:
    """Shared belt rotation: prefer rad_per_day from YAML if set."""
    if rad_per_day is not None:
        dt = sim_date
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        days = (dt - _EPOCH).total_seconds() / 86400.0
        return rad_per_day * days
    return rotation_phase_rad(sim_date, deg_per_year)


def belt_screen_points_flat(
    particles: list[tuple[float, float]],
    phase_rad: float,
    world_to_screen,
    cx: float,
    cy: float,
) -> list[float]:
    """Flatten (sx, sy, ...) for Kivy Point."""
    pts: list[float] = []
    for r, th in particles:
        t = th + phase_rad
        x_au = r * math.cos(t)
        y_au = r * math.sin(t)
        sx, sy = world_to_screen(x_au, y_au, cx, cy)
        pts.extend([sx, sy])
    return pts


def build_spherical_shell_particles(
    r_min_au: float,
    r_max_au: float,
    count: int,
    seed: int,
) -> list[tuple[float, float]]:
    """
    Uniform sampling in a spherical shell (volume-uniform radius), projected to ecliptic x,y.
    Deterministic for fixed seed.
    """
    if count <= 0 or r_max_au <= r_min_au:
        return []
    rng = random.Random(seed)
    lo3 = r_min_au**3
    hi3 = r_max_au**3
    out: list[tuple[float, float]] = []
    for _ in range(count):
        r = (lo3 + rng.random() * (hi3 - lo3)) ** (1.0 / 3.0)
        u = rng.uniform(-1.0, 1.0)
        phi = rng.uniform(0.0, 2 * math.pi)
        st = math.sqrt(max(0.0, 1.0 - u * u))
        x = r * st * math.cos(phi)
        y = r * st * math.sin(phi)
        out.append((float(x), float(y)))
    return out


def cloud_xy_screen_points_flat(
    particles_xy: list[tuple[float, float]],
    phase_rad: float,
    world_to_screen,
    cx: float,
    cy: float,
) -> list[float]:
    """Rigid rotation of (x,y) by phase_rad, then project for Kivy Point."""
    c = math.cos(phase_rad)
    s = math.sin(phase_rad)
    pts: list[float] = []
    for x, y in particles_xy:
        xr = x * c - y * s
        yr = x * s + y * c
        sx, sy = world_to_screen(xr, yr, cx, cy)
        pts.extend([sx, sy])
    return pts
