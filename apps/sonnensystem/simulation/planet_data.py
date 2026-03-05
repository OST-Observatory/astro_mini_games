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
