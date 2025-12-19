"""
Control Panel mit automatischem Unicode/ASCII-Fallback
"""

from kivy.app import App
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner

# Symbol-Import
from ui.symbols import S


class ParamSlider(BoxLayout):
    """Parameter-Slider"""

    def __init__(
        self, label, min_v, max_v, default, step, fmt="{:.1f}", callback=None, **kw
    ):
        super().__init__(**kw)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = 48
        self.spacing = 2
        self.padding = [5, 0]

        self.fmt = fmt
        self.callback = callback
        self.key = label

        row = BoxLayout(size_hint_y=0.45)

        self.lbl = Label(text=label, size_hint_x=0.6, font_size="11sp", halign="left")
        self.lbl.bind(
            size=lambda *x: setattr(self.lbl, "text_size", (self.lbl.width, None))
        )

        self.val_lbl = Label(
            text=fmt.format(default),
            size_hint_x=0.4,
            font_size="11sp",
            color=(0.4, 0.8, 1, 1),
            halign="right",
        )
        self.val_lbl.bind(
            size=lambda *x: setattr(
                self.val_lbl, "text_size", (self.val_lbl.width, None)
            )
        )

        row.add_widget(self.lbl)
        row.add_widget(self.val_lbl)

        self.slider = Slider(
            min=min_v,
            max=max_v,
            value=default,
            step=step,
            size_hint_y=0.55,
            value_track=True,
            value_track_color=[0.3, 0.6, 1, 1],
        )
        self.slider.bind(value=self._on_change)

        self.value = default

        self.add_widget(row)
        self.add_widget(self.slider)

    def _on_change(self, inst, val):
        self.value = val
        self.val_lbl.text = self.fmt.format(val)
        if self.callback:
            self.callback(self.key, val)


