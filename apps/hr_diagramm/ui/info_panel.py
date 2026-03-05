"""Slide-in info panel for star details."""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from ui.theme import Colors, SPACING_MD


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

    def show_star(self, star: dict):
        self.label_name.text = star.get("name", "Unbekannt")
        lines = [
            f"B-V: {star.get('bv', 0):.2f}",
            f"Abs. Mag: {star.get('absmag', 0):.1f}",
            f"Spektraltyp: {star.get('spect', '-')}",
            f"Masse: {star.get('mass', '-')} Sonnenmassen",
            f"Lebensdauer: {star.get('lifetime', '-')} Mrd. Jahre",
        ]
        self.label_info.text = "\n".join(lines)

    def hide(self):
        self.label_name.text = ""
        self.label_info.text = ""
