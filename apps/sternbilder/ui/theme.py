"""
Star constellation theme
"""

from kivy.metrics import dp

SPACING_SM = 8
SPACING_MD = 12
RADIUS_MD = 12
MIN_TOUCH_TARGET = 48

# Fullscreen menu screens: start, quiz_intro, quiz_end (learn / in-quiz unchanged)
MENU_HEADING_START_SP = "42sp"
MENU_HEADING_QUIZ_INTRO_SP = "42sp"
MENU_PRIMARY_FONT_SP = "27sp"
MENU_SECONDARY_FONT_SP = "14sp"
MENU_RESULT_BODY_SP = "23sp"
MENU_PRIMARY_BTN_HEIGHT = int(dp(72))
MENU_SECONDARY_BTN_HEIGHT = max(int(dp(48)), MIN_TOUCH_TARGET)
# size_hint_x for RoundedButton on menu screens (narrower = less dominant)
MENU_PRIMARY_BTN_WIDTH = 0.25
MENU_SECONDARY_BTN_WIDTH = 0.15
MENU_QUIZ_INTRO_PRIMARY_WIDTH = 0.25
MENU_VIGNETTE_EDGE_ALPHA = 0.2
MENU_VIGNETTE_EDGE_FRACTION = 0.1
# Semi-transparent panel behind intro scroll text (start + quiz_intro)
MENU_INTRO_BOX_BG = (0.06, 0.06, 0.14, 0.55)
MENU_INTRO_BOX_PADDING = int(dp(14))
# Max fraction of window height for intro text area before scrolling
MENU_INTRO_MAX_HEIGHT_FRACTION = 0.46


class Colors:
    """Dark star sky, subtle lines"""

    BG_VIEW = (0.02, 0.02, 0.06, 1)
    BG_PANEL = (0.06, 0.06, 0.12, 0.95)
    BG_BUTTON = (0.12, 0.12, 0.2, 1)

    ACCENT = (0.5, 0.65, 1.0, 1)
    ACCENT_2 = (0.9, 0.75, 0.3, 1)
    TEXT_PRIMARY = (0.95, 0.95, 1.0, 1)
    TEXT_SECONDARY = (0.65, 0.7, 0.85, 1)
    CORRECT = (0.3, 0.8, 0.4, 1)
    WRONG = (0.9, 0.3, 0.25, 1)
