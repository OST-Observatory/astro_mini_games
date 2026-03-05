"""Keplerian orbits - analytical position from time."""

import math


def kepler_equation_solve(M: float, e: float, max_iter: int = 20) -> float:
    """Solve E - e*sin(E) = M for E (eccentric anomaly)."""
    E = M if e < 0.8 else math.pi
    for _ in range(max_iter):
        dE = (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
        E -= dE
        if abs(dE) < 1e-12:
            break
    return E


def position_at_time(a: float, e: float, T: float, t: float) -> tuple:
    """
    Return (x, y) position on orbital plane for time t.
    t in years, T = orbital period in years.
    """
    M = 2 * math.pi * (t % T) / T
    E = kepler_equation_solve(M, e)
    # True anomaly
    nu = 2 * math.atan2(
        math.sqrt(1 + e) * math.sin(E / 2),
        math.sqrt(1 - e) * math.cos(E / 2),
    )
    r = a * (1 - e * e) / (1 + e * math.cos(nu))
    x = r * math.cos(nu)
    y = r * math.sin(nu)
    return (x, y)
