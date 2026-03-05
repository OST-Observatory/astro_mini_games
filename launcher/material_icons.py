"""
Material Design Icons (Google) - codepoint mapping for launcher tiles.
Font: fonts/MaterialIcons-Regular.ttf
"""

from pathlib import Path

# Path to Material Icons font
FONT_PATH = str(Path(__file__).resolve().parent.parent / "fonts" / "MaterialIcons-Regular.ttf")

# Selected icons for our apps (name -> Unicode codepoint)
# See: https://fonts.google.com/icons
ICONS = {
    "public": "\ue80b",           # Globe/Earth – solar system
    "quiz": "\uf04c",            # Quiz – astro quiz
    "nights_stay": "\uea46",     # Moon + stars – moon phases
    "stars": "\ue8d0",           # Stars – constellations
    "hub": "\ue9f4",             # Network hub – galaxy collision
    "satellite_alt": "\ueb3a",   # Satellite – StarLink tracker
    "scatter_plot": "\ue268",    # Scatter plot – HR diagram
    "travel_explore": "\ue2db",  # Explore – exoplanet
    "extension": "\ue87b",       # Puzzle pieces – astro puzzle
    "orbit": "\ue028",           # N-body/orbit simulation
}


def resolve_icon(icon_config: str) -> tuple[str, str | None]:
    """
    Converts config value (e.g. "md:public" or "O") to (character, font path).
    Returns: (text, font_name) - font_name is None for normal font.
    """
    if not icon_config or not isinstance(icon_config, str):
        return ("*", None)

    icon = icon_config.strip()
    if icon.startswith("md:"):
        name = icon[3:].strip().lower()
        char = ICONS.get(name)
        if char:
            return (char, FONT_PATH)
        return (ICONS.get("stars", "*"), FONT_PATH)

    return (icon, None)
