"""Slide-in panel with planet info."""

from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from ui.theme import Colors, SPACING_MD, RADIUS_LG, MIN_TOUCH_TARGET


def _font():
    from shared.fonts import get_safe_font
    return get_safe_font()


# Extended planet data with description and comparisons
PLANET_INFO = {
    "Merkur": {
        "distance": "0.39x Erde - Sonne",
        "period": "88 Tage",
        "mass": "0.06 Erdmassen",
        "size": "0.38 Erddurchmesser",
        "type": "Gesteinsplanet",
        "desc": "Er ist der kleinste Planet und der Sonne am nächsten.",
    },
    "Venus": {
        "distance": "0.72x Erde - Sonne",
        "period": "225 Tage",
        "mass": "0.82 Erdmassen",
        "size": "0.95 Erddurchmesser",
        "type": "Gesteinsplanet",
        "desc": "Schwesterplanet der Erde mit einer dichten Atmosphäre und einem galoppierenden Treibhauseffekt.",
    },
    "Erde": {
        "distance": "1.00x Erde - Sonne",
        "period": "365 Tage",
        "mass": "1.00 Erdmasse",
        "size": "1.00 Erddurchmesser",
        "type": "Gesteinsplanet",
        "desc": "Unser Heimatplanet und der einzige mit flüssigem Wasser an der Oberfläche.",
    },
    "Mars": {
        "distance": "1.52x Erde - Sonne",
        "period": "687 Tage",
        "mass": "0.11 Erdmassen",
        "size": "0.53 Erddurchmesser",
        "type": "Gesteinsplanet",
        "desc": "Der Rote Planet - Er hat den höchsten Vulkan im Sonnensystem, Olympus Mons.",
    },
    "Jupiter": {
        "distance": "5.20x Erde - Sonne",
        "period": "12 Jahre",
        "mass": "318 Erdmassen",
        "size": "11.2 Erddurchmesser",
        "type": "Gasriese",
        "desc": "Der größte Planet im Sonnensystem mit einem Sturmsystem größer als die Erde dem Großen Roten Fleck.",
    },
    "Saturn": {
        "distance": "9.54x Erde - Sonne",
        "period": "29 Jahre",
        "mass": "95 Erdmassen",
        "size": "9.45 Erddurchmesser",
        "type": "Gasriese",
        "desc": "Berühmt für sein Ringystem aus Eis und Gestein.",
    },
    "Uranus": {
        "distance": "19.2x Erde - Sonne",
        "period": "84 Jahre",
        "mass": "14.5 Erdmassen",
        "size": "4 Erddurchmesser",
        "type": "Eisriese",
        "desc": "Ein Eisriese, der seitlich gekippt ist, wahrscheinlich durch einen Stoß mit einem anderen Planeten.",
    },
    "Neptun": {
        "distance": "30.1x Erde - Sonne",
        "period": "165 Jahre",
        "mass": "17.1 Erdmassen",
        "size": "3.9 Erddurchmesser",
        "type": "Eisriese",
        "desc": "Der außerste Planet im Sonnensystem. Licht braucht mehr als 4 Stunden von der Sonne bis zum Neptun.",
    },
}


class InfoPanel(BoxLayout):
    """Slide-in panel with planet info."""

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(None, 1),
            width=350,
            padding=SPACING_MD,
            spacing=SPACING_MD,
            **kwargs
        )
        self.pos_hint = {"right": 1, "top": 1}
        self.bind(parent=self._update_width)
        with self.canvas.before:
            Color(*Colors.BG_PANEL)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[RADIUS_LG] * 4)
        self.bind(pos=self._update_bg, size=self._update_bg)
        self.label_name = Label(
            text="",
            font_name=_font(),
            font_size="28sp",
            bold=True,
            color=Colors.ACCENT,
            size_hint_y=None,
            height=50,
        )
        self.add_widget(self.label_name)
        self.label_info = Label(
            text="",
            font_name=_font(),
            font_size="20sp",
            color=Colors.TEXT_SECONDARY,
            halign="left",
            size_hint_y=1,
        )
        self.label_info.bind(size=lambda *x: setattr(self.label_info, "text_size", (self.label_info.width - 24, None)))
        self.add_widget(self.label_info)
        self.label_sim_time = Label(
            text="",
            font_name=_font(),
            font_size="14sp",
            color=Colors.TEXT_SECONDARY,
            size_hint_y=None,
            height=24,
        )
        self.add_widget(self.label_sim_time)
        close_btn = Button(
            text="Schließen",
            font_name=_font(),
            font_size="20sp",
            size_hint_y=None,
            height=MIN_TOUCH_TARGET,
            background_color=Colors.BG_BUTTON,
            background_normal="",
        )
        close_btn.bind(on_release=lambda x: self.hide())
        self.add_widget(close_btn)
        self.opacity = 0
        self.disabled = True

    def _update_bg(self, *args):
        if hasattr(self, "_bg_rect"):
            self._bg_rect.pos = self.pos
            self._bg_rect.size = self.size

    def _update_width(self, *args):
        if self.parent and self.parent.width > 0:
            self.width = max(280, min(400, self.parent.width * 0.35))

    def show(self, planet_name: str, sim_date=None):
        """Display planet info (name, description, distance, period, mass, etc.)."""
        info = PLANET_INFO.get(planet_name, {})
        self.label_name.text = planet_name
        key_labels = {
            "desc": "",
            "distance": "Abstand: ",
            "period": "Umlaufzeit: ",
            "mass": "Masse: ",
            "type": "Typ: ",
            "size": "Größe: ",
        }
        lines = []
        if "desc" in info:
            lines.append(info["desc"])
        for k in ("distance", "period", "mass", "size", "type"):
            if k in info:
                lines.append(key_labels[k] + str(info[k]))
        self.label_info.text = "\n\n".join(lines) if lines else "Keine Daten"
        if sim_date:
            self.label_sim_time.text = sim_date.strftime("Simulation: %d.%m.%Y")
        else:
            self.label_sim_time.text = ""
        self.opacity = 1
        self.disabled = False

    def hide(self):
        """Fade out and disable the info panel."""
        anim = Animation(opacity=0, duration=0.2)
        anim.start(self)
        self.disabled = True
