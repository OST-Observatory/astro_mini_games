"""Three locale toggles for DE / EN / ES (PNG flags in ``assets/locale_flags/``, text fallback)."""

from __future__ import annotations

from pathlib import Path

from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image

from shared.i18n import get_locale, set_locale

LABEL_DE = "DE"
LABEL_EN = "EN"
LABEL_ES = "ES"


def _package_root(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    return Path(__file__).resolve().parent.parent.parent


def _flag_png_path(root: Path, code: str) -> Path | None:
    base = root / "assets" / "locale_flags"
    candidates = [base / f"{code}.png"]
    if code == "en":
        candidates.extend(
            [
                base / "gb.png",
                base / "en_GB.png",
                base / "uk.png",
            ]
        )
    for p in candidates:
        if p.is_file():
            return p
    return None


class _LocaleFlagButton(ButtonBehavior, Image):
    """Pressable flag image; ``color`` tints the texture for selection state."""

    def __init__(self, source: str, **kwargs):
        super().__init__(
            source=source,
            allow_stretch=True,
            keep_ratio=True,
            **kwargs,
        )


class LanguageSwitcher(BoxLayout):
    """Horizontal row of locale toggle buttons."""

    def __init__(self, project_root=None, **kwargs):
        super().__init__(**kwargs)
        self._project_root = project_root
        self.orientation = "horizontal"
        self.spacing = dp(6)
        self.size_hint = (None, None)
        self.padding = [dp(6), dp(4), dp(6), dp(4)]

        root = _package_root(project_root)
        self._buttons: dict[str, Button | _LocaleFlagButton] = {}
        for code, label in (("de", LABEL_DE), ("en", LABEL_EN), ("es", LABEL_ES)):
            png = _flag_png_path(root, code)
            if png is not None:
                btn = _LocaleFlagButton(
                    source=str(png),
                    size_hint=(None, None),
                    size=(dp(52), dp(36)),
                    mipmap=True,
                )
            else:
                btn = Button(
                    text=label,
                    bold=True,
                    font_size="20sp",
                    size_hint=(None, None),
                    size=(dp(44), dp(40)),
                )
            btn.bind(on_press=lambda inst, c=code: self._on_pick(c))
            self.add_widget(btn)
            self._buttons[code] = btn

        self.bind(minimum_size=self.setter("size"))

        self._update_highlight()

    def _on_pick(self, code: str):
        set_locale(code, self._project_root)
        self._update_highlight()

    def _update_highlight(self):
        current = get_locale()
        for code, btn in self._buttons.items():
            active = code == current
            if isinstance(btn, _LocaleFlagButton):
                btn.color = (0.75, 0.88, 1.0, 1.0) if active else (0.55, 0.55, 0.58, 1.0)
            else:
                btn.background_color = (
                    (0.35, 0.55, 0.85, 1) if active else (0.2, 0.2, 0.28, 0.9)
                )

    def refresh_highlight(self):
        """Call after external set_locale (e.g. env already updated)."""
        self._update_highlight()
