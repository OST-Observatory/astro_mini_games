"""
Astro-Quiz theme - warm, playful, gamification.
"""

# Spacing
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16

# Radius
RADIUS_SM = 8
RADIUS_MD = 12
RADIUS_LG = 20

# Minimum touch target (px)
MIN_TOUCH_TARGET = 48


class Colors:
    """Warm, playful color palette (orange/amber)."""

    # Backgrounds
    BG_VIEW = (0.08, 0.04, 0.02, 1)
    BG_CARD = (0.15, 0.08, 0.04, 0.98)
    BG_BUTTON = (0.25, 0.15, 0.08, 1)
    BG_BUTTON_HOVER = (0.35, 0.22, 0.12, 1)
    BG_SPINNER_SELECTED = (0.32, 0.20, 0.10, 1)   # currently selected option (lighter)
    BG_SPINNER_OPTION = (0.18, 0.10, 0.05, 1)     # options available for selection (darker)

    # Akzente (Orange/Amber)
    ACCENT = (1.0, 0.6, 0.2, 1)
    ACCENT_DIM = (0.8, 0.5, 0.15, 1)

    # Feedback
    CORRECT = (0.2, 0.7, 0.3, 1)
    WRONG = (0.85, 0.25, 0.2, 1)
    NEUTRAL = (0.4, 0.35, 0.3, 1)

    # Text
    TEXT_PRIMARY = (1.0, 0.95, 0.9, 1)
    TEXT_SECONDARY = (0.85, 0.75, 0.6, 1)
    TEXT_MUTED = (0.6, 0.5, 0.4, 1)

    # Timer
    TIMER_OK = (0.3, 0.8, 0.4, 1)
    TIMER_WARNING = (1.0, 0.7, 0.2, 1)
    TIMER_DANGER = (0.9, 0.3, 0.2, 1)
