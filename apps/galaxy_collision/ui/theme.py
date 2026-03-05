"""
UI theme - colors, spacing, breakpoints.
"""

# Breakpoint for layout detection (width in px)
# < breakpoint = touch/drawer mode, >= = desktop mode
BREAKPOINT_WIDTH = 768

# Minimum touch targets (px)
MIN_TOUCH_TARGET = 48
SLIDER_CURSOR_SIZE = (48, 48)  # Larger for touch displays (drag easier to grip)
SLIDER_PADDING = 20

# Spacing
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16

# Radius
RADIUS_SM = 8
RADIUS_MD = 12
RADIUS_LG = 16

# Drawer
DRAWER_WIDTH = 320
DRAWER_OVERLAY_ALPHA = 0.4
SWIPE_THRESHOLD = 50

# Colors – dark theme with cyan accent
class Colors:
    # Backgrounds
    BG_VIEW = (0.01, 0.01, 0.03, 1)
    BG_PANEL = (0.06, 0.06, 0.10, 0.98)
    BG_BUTTON = (0.12, 0.14, 0.18, 1)
    BG_BUTTON_HOVER = (0.18, 0.20, 0.25, 1)
    BG_OVERLAY = (0, 0, 0, 0.4)

    # Akzent
    ACCENT = (0.2, 0.65, 0.9, 1)
    ACCENT_DIM = (0.15, 0.45, 0.65, 1)

    # Aktionen
    PLAY = (0.15, 0.65, 0.25, 1)
    PAUSE = (0.55, 0.45, 0.12, 1)
    RESET = (0.55, 0.28, 0.18, 1)
    DANGER = (0.55, 0.18, 0.18, 1)
    NEUTRAL = (0.25, 0.27, 0.32, 1)

    # Text
    TEXT_PRIMARY = (0.95, 0.95, 0.97, 1)
    TEXT_SECONDARY = (0.6, 0.62, 0.68, 1)
    TEXT_MUTED = (0.42, 0.44, 0.48, 1)
    VALUE = (0.35, 0.75, 0.95, 1)

    # Slider
    SLIDER_TRACK = (0.25, 0.6, 0.95, 0.9)
    SLIDER_CURSOR = (0.3, 0.65, 0.95, 1)


def is_touch_layout(width: float, layout_mode: str, breakpoint: int = None) -> bool:
    """Return True if touch/drawer layout should be used."""
    if layout_mode == "touch":
        return True
    if layout_mode == "desktop":
        return False
    # auto: based on width
    bp = breakpoint if breakpoint is not None else BREAKPOINT_WIDTH
    return width < bp
