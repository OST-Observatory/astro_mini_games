"""Real planet data: radii (km), colors."""

# Radius in km (equatorial, NASA Fact Sheets)
SUN_RADIUS_KM = 696_340
PLANET_RADII_KM = {
    "Merkur": 2_439.7,
    "Venus": 6_051.8,
    "Erde": 6_371.0,
    "Mars": 3_389.5,
    "Jupiter": 69_911,
    "Saturn": 58_232,
    "Uranus": 25_362,
    "Neptun": 24_622,
}

# Display colors (RGBA)
PLANET_COLORS = {
    "Merkur": [0.6, 0.55, 0.5, 1],
    "Venus": [0.9, 0.8, 0.5, 1],
    "Erde": [0.3, 0.5, 0.9, 1],
    "Mars": [0.9, 0.4, 0.2, 1],
    "Jupiter": [0.9, 0.7, 0.4, 1],
    "Saturn": [0.9, 0.85, 0.6, 1],
    "Uranus": [0.6, 0.9, 0.9, 1],
    "Neptun": [0.3, 0.5, 1.0, 1],
}


PLANET_ORDER = [
    "Merkur", "Venus", "Erde", "Mars", "Jupiter", "Saturn", "Uranus", "Neptun",
]

# Five IAU dwarf planets (names kept international / Latin)
DWARF_PLANET_ORDER = ["Ceres", "Pluto", "Haumea", "Makemake", "Eris"]

DWARF_PLANET_RADII_KM = {
    "Ceres": 469.4,
    "Pluto": 1188.3,
    "Haumea": 816.0,
    "Makemake": 715.0,
    "Eris": 1163.0,
}

DWARF_PLANET_COLORS = {
    "Ceres": [0.62, 0.58, 0.52, 1],
    "Pluto": [0.72, 0.68, 0.62, 1],
    "Haumea": [0.52, 0.58, 0.54, 1],
    "Makemake": [0.52, 0.45, 0.38, 1],
    "Eris": [0.58, 0.54, 0.68, 1],
}


def get_planets_with_data():
    """Returns planets with radius (km) and color."""
    return [
        {
            "name": name,
            "radius_km": PLANET_RADII_KM[name],
            "color": PLANET_COLORS[name],
        }
        for name in PLANET_ORDER
    ]


def get_dwarf_planets_with_data():
    """Radii (km) and display colors for IAU dwarf planets."""
    return [
        {
            "name": name,
            "radius_km": DWARF_PLANET_RADII_KM[name],
            "color": DWARF_PLANET_COLORS[name],
        }
        for name in DWARF_PLANET_ORDER
    ]


def body_radius_km(name: str) -> float:
    """Radius in km for a major planet or dwarf planet."""
    if name in PLANET_RADII_KM:
        return PLANET_RADII_KM[name]
    return DWARF_PLANET_RADII_KM.get(name, 6371.0)


def body_color_rgba(name: str) -> list[float]:
    """Display RGBA for major planet or dwarf planet."""
    return PLANET_COLORS.get(name) or DWARF_PLANET_COLORS.get(
        name, [1.0, 1.0, 1.0, 1.0]
    )