class ControlPanel(BoxLayout):
    """Control Panel mit Zoom-Buttons"""

    simulation = ObjectProperty(None)
    color_mode_callback = ObjectProperty(None)

    def __init__(self, simulation=None, config=None, **kwargs):
        self.simulation = simulation
        self.config = config or {}
        super().__init__(**kwargs)

        self.orientation = "vertical"
        self.padding = 8
        self.spacing = 4
        self.size_hint_x = None
        self.width = 280
        self.pos_hint = {"right": 1}

        self._params = {}

        with self.canvas.before:
            Color(0.08, 0.08, 0.12, 0.95)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(
            pos=lambda *x: setattr(self.bg, "pos", self.pos),
            size=lambda *x: setattr(self.bg, "size", self.size),
        )

        self._build_ui()

    def _build_ui(self):
        # Titel
        self.add_widget(
            Label(
                text=f"{S.SETTINGS} Simulation",
                font_size="14sp",
                bold=True,
                size_hint_y=None,
                height=28,
            )
        )

        # === ZOOM-BUTTONS ===
        zoom_box = BoxLayout(size_hint_y=None, height=40, spacing=5)

        zoom_out = Button(
            text=S.ZOOM_OUT,
            font_size="16sp",
            background_color=(0.3, 0.3, 0.4, 1),
            background_normal="",
        )
        zoom_out.bind(on_release=lambda x: self._zoom(30))

        zoom_label = Label(text="Zoom", font_size="12sp")

        zoom_in = Button(
            text=S.ZOOM_IN,
            font_size="16sp",
            background_color=(0.3, 0.3, 0.4, 1),
            background_normal="",
        )
        zoom_in.bind(on_release=lambda x: self._zoom(-30))

        zoom_box.add_widget(zoom_out)
        zoom_box.add_widget(zoom_label)
        zoom_box.add_widget(zoom_in)
        self.add_widget(zoom_box)

        # === PLAY/RESET ===
        btns = BoxLayout(size_hint_y=None, height=38, spacing=5)

        self.play_btn = Button(
            text=f"{S.PLAY} Start",
            font_size="12sp",
            background_color=(0.2, 0.55, 0.2, 1),
            background_normal="",
        )
        self.play_btn.bind(on_release=self._on_play)

        reset_btn = Button(
            text=f"{S.RESET} Reset",
            font_size="12sp",
            background_color=(0.55, 0.3, 0.2, 1),
            background_normal="",
        )
        reset_btn.bind(on_release=self._on_reset)

        btns.add_widget(self.play_btn)
        btns.add_widget(reset_btn)
        self.add_widget(btns)

        # === ZEITRAFFER ===
        self.time_slider = ParamSlider(
            f"{S.TIME} Zeitraffer",
            0.1,
            10.0,
            1.0,
            0.1,
            "{:.1f}x",
            callback=self._on_time,
        )
        self.add_widget(self.time_slider)

        # === FARBMODUS ===
        color_box = BoxLayout(size_hint_y=None, height=40, spacing=5, padding=[5, 0])
        color_box.add_widget(
            Label(text=f"{S.PALETTE} Farben:", size_hint_x=0.4, font_size="11sp")
        )

        self.color_spin = Spinner(
            text="Galaxien",
            values=["Galaxien", "Realistisch", "Geschwindigkeit"],
            size_hint_x=0.6,
            font_size="11sp",
        )
        self.color_spin.bind(text=self._on_color)
        color_box.add_widget(self.color_spin)
        self.add_widget(color_box)

        # === SCROLL-BEREICH ===
        scroll = ScrollView(size_hint=(1, 1))
        params = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=3, padding=[0, 5]
        )
        params.bind(minimum_height=params.setter("height"))

        # Galaxien
        params.add_widget(
            Label(
                text=S.section("Galaxien"),
                font_size="10sp",
                size_hint_y=None,
                height=20,
                color=(0.6, 0.6, 0.6, 1),
            )
        )

        self._add_slider(
            params, "Partikel", 5000, 30000, 20000, 5000, "{:.0f}", "total_particles"
        )
        self._add_slider(
            params, "M-Verhältnis", 0.2, 5.0, 1.0, 0.2, "{:.1f}", "mass_ratio"
        )
        self._add_slider(
            params, "Gesamtmasse", 1.0, 4.0, 2.0, 0.5, "{:.1f}", "total_mass"
        )

        # Kollision
        params.add_widget(
            Label(
                text=S.section("Kollision"),
                font_size="10sp",
                size_hint_y=None,
                height=20,
                color=(0.6, 0.6, 0.6, 1),
            )
        )

        self._add_slider(
            params, "Abstand", 30.0, 80.0, 50.0, 5.0, "{:.0f}", "initial_distance"
        )
        self._add_slider(
            params, "v/v_escape", 0.2, 0.9, 0.5, 0.1, "{:.1f}", "velocity_factor"
        )
        self._add_slider(
            params, "Impact", 0.0, 0.7, 0.3, 0.1, "{:.1f}", "impact_parameter"
        )
        self._add_slider(
            params,
            f"Inklination",
            0.0,
            90.0,
            30.0,
            10.0,
            "{:.0f}" + S.DEGREE,
            "inclination",
        )

        # Physik
        params.add_widget(
            Label(
                text=S.section("Physik"),
                font_size="10sp",
                size_hint_y=None,
                height=20,
                color=(0.6, 0.6, 0.6, 1),
            )
        )

        self._add_slider(
            params, "Reibung", 0.0, 0.05, 0.01, 0.005, "{:.3f}", "dynamic_friction"
        )
        self._add_slider(params, "Softening", 0.5, 3.0, 1.0, 0.5, "{:.1f}", "softening")

        # Hinweis
        params.add_widget(
            Label(
                text=f"{S.INFO} Parameter {S.ARROW_RIGHT} Reset drücken",
                font_size="9sp",
                size_hint_y=None,
                height=22,
                color=(0.4, 0.4, 0.4, 1),
            )
        )

        scroll.add_widget(params)
        self.add_widget(scroll)

        # Beenden
        exit_btn = Button(
            text=f"{S.CLOSE} Beenden",
            font_size="12sp",
            size_hint_y=None,
            height=36,
            background_color=(0.4, 0.15, 0.15, 1),
            background_normal="",
        )
        exit_btn.bind(on_release=lambda x: App.get_running_app().stop())
        self.add_widget(exit_btn)

        # Stats
        self.stats_lbl = Label(
            text="",
            font_size="9sp",
            size_hint_y=None,
            height=35,
            color=(0.5, 0.5, 0.5, 1),
        )
        self.add_widget(self.stats_lbl)

    def _add_slider(self, container, label, min_v, max_v, default, step, fmt, key):
        slider = ParamSlider(
            label,
            min_v,
            max_v,
            default,
            step,
            fmt,
            callback=lambda n, v, k=key: self._on_param(k, v),
        )
        self._params[key] = default
        container.add_widget(slider)

    def _zoom(self, delta):
        """Zoom ändern"""
        app = App.get_running_app()
        if app and hasattr(app, "view") and app.view:
            cam = app.view.camera
            cam.distance = max(
                cam.min_distance, min(cam.max_distance, cam.distance + delta)
            )

    def _on_play(self, inst):
        if not self.simulation:
            return
        if self.simulation.paused:
            self.simulation.play()
            self.play_btn.text = f"{S.PAUSE} Pause"
            self.play_btn.background_color = (0.55, 0.45, 0.15, 1)
        else:
            self.simulation.pause()
            self.play_btn.text = f"{S.PLAY} Start"
            self.play_btn.background_color = (0.2, 0.55, 0.2, 1)

    def _on_reset(self, inst):
        if not self.simulation:
            return

        new_cfg = {
            "simulation": {
                "dynamic_friction": self._params.get("dynamic_friction", 0.01),
                "softening_length": self._params.get("softening", 1.0),
            },
            "galaxies": {
                "total_particles": int(self._params.get("total_particles", 20000)),
                "mass_ratio": self._params.get("mass_ratio", 1.0),
                "total_mass": self._params.get("total_mass", 2.0),
            },
            "collision": {
                "initial_distance": self._params.get("initial_distance", 50.0),
                "velocity_factor": self._params.get("velocity_factor", 0.5),
                "impact_parameter": self._params.get("impact_parameter", 0.3),
                "inclination": self._params.get("inclination", 30.0),
            },
        }

        self.simulation.update_config(new_cfg)
        self.simulation.reset()

        self.play_btn.text = f"{S.PLAY} Start"
        self.play_btn.background_color = (0.2, 0.55, 0.2, 1)

    def _on_time(self, name, val):
        if self.simulation:
            self.simulation.set_time_scale(val)

    def _on_color(self, spin, text):
        mode_map = {
            "Galaxien": "distinct",
            "Realistisch": "realistic",
            "Geschwindigkeit": "velocity",
        }
        if self.color_mode_callback:
            self.color_mode_callback(mode_map.get(text, "distinct"))

    def _on_param(self, key, val):
        self._params[key] = val

    def update_stats(self, stats):
        t = stats.get("time", 0)
        d = stats.get("distance", 0)
        n = stats.get("particles", 0)
        ma = stats.get("mass_a", 1)
        mb = stats.get("mass_b", 1)

        self.stats_lbl.text = f"t={t:.1f} | d={d:.1f} | N={n}\nM: {ma:.2f}/{mb:.2f}"
