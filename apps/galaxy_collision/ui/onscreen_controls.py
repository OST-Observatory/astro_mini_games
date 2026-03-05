"""
On-screen controls for touch devices.
Central bottom bar with Play, Reset, Zoom, Rotate - Material Icons, RoundedButton.
"""

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.app import App
from kivy.graphics import Color, RoundedRectangle

from ui.material_icons import get_icon, get_icon_font
from ui.rounded_button import RoundedButton
from ui.theme import Colors, MIN_TOUCH_TARGET, RADIUS_MD, SPACING_SM


class OnScreenControls(FloatLayout):
    """On-Screen Controls - zentrale Bottom-Bar, Touch-optimiert"""

    simulation = ObjectProperty(None)

    def __init__(self, simulation=None, use_drawer=False, show_zoom_buttons=True, **kwargs):
        super().__init__(**kwargs)
        self.simulation = simulation
        self.use_drawer = use_drawer
        self.show_zoom_buttons = show_zoom_buttons
        self.size_hint = (1, None)
        self.button_size = max(56, MIN_TOUCH_TARGET)
        self.bar_height = self.button_size + SPACING_SM * 2
        self.height = self.bar_height + 20
        self.pos_hint = {"x": 0, "y": 0}
        self._icon_font = get_icon_font()
        self._build_controls()

    def _build_controls(self):
        """Zentrale Bottom-Bar: Play, Reset, Rotate L/R, Zoom In/Out"""
        self.bar = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            height=self.bar_height,
            spacing=SPACING_SM,
            padding=[SPACING_SM, SPACING_SM],
        )
        with self.bar.canvas.before:
            Color(*Colors.BG_PANEL[:3], 0.85)
            self.bar_bg = RoundedRectangle(
                pos=self.bar.pos,
                size=self.bar.size,
                radius=[RADIUS_MD],
            )
        self.bar.bind(
            pos=lambda i, p: setattr(self.bar_bg, "pos", p),
            size=lambda i, s: setattr(self.bar_bg, "size", s),
        )

        # Play/Pause
        self.play_btn = RoundedButton(
            text=get_icon("play_arrow"),
            font_name=self._icon_font,
            font_size="28sp",
            size_hint=(None, None),
            size=(self.button_size, self.button_size),
            background_color=(*Colors.PLAY[:3], 0.95),
            color=Colors.TEXT_PRIMARY,
        )
        self.play_btn.bind(on_release=self._on_play)
        self.bar.add_widget(self.play_btn)

        # Reset
        self.reset_btn = RoundedButton(
            text=get_icon("replay"),
            font_name=self._icon_font,
            font_size="24sp",
            size_hint=(None, None),
            size=(self.button_size, self.button_size),
            background_color=(*Colors.RESET[:3], 0.95),
            color=Colors.TEXT_PRIMARY,
        )
        self.reset_btn.bind(on_release=self._on_reset)
        self.bar.add_widget(self.reset_btn)

        # Rotate Left
        self.rot_l_btn = RoundedButton(
            text=get_icon("rotate_left"),
            font_name=self._icon_font,
            font_size="24sp",
            size_hint=(None, None),
            size=(self.button_size, self.button_size),
            background_color=(*Colors.NEUTRAL[:3], 0.95),
            color=Colors.TEXT_PRIMARY,
        )
        self.rot_l_btn.bind(on_release=self._on_rotate_left)
        self.bar.add_widget(self.rot_l_btn)

        # Rotate Right
        self.rot_r_btn = RoundedButton(
            text=get_icon("rotate_right"),
            font_name=self._icon_font,
            font_size="24sp",
            size_hint=(None, None),
            size=(self.button_size, self.button_size),
            background_color=(*Colors.NEUTRAL[:3], 0.95),
            color=Colors.TEXT_PRIMARY,
        )
        self.rot_r_btn.bind(on_release=self._on_rotate_right)
        self.bar.add_widget(self.rot_r_btn)

        if self.show_zoom_buttons:
            # Zoom In
            self.zoom_in_btn = RoundedButton(
                text=get_icon("zoom_in"),
                font_name=self._icon_font,
                font_size="24sp",
                size_hint=(None, None),
                size=(self.button_size, self.button_size),
                background_color=(*Colors.NEUTRAL[:3], 0.95),
                color=Colors.TEXT_PRIMARY,
            )
            self.zoom_in_btn.bind(on_release=self._on_zoom_in)
            self.bar.add_widget(self.zoom_in_btn)

            # Zoom Out
            self.zoom_out_btn = RoundedButton(
                text=get_icon("zoom_out"),
                font_name=self._icon_font,
                font_size="24sp",
                size_hint=(None, None),
                size=(self.button_size, self.button_size),
                background_color=(*Colors.NEUTRAL[:3], 0.95),
                color=Colors.TEXT_PRIMARY,
            )
            self.zoom_out_btn.bind(on_release=self._on_zoom_out)
            self.bar.add_widget(self.zoom_out_btn)
        else:
            self.zoom_in_btn = None
            self.zoom_out_btn = None

        self.add_widget(self.bar)
        self.bind(size=self._update_positions)

    def _update_positions(self, instance, size):
        """Center the bar at the bottom."""
        if size[0] == 0 or size[1] == 0:
            return
        n = 6 if self.show_zoom_buttons else 4  # Play, Reset, RotL, RotR, [ZoomIn, ZoomOut]
        bar_w = n * self.button_size + (n - 1) * SPACING_SM + SPACING_SM * 2
        self.bar.size = (bar_w, self.bar_height)
        self.bar.pos = ((size[0] - bar_w) / 2, 10)

    def _on_play(self, instance):
        if not self.simulation:
            return
        app = App.get_running_app()
        if self.simulation.paused:
            self.simulation.play()
            self.play_btn.text = get_icon("pause")
            self.play_btn.set_display_color((*Colors.PAUSE[:3], 0.95))
        else:
            self.simulation.pause()
            self.play_btn.text = get_icon("play_arrow")
            self.play_btn.set_display_color((*Colors.PLAY[:3], 0.95))

    def _on_reset(self, instance):
        app = App.get_running_app()
        if app and hasattr(app, "panel") and app.panel:
            app.panel._on_reset(None)

    def _on_rotate_left(self, instance):
        """Kamera links drehen"""
        app = App.get_running_app()
        if app and hasattr(app, "view") and app.view:
            app.view.camera.rotate(15, 0)

    def _on_rotate_right(self, instance):
        """Kamera rechts drehen"""
        app = App.get_running_app()
        if app and hasattr(app, "view") and app.view:
            app.view.camera.rotate(-15, 0)

    def _on_zoom_out(self, instance):
        app = App.get_running_app()
        if app and hasattr(app, "view") and app.view:
            cam = app.view.camera
            cam.distance = min(cam.max_distance, cam.distance + 30)

    def _on_zoom_in(self, instance):
        app = App.get_running_app()
        if app and hasattr(app, "view") and app.view:
            cam = app.view.camera
            cam.distance = max(cam.min_distance, cam.distance - 30)

    def update_play_button(self, is_paused):
        if is_paused:
            self.play_btn.text = get_icon("play_arrow")
            self.play_btn.set_display_color((*Colors.PLAY[:3], 0.95))
        else:
            self.play_btn.text = get_icon("pause")
            self.play_btn.set_display_color((*Colors.PAUSE[:3], 0.95))
