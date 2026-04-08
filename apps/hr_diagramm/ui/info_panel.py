"""Slide-in info panel for star details."""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from ui.theme import Colors, SPACING_MD
from shared.i18n import tr


def _font():
    from shared.fonts import get_safe_font
    return get_safe_font()


class InfoPanel(BoxLayout):
    """Shows star info: name, spectral type, mass, lifetime."""

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(None, 1),
            width=260,
            padding=SPACING_MD,
            spacing=SPACING_MD,
            **kwargs
        )
        self.pos_hint = {"right": 1, "top": 1}
        self.label_name = Label(
            text="",
            font_name=_font(),
            font_size="22sp",
            bold=True,
            color=Colors.ACCENT,
            size_hint_y=None,
            height=40,
        )
        self.add_widget(self.label_name)
        self.label_info = Label(
            text="",
            font_name=_font(),
            font_size="16sp",
            color=Colors.TEXT_SECONDARY,
            halign="left",
            size_hint_y=1,
        )
        self.label_info.bind(
            size=lambda *x: setattr(self.label_info, "text_size", (self.label_info.width - 20, None))
        )
        self.add_widget(self.label_info)
        self._last_star = None

    def show_star(self, star: dict):
        self._last_star = star
        self.label_name.text = star.get("name", tr("hr_diagramm.unknown"))
        lines = [
            tr("hr_diagramm.line_bv", v=star.get("bv", 0)),
            tr("hr_diagramm.line_absmag", v=star.get("absmag", 0)),
            tr("hr_diagramm.line_spectral", v=star.get("spect", "-")),
            tr("hr_diagramm.line_mass", v=star.get("mass", "-")),
            tr("hr_diagramm.line_lifetime", v=star.get("lifetime", "-")),
        ]
        self.label_info.text = "\n".join(lines)

    def apply_i18n(self):
        if self._last_star:
            self.show_star(self._last_star)

    def hide(self):
        self._last_star = None
        self.label_name.text = ""
        self.label_info.text = ""
