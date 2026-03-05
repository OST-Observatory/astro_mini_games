"""
Symbol definitions with Unicode characters
"""

from ui.fonts import is_unicode_available


class Symbols:
    """
    Symbol collection for the UI.
    """

    def __init__(self, use_unicode: bool = True):
        self._use_unicode = use_unicode

    @property
    def _unicode(self) -> bool:
        """Dynamically checks whether Unicode should be used."""
        return self._use_unicode and is_unicode_available()

    # === PLAYBACK ===
    @property
    def PLAY(self):
        return "▶" if self._unicode else ">"

    @property
    def PAUSE(self):
        return "⏸" if self._unicode else "||"

    @property
    def STOP(self):
        return "■" if self._unicode else "[#]"

    @property
    def RESET(self):
        return "↺" if self._unicode else "<<"

    # === ZOOM ===
    @property
    def ZOOM_IN(self):
        return "⊕" if self._unicode else "[+]"

    @property
    def ZOOM_OUT(self):
        return "⊖" if self._unicode else "[-]"

    @property
    def PLUS(self):
        return "+" if self._unicode else "+"

    @property
    def MINUS(self):
        return "−" if self._unicode else "-"

    # === UI ===
    @property
    def SETTINGS(self):
        return "⚙" if self._unicode else "*"

    @property
    def CLOSE(self):
        return "✕" if self._unicode else "X"

    @property
    def CHECK(self):
        return "✓" if self._unicode else "v"

    @property
    def CROSS(self):
        return "✗" if self._unicode else "x"

    @property
    def INFO(self):
        return "ℹ" if self._unicode else "i"

    @property
    def WARNING(self):
        return "⚠" if self._unicode else "!"

    @property
    def BULLET(self):
        return "•" if self._unicode else "*"

    # === ASTRONOMIE ===
    @property
    def STAR(self):
        return "★" if self._unicode else "*"

    @property
    def GALAXY(self):
        return "◎" if self._unicode else "@"

    @property
    def SUN(self):
        return "☀" if self._unicode else "O"

    @property
    def CIRCLE(self):
        return "●" if self._unicode else "o"

    # === PFEILE ===
    @property
    def ARROW_UP(self):
        return "↑" if self._unicode else "^"

    @property
    def ARROW_DOWN(self):
        return "↓" if self._unicode else "v"

    @property
    def ARROW_LEFT(self):
        return "←" if self._unicode else "<"

    @property
    def ARROW_RIGHT(self):
        return "→" if self._unicode else ">"

    # === SONSTIGES ===
    @property
    def TIME(self):
        return "⏱" if self._unicode else "t"

    @property
    def SPEED(self):
        return "⚡" if self._unicode else "~"

    @property
    def PALETTE(self):
        return "◧" if self._unicode else "#"

    @property
    def LINE_H(self):
        return "─" if self._unicode else "-"

    def section(self, title: str) -> str:
        if self._unicode:
            return f"─── {title} ───"
        else:
            return f"--- {title} ---"

    @property
    def DEGREE(self):
        return "°" if self._unicode else " deg"


# Globale Instanz
S = Symbols(use_unicode=True)
