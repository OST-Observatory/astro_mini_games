"""
App tile widget with touch feedback and attention animation.
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

from launcher.material_icons import resolve_icon


def hex_to_rgb(hex_color):
    """Converts hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))


class AppTile(ButtonBehavior, BoxLayout):
    """
    Touchable tile for an app with wiggle animation.
    """

    app_config = DictProperty({})
    app_name = StringProperty("App")
    app_icon = StringProperty("*")
    app_description = StringProperty("")
    app_color = ListProperty([0.1, 0.1, 0.3, 1])

    # Animation Properties
    scale = NumericProperty(1.0)
    glow_alpha = NumericProperty(0)
    wiggle_angle = NumericProperty(0)  # Wiggle angle
    is_wiggling = BooleanProperty(False)  # Currently wiggling?

    _icon_font = None  # Path to Material Icons font, or None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 15
        self.spacing = 8
        self._icon_font = None

        self.bind(app_config=self._apply_config)
        self.bind(size=self._on_size_change, pos=self._draw)
        self.bind(scale=self._draw, glow_alpha=self._draw, wiggle_angle=self._draw)

    def _apply_config(self, instance, config):
        """Applies app configuration."""
        self.app_name = config.get("name", "App")
        self.app_description = config.get("description", "")

        icon_char, icon_font = resolve_icon(config.get("icon", "*"))
        self.app_icon = icon_char
        self._icon_font = icon_font

        color_hex = config.get("color", "#1a237e")
        rgb = hex_to_rgb(color_hex)
        self.app_color = [rgb[0], rgb[1], rgb[2], 0.85]

        self._build_ui()
        self._draw()

    def _on_size_change(self, *args):
        """Called when size changes."""
        self._update_font_sizes()
        self._draw()

    def _update_font_sizes(self):
        """Adjusts font sizes to tile size."""
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
        """Builds the UI elements."""
        self.clear_widgets()

        icon_kw = {"text": self.app_icon, "font_size": "48sp", "size_hint_y": 0.45}
        if getattr(self, "_icon_font", None):
            icon_kw["font_name"] = self._icon_font
        icon_label = Label(**icon_kw)

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
        """Draws the tile background with rotation."""
        self.canvas.before.clear()

        scaled_width = self.width * self.scale
        scaled_height = self.height * self.scale
        offset_x = (self.width - scaled_width) / 2
        offset_y = (self.height - scaled_height) / 2

        corner_radius = min(self.width, self.height) * 0.08

        # Center for rotation
        center_x = self.x + self.width / 2
        center_y = self.y + self.height / 2

        with self.canvas.before:
            PushMatrix()

            # Rotation around center (for wiggle)
            Translate(center_x, center_y, 0)
            Rotate(angle=self.wiggle_angle, axis=(0, 0, 1))
            Translate(-center_x, -center_y, 0)

            # Glow effect (enhanced when wiggling)
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

            # Main background
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
        """Starts the wiggle animation."""
        if self.is_wiggling:
            return

        self.is_wiggling = True

        # Wiggle sequence: left-right-left-right-stop
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
        """Callback when wiggle finished."""
        self.is_wiggling = False
        self.wiggle_angle = 0

    def on_press(self):
        """Touch start animation."""
        # Stop wiggle if active
        Animation.cancel_all(self, "wiggle_angle")
        self.is_wiggling = False
        self.wiggle_angle = 0

        Animation.cancel_all(self, "scale", "glow_alpha")
        anim = Animation(scale=0.95, glow_alpha=1, duration=0.1)
        anim.start(self)

    def on_release(self):
        """Touch end – launch app."""
        Animation.cancel_all(self, "scale", "glow_alpha")

        anim = Animation(scale=1.0, glow_alpha=0, duration=0.2)
        anim.start(self)

        app = App.get_running_app()
        if app and self.app_config:
            app.launch_app(self.app_config)
