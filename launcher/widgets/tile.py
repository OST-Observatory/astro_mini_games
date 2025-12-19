"""
App-Kachel Widget mit Touch-Feedback und Aufmerksamkeits-Animation
"""

import math

from kivy.animation import Animation
from kivy.app import App
from kivy.graphics import (
    Color,
    Line,
    PopMatrix,
    PushMatrix,
    Rotate,
    RoundedRectangle,
    Translate,
)
from kivy.properties import (
    BooleanProperty,
    DictProperty,
    ListProperty,
    NumericProperty,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label


def hex_to_rgb(hex_color):
    """Konvertiert Hex-Farbe zu RGB-Tuple"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))


class AppTile(ButtonBehavior, BoxLayout):
    """
    Touch-fähige Kachel für eine App mit Wackel-Animation
    """

    app_config = DictProperty({})
    app_name = StringProperty("App")
    app_icon = StringProperty("*")
    app_description = StringProperty("")
    app_color = ListProperty([0.1, 0.1, 0.3, 1])

    # Animation Properties
    scale = NumericProperty(1.0)
    glow_alpha = NumericProperty(0)
    wiggle_angle = NumericProperty(0)  # NEU: Wackel-Winkel
    is_wiggling = BooleanProperty(False)  # NEU: Wackelt gerade?

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 15
        self.spacing = 8

        self.bind(app_config=self._apply_config)
        self.bind(size=self._on_size_change, pos=self._draw)
        self.bind(scale=self._draw, glow_alpha=self._draw, wiggle_angle=self._draw)

    def _apply_config(self, instance, config):
        """Wendet App-Konfiguration an"""
        self.app_name = config.get("name", "App")
        self.app_icon = config.get("icon", "*")
        self.app_description = config.get("description", "")

        color_hex = config.get("color", "#1a237e")
        rgb = hex_to_rgb(color_hex)
        self.app_color = [rgb[0], rgb[1], rgb[2], 0.85]

        self._build_ui()
        self._draw()

    def _on_size_change(self, *args):
        """Wird aufgerufen wenn sich die Größe ändert"""
        self._update_font_sizes()
        self._draw()

    def _update_font_sizes(self):
        """Passt Schriftgrößen an Kachelgröße an"""
        if not self.children or self.width <= 0:
            return

        base = min(self.width, self.height)

        for i, child in enumerate(reversed(self.children)):
            if isinstance(child, Label):
                if i == 0:  # Icon
                    child.font_size = base * 0.25
                elif i == 1:  # Name
                    child.font_size = base * 0.12
                else:  # Description
                    child.font_size = base * 0.07

    def _build_ui(self):
        """Erstellt die UI-Elemente"""
        self.clear_widgets()

        icon_label = Label(text=self.app_icon, font_size="48sp", size_hint_y=0.45)

        name_label = Label(
            text=self.app_name, font_size="22sp", bold=True, size_hint_y=0.28
        )

        desc_label = Label(
            text=self.app_description,
            font_size="13sp",
            color=(1, 1, 1, 0.7),
            size_hint_y=0.27,
            halign="center",
            valign="top",
        )
        desc_label.bind(
            size=lambda *x: setattr(
                desc_label, "text_size", (desc_label.width - 10, None)
            )
        )

        self.add_widget(icon_label)
        self.add_widget(name_label)
        self.add_widget(desc_label)

        self._update_font_sizes()

    def _draw(self, *args):
        """Zeichnet den Hintergrund der Kachel mit Rotation"""
        self.canvas.before.clear()

        scaled_width = self.width * self.scale
        scaled_height = self.height * self.scale
        offset_x = (self.width - scaled_width) / 2
        offset_y = (self.height - scaled_height) / 2

        corner_radius = min(self.width, self.height) * 0.08

        # Zentrum für Rotation
        center_x = self.x + self.width / 2
        center_y = self.y + self.height / 2

        with self.canvas.before:
            PushMatrix()

            # Rotation um Zentrum (für Wackeln)
            Translate(center_x, center_y, 0)
            Rotate(angle=self.wiggle_angle, axis=(0, 0, 1))
            Translate(-center_x, -center_y, 0)

            # Glow-Effekt (verstärkt beim Wackeln)
            glow = self.glow_alpha
            if self.is_wiggling:
                glow = max(glow, 0.5)

            if glow > 0:
                Color(0.5, 0.7, 1, glow * 0.3)
                RoundedRectangle(
                    pos=(self.x + offset_x - 5, self.y + offset_y - 5),
                    size=(scaled_width + 10, scaled_height + 10),
                    radius=[corner_radius + 5],
                )

            # Haupthintergrund
            Color(*self.app_color)
            RoundedRectangle(
                pos=(self.x + offset_x, self.y + offset_y),
                size=(scaled_width, scaled_height),
                radius=[corner_radius],
            )

            # Rand
            Color(1, 1, 1, 0.2)
            Line(
                rounded_rectangle=(
                    self.x + offset_x,
                    self.y + offset_y,
                    scaled_width,
                    scaled_height,
                    corner_radius,
                ),
                width=1.2,
            )

            PopMatrix()

    def wiggle(self):
        """Startet die Wackel-Animation"""
        if self.is_wiggling:
            return

        self.is_wiggling = True

        # Wackel-Sequenz: links-rechts-links-rechts-stop
        anim = (
            Animation(wiggle_angle=3, duration=0.08)
            + Animation(wiggle_angle=-3, duration=0.08)
            + Animation(wiggle_angle=2.5, duration=0.07)
            + Animation(wiggle_angle=-2.5, duration=0.07)
            + Animation(wiggle_angle=1.5, duration=0.06)
            + Animation(wiggle_angle=-1.5, duration=0.06)
            + Animation(wiggle_angle=0, duration=0.05)
        )

        anim.bind(on_complete=self._on_wiggle_complete)
        anim.start(self)

    def _on_wiggle_complete(self, *args):
        """Callback wenn Wackeln fertig"""
        self.is_wiggling = False
        self.wiggle_angle = 0

    def on_press(self):
        """Touch-Start Animation"""
        # Wackeln stoppen falls aktiv
        Animation.cancel_all(self, "wiggle_angle")
        self.is_wiggling = False
        self.wiggle_angle = 0

        Animation.cancel_all(self, "scale", "glow_alpha")
        anim = Animation(scale=0.95, glow_alpha=1, duration=0.1)
        anim.start(self)

    def on_release(self):
        """Touch-Ende - App starten"""
        Animation.cancel_all(self, "scale", "glow_alpha")

        anim = Animation(scale=1.0, glow_alpha=0, duration=0.2)
        anim.start(self)

        app = App.get_running_app()
        if app and self.app_config:
            app.launch_app(self.app_config)
