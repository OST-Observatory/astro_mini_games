"""Solar system main app"""

from pathlib import Path

import yaml
from shared.base_app import AstroApp
from shared.i18n import tr
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from ui.theme import Colors, MIN_TOUCH_TARGET, SPACING_MD
from ui.rounded_button import RoundedButton
from ui.info_panel import InfoPanel
from ui.date_picker import DatePickerPopup
from visualization.renderer import SolarSystemRenderer


def _font():
    from shared.fonts import get_safe_font
    return get_safe_font()


class SonnensystemApp(AstroApp):
    """Solar system Kivy application."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_path = Path(__file__).parent.parent / "config.yaml"
        self.screen = "intro"  # intro | explore

    def _apply_locale(self):
        super()._apply_locale()
        if getattr(self, "_intro_heading", None):
            self._intro_heading.text = tr("sonnensystem.title")
            self._intro_label.text = tr("sonnensystem.intro")
            self._intro_start.text = tr("sonnensystem.lets_go")
            self._intro_exit.text = tr("sonnensystem.back_launcher")
        if getattr(self, "_settings_heading", None):
            self._settings_heading.text = tr("sonnensystem.settings")
            self._date_btn.text = tr("sonnensystem.date")
            self.legend_btn.text = tr("sonnensystem.legend")
            self.namen_btn.text = (
                tr("sonnensystem.names_off")
                if self.renderer.show_planet_labels
                else tr("sonnensystem.names_on")
            )
            self.vergroessert_btn.text = tr("sonnensystem.planets_large")
            self.massstab_btn.text = tr("sonnensystem.planets_scale")
            self._back_btn.text = tr("sonnensystem.back_launcher")
            self._reset_btn.text = tr("sonnensystem.reset")
        if getattr(self, "info_panel", None):
            self.info_panel.apply_i18n()

    def build(self):
        """Build the solar system UI: renderer, intro, info panel, controls."""
        self.title = "Sonnensystem"
        Window.bind(on_keyboard=self._on_keyboard)

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        root = FloatLayout()
        with root.canvas.before:
            Color(*Colors.BG_VIEW)
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(size=self._update_bg)

        self.renderer = SolarSystemRenderer(
            config,
            on_planet_tap=self._on_planet_tap,
            size_hint=(1, 1),
        )
        root.add_widget(self.renderer)

        # Intro screen
        self._build_intro(root)

        # Info panel (hidden)
        self.info_panel = InfoPanel()
        root.add_widget(self.info_panel)
        root.bind(size=lambda inst, val: self.info_panel._update_width())

        # Controls (visible only in explore)
        self._ctrl_box = None
        self._time_box = None
        self._back_btn = None

        # Controls: Play/Pause first, then rotation, zoom, reset
        btn_sz = MIN_TOUCH_TARGET
        ctrl_box = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            size=(btn_sz * 6 + 80 + SPACING_MD * 6, btn_sz),
            pos_hint={"x": 0.02, "bottom": 0.02},
            spacing=SPACING_MD,
        )
        self.pause_btn = RoundedButton(
            text=">" if self.renderer.paused else "||",
            font_name=_font(),
            font_size="22sp",
            size_hint=(None, None),
            size=(btn_sz, btn_sz),
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        self.pause_btn.bind(on_release=self._toggle_pause)
        ctrl_box.add_widget(self.pause_btn)
        rot_l_btn = RoundedButton(
            text="↶",
            font_name=_font(),
            font_size="24sp",
            size_hint=(None, None),
            size=(btn_sz, btn_sz),
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        rot_l_btn.bind(on_release=lambda x: self._rotate(-0.2))
        ctrl_box.add_widget(rot_l_btn)
        rot_r_btn = RoundedButton(
            text="↷",
            font_name=_font(),
            font_size="24sp",
            size_hint=(None, None),
            size=(btn_sz, btn_sz),
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        rot_r_btn.bind(on_release=lambda x: self._rotate(0.2))
        ctrl_box.add_widget(rot_r_btn)

        zoom_out_btn = RoundedButton(
            text="−",
            font_name=_font(),
            font_size="30sp",
            size_hint=(None, None),
            size=(btn_sz, btn_sz),
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        zoom_out_btn.bind(on_release=lambda x: self._zoom(0.9))
        ctrl_box.add_widget(zoom_out_btn)

        zoom_in_btn = RoundedButton(
            text="+",
            font_name=_font(),
            font_size="30sp",
            size_hint=(None, None),
            size=(btn_sz, btn_sz),
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        zoom_in_btn.bind(on_release=lambda x: self._zoom(1.1))
        ctrl_box.add_widget(zoom_in_btn)
        self._reset_btn = RoundedButton(
            text=tr("sonnensystem.reset"),
            font_name=_font(),
            font_size="16sp",
            size_hint=(None, None),
            size=(80, btn_sz),
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        self._reset_btn.bind(on_release=lambda x: self._reset_view())
        ctrl_box.add_widget(self._reset_btn)
        self._ctrl_box = ctrl_box
        ctrl_box.opacity = 0
        root.add_widget(ctrl_box)

        self._back_btn = RoundedButton(
            text=tr("sonnensystem.back_launcher"),
            font_name=_font(),
            font_size="14sp",
            size_hint=(None, None),
            size=(200, MIN_TOUCH_TARGET),
            pos_hint={"right": 0.53, "bottom": 0.02},
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        self._back_btn.bind(on_release=lambda x: self.stop())
        self._back_btn.opacity = 0
        root.add_widget(self._back_btn)

        # Settings (top left) – frame and label
        settings_outer = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(340, 275),
            pos_hint={"x": 0.02, "top": 0.98},
            spacing=0,
            padding=(0, 0, 0, 0),
        )
        with settings_outer.canvas.before:
            from kivy.graphics import RoundedRectangle
            Color(*Colors.BG_PANEL)
            settings_outer._bg = RoundedRectangle(
                pos=(0, 0), size=(0, 0), radius=[10] * 4
            )
        settings_outer.bind(pos=lambda b, v: setattr(b._bg, "pos", v))
        settings_outer.bind(size=lambda b, v: setattr(b._bg, "size", v))

        self._settings_heading = Label(
            text=tr("sonnensystem.settings"),
            font_name=_font(),
            font_size="14sp",
            bold=True,
            color=Colors.TEXT_SECONDARY,
            size_hint_y=None,
            height=28,
        )
        settings_outer.add_widget(self._settings_heading)

        time_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=242,
            spacing=6,
            padding=8,
        )

        self.time_label = Label(
            text="",
            font_name=_font(),
            font_size="22sp",
            color=Colors.TEXT_PRIMARY,
            size_hint_y=None,
            height=32,
        )
        time_box.add_widget(self.time_label)
        btn_h = MIN_TOUCH_TARGET
        ts_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=btn_h, spacing=6)
        self._speed_buttons = {}
        for mult, lbl in [(1, "1×"), (10, "10×"), (100, "100×")]:
            is_active = mult == self.renderer.time_scale
            btn = RoundedButton(
                text=lbl,
                font_name=_font(),
                font_size="18sp",
                size_hint_x=None,
                width=btn_h,
                background_color=Colors.BG_BUTTON_ACTIVE if is_active else Colors.BG_BUTTON,
                color=Colors.TEXT_PRIMARY,
            )
            btn.bind(on_release=lambda b, m=mult: self._set_time_scale(m))
            self._speed_buttons[mult] = btn
            ts_row.add_widget(btn)
        time_box.add_widget(ts_row)
        row2 = BoxLayout(orientation="horizontal", size_hint_y=None, height=btn_h, spacing=6)
        self._date_btn = RoundedButton(
            text=tr("sonnensystem.date"),
            font_name=_font(),
            font_size="16sp",
            size_hint_x=None,
            width=90,
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        self._date_btn.bind(on_release=self._open_date_picker)
        row2.add_widget(self._date_btn)

        self.legend_btn = RoundedButton(
            text=tr("sonnensystem.legend"),
            font_name=_font(),
            font_size="15sp",
            size_hint_x=None,
            width=105,
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        self.legend_btn.bind(on_release=self._toggle_legend)
        row2.add_widget(self.legend_btn)
        self.namen_btn = RoundedButton(
            text=tr("sonnensystem.names_off"),
            font_name=_font(),
            font_size="14sp",
            size_hint_x=None,
            width=105,
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        self.namen_btn.bind(on_release=self._toggle_planet_labels)
        row2.add_widget(self.namen_btn)
        time_box.add_widget(row2)

        row3 = BoxLayout(orientation="horizontal", size_hint_y=None, height=btn_h, spacing=6)
        self.vergroessert_btn = RoundedButton(
            text=tr("sonnensystem.planets_large"),
            font_name=_font(),
            font_size="14sp",
            size_hint_x=None,
            width=180,
            background_color=Colors.BG_BUTTON_ACTIVE,
            color=Colors.TEXT_PRIMARY,
        )
        self.vergroessert_btn.bind(on_release=lambda x: self._set_size_mode("vergroessert"))
        row3.add_widget(self.vergroessert_btn)
        self.massstab_btn = RoundedButton(
            text=tr("sonnensystem.planets_scale"),
            font_name=_font(),
            font_size="14sp",
            size_hint_x=None,
            width=180,
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        self.massstab_btn.bind(on_release=lambda x: self._set_size_mode("massstab"))
        row3.add_widget(self.massstab_btn)
        time_box.add_widget(row3)

        settings_outer.add_widget(time_box)
        self._legend_panel = None
        self._time_box = settings_outer
        settings_outer.opacity = 0
        root.add_widget(settings_outer)

        Clock.schedule_interval(self._update_time_label, 0.3)
        return root

    def _set_time_scale(self, mult: float):
        self.renderer.time_scale = float(mult)
        for m, btn in self._speed_buttons.items():
            btn.set_display_color(
                Colors.BG_BUTTON_ACTIVE if m == mult else Colors.BG_BUTTON
            )

    def _rotate(self, delta_rad: float):
        self.renderer.camera.rotate_by_angle(delta_rad)

    def _reset_view(self):
        self.renderer.camera.reset_view()

    def _open_date_picker(self, *args):
        popup = DatePickerPopup(
            initial_date=self.renderer.sim_date,
            on_date_set=lambda dt: setattr(self.renderer, "sim_date", dt),
        )
        popup.open()

    def _set_size_mode(self, mode: str):
        self.renderer.size_mode = mode
        self.vergroessert_btn.set_display_color(
            Colors.BG_BUTTON_ACTIVE if mode == "vergroessert" else Colors.BG_BUTTON
        )
        self.massstab_btn.set_display_color(
            Colors.BG_BUTTON_ACTIVE if mode == "massstab" else Colors.BG_BUTTON
        )

    def _toggle_planet_labels(self, instance):
        self.renderer.show_planet_labels = not self.renderer.show_planet_labels
        instance.text = (
            tr("sonnensystem.names_off")
            if self.renderer.show_planet_labels
            else tr("sonnensystem.names_on")
        )

    def _toggle_legend(self, instance):
        if self._legend_panel is None:
            self._build_legend()
        if self._legend_panel.parent:
            self.root.remove_widget(self._legend_panel)
            instance.text = tr("sonnensystem.legend")
        else:
            self.root.add_widget(self._legend_panel)
            instance.text = tr("sonnensystem.legend_check")

    def _build_legend(self):
        from simulation.planet_data import PLANET_ORDER, PLANET_COLORS
        box = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(120, 260),
            pos_hint={"right": 0.98, "center_y": 0.5},
            padding=10,
            spacing=4,
        )
        with box.canvas.before:
            from kivy.graphics import RoundedRectangle
            Color(*Colors.BG_PANEL)
            box._bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[12] * 4)
        box.bind(pos=lambda b, v: setattr(b._bg, "pos", v))
        box.bind(size=lambda b, v: setattr(b._bg, "size", v))
        for name in PLANET_ORDER:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=28, spacing=8)
            dot = Button(
                text="",
                size_hint=(None, None),
                size=(20, 20),
                background_color=PLANET_COLORS.get(name, [1, 1, 1, 1]),
                background_normal="",
            )
            row.add_widget(dot)
            row.add_widget(
                Label(text=name, font_name=_font(), font_size="15sp", color=Colors.TEXT_PRIMARY)
            )
            box.add_widget(row)
        self._legend_panel = box

    def _build_intro(self, root):
        layout = FloatLayout(size_hint=(1, 1))
        self._intro_heading = Label(
            text=tr("sonnensystem.title"),
            font_name=_font(),
            font_size="50sp",
            bold=True,
            color=Colors.TEXT_PRIMARY,
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "top": 0.92},
        )
        self._intro_heading.bind(texture_size=self._intro_heading.setter("size"))
        layout.add_widget(self._intro_heading)

        scroll = ScrollView(size_hint=(0.6, 0.4), pos_hint={"center_x": 0.5, "top": 0.82})
        self._intro_label = Label(
            text=tr("sonnensystem.intro"),
            font_name=_font(),
            font_size="25sp",
            color=Colors.TEXT_PRIMARY,
            size_hint=(1, None),
            halign="center",
            valign="middle",
        )
        self._intro_label.bind(
            texture_size=lambda lbl, val: setattr(lbl, "height", val[1] + 40),
            size=lambda lbl, val: setattr(lbl, "text_size", (val[0], None)),
        )
        scroll.add_widget(self._intro_label)
        layout.add_widget(scroll)

        self._intro_start = RoundedButton(
            text=tr("sonnensystem.lets_go"),
            font_name=_font(),
            font_size="35sp",
            bold=True,
            size_hint=(0.5, 0.1),
            pos_hint={"center_x": 0.5, "center_y": 0.35},
            background_color=Colors.ACCENT,
            color=Colors.TEXT_PRIMARY,
        )
        self._intro_start.bind(on_release=self._start_explore)
        layout.add_widget(self._intro_start)

        self._intro_exit = RoundedButton(
            text=tr("sonnensystem.back_launcher"),
            font_name=_font(),
            font_size="16sp",
            size_hint=(0.5, 0.08),
            pos_hint={"center_x": 0.5, "bottom": 0.04},
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        self._intro_exit.bind(on_release=lambda x: self.stop())
        layout.add_widget(self._intro_exit)

        self._intro_layout = layout
        root.add_widget(layout)

    def _start_explore(self, *args):
        self.screen = "explore"
        self.root.remove_widget(self._intro_layout)
        if self._ctrl_box:
            self._ctrl_box.opacity = 1
        if self._time_box:
            self._time_box.opacity = 1
        if self._back_btn:
            self._back_btn.opacity = 1

    def _update_time_label(self, dt):
        if hasattr(self, "time_label") and hasattr(self, "renderer"):
            d = self.renderer.sim_date
            self.time_label.text = d.strftime("%d.%m.%Y")

    def _zoom(self, factor: float):
        self.renderer.camera.zoom(factor)

    def _update_bg(self, instance, value):
        self._bg_rect.pos = instance.pos
        self._bg_rect.size = instance.size

    def _on_planet_tap(self, planet_name: str):
        self.info_panel.show(planet_name, self.renderer.sim_date)

    def _toggle_pause(self, instance):
        self.renderer.paused = not self.renderer.paused
        instance.text = ">" if self.renderer.paused else "||"

    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:
            self.stop()
            return True
        if key == 281:  # Page Down / Zoom out
            self.renderer.camera.zoom(0.9)
        if key == 280:  # Page Up / Zoom in
            self.renderer.camera.zoom(1.1)
        return False
