"""
Control panel with Unicode support.
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.button import Button
from ui.rounded_button import RoundedButton
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ObjectProperty
from kivy.app import App

from ui.fonts import get_font_name
from ui.symbols import S
from ui.material_icons import get_icon, get_icon_font
from ui.theme import Colors, SPACING_SM, SPACING_MD, SPACING_LG, RADIUS_MD, RADIUS_LG
from ui.theme import SLIDER_CURSOR_SIZE, SLIDER_PADDING, MIN_TOUCH_TARGET

from shared.i18n import tr


def _font():
    """Returns the current font name (dynamically)."""
    return get_font_name()


class ParamSlider(BoxLayout):
    """Parameter slider with Unicode labels - touch-optimized."""

    def __init__(self, label, min_v, max_v, default, step, fmt="{:.1f}", callback=None,
                 icon_text=None, icon_font=None, **kw):
        super().__init__(**kw)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = 68
        self.spacing = 6
        self.padding = [0, SLIDER_PADDING // 2]

        self.fmt = fmt
        self.callback = callback
        self.key = label

        row = BoxLayout(size_hint_y=0.5)

        if icon_text and icon_font:
            icon_lbl = Label(
                text=icon_text,
                font_name=icon_font,
                size_hint_x=None,
                width=24,
                font_size="18sp",
                color=Colors.TEXT_PRIMARY,
                halign="center",
            )
            row.add_widget(icon_lbl)

        self.lbl = Label(
            text=label,
            font_name=_font(),
            size_hint_x=1.0 if (icon_text and icon_font) else 0.6,
            size_hint_y=1.7,
            font_size="14sp",
            color=Colors.TEXT_PRIMARY,
            halign="left",
        )
        self.lbl.bind(size=lambda *x: setattr(self.lbl, "text_size", (self.lbl.width, None)))

        self.val_lbl = Label(
            text=fmt.format(default),
            font_name=_font(),
            size_hint_x=0.4,
            font_size="14sp",
            color=Colors.VALUE,
            halign="right",
        )
        self.val_lbl.bind(size=lambda *x: setattr(self.val_lbl, "text_size", (self.val_lbl.width, None)))

        row.add_widget(self.lbl)
        row.add_widget(self.val_lbl)

        self.slider = Slider(
            min=min_v,
            max=max_v,
            value=default,
            step=step,
            size_hint_y=0.5,
            value_track=True,
            value_track_color=list(Colors.SLIDER_TRACK),
            cursor_size=SLIDER_CURSOR_SIZE,
            padding=SLIDER_PADDING,
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
    """Control panel with Unicode symbols."""

    simulation = ObjectProperty(None)
    color_mode_callback = ObjectProperty(None)

    def __init__(self, simulation=None, config=None, use_drawer=False, drawer_width=320, **kwargs):
        self.simulation = simulation
        self.config = config or {}
        self.use_drawer = use_drawer
        super().__init__(**kwargs)

        self.orientation = "vertical"
        self.padding = [SPACING_MD, SPACING_MD]
        self.spacing = SPACING_SM
        self.size_hint_x = None
        self.width = drawer_width
        if not use_drawer:
            self.pos_hint = {"right": 1}

        self._params = {}
        self._sliders = {}  # key -> ParamSlider for preset updates
        self._pending_reset_changes = False  # Changes during simulation -> hint

        with self.canvas.before:
            Color(*Colors.BG_PANEL)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[RADIUS_LG])
        self.bind(pos=lambda *x: setattr(self.bg, "pos", self.pos),
                  size=lambda *x: setattr(self.bg, "size", self.size))

        self._build_ui()

    _SLIDER_I18N_KEYS = {
        "total_particles": "galaxy.particles",
        "mass_ratio": "galaxy.mass_ratio",
        "total_mass": "galaxy.total_mass",
        "initial_distance": "galaxy.distance",
        "velocity_factor": "galaxy.velocity",
        "impact_parameter": "galaxy.impact_param",
        "inclination": "galaxy.inclination",
        "dynamic_friction": "galaxy.friction",
        "softening": "galaxy.softening",
    }

    def apply_i18n(self):
        """Refresh all panel strings for the current locale."""
        self._title_row.text = f"{S.SETTINGS} {tr('galaxy.settings_title')}"
        self._sec_sim.text = S.section(tr("galaxy.section_sim_speed"))
        self.time_slider.lbl.text = tr("galaxy.speed")
        self._sec_color.text = S.section(tr("galaxy.section_coloring"))
        self._lbl_colors.text = f"{S.PALETTE} {tr('galaxy.colors_label')}"
        self._color_btns["distinct"].text = tr("galaxy.color_distinct")
        self._color_btns["realistic"].text = tr("galaxy.color_position")
        self._color_btns["velocity"].text = tr("galaxy.color_velocity")
        self._sec_presets.text = S.section(tr("galaxy.section_presets"))
        self._preset_btns["classic"].text = tr("galaxy.preset_classic")
        self._preset_btns["fast"].text = tr("galaxy.preset_fast")
        self._preset_btns["merge"].text = tr("galaxy.preset_merge")
        self._sec_galaxy.text = S.section(tr("galaxy.section_galaxy"))
        self._sec_collision.text = S.section(tr("galaxy.section_collision"))
        if getattr(self, "_sec_physics", None):
            self._sec_physics.text = S.section(tr("galaxy.section_physics"))
        for pkey, tr_key in self._SLIDER_I18N_KEYS.items():
            sl = self._sliders.get(pkey)
            if sl:
                sl.lbl.text = tr(tr_key)
        deg = S.DEGREE
        inc_sl = self._sliders.get("inclination")
        if inc_sl:
            inc_sl.fmt = "{:.0f}" + deg
        self._exit_btn.text = tr("galaxy.exit_launcher")
        self._update_hint(self._pending_reset_changes)

    def on_touch_down(self, touch):
        """Consume touches in settings area - prevents rotate/zoom on accidental tap."""
        if self.collide_point(*touch.pos):
            super().on_touch_down(touch)
            # Only grab when no child (e.g. slider) has already grabbed
            if touch.grab_current is None:
                touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            super().on_touch_move(touch)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            super().on_touch_up(touch)
            return True
        return super().on_touch_up(touch)

    def _lbl(self, **kwargs):
        """Create label with correct font."""
        kwargs['font_name'] = _font()
        return Label(**kwargs)

    def _btn(self, **kwargs):
        """Create RoundedButton with correct font and color scheme."""
        kwargs['font_name'] = _font()
        return RoundedButton(**kwargs)

    def _btn_rect(self, **kwargs):
        """Create rectangular button (for color chips, background color visible)."""
        kwargs['font_name'] = _font()
        return Button(**kwargs)

    def _build_ui(self):
        # Spacing between sections
        section_spacing = 15

        # Order: first added = TOP (Kivy BoxLayout). Spacer with size_hint_y=1
        # fills the middle, exit button stays at bottom.

        # === TOP: Title and content ===
        self._title_row = self._lbl(
            text=f"{S.SETTINGS} {tr('galaxy.settings_title')}",
            font_size="16sp",
            bold=True,
            size_hint_y=None,
            height=32,
            color=Colors.TEXT_PRIMARY,
        )
        self.add_widget(self._title_row)

        # === SIMULATIONSGESCHWINDIGKEIT ===
        self._sec_sim = self._lbl(
            text=S.section(tr("galaxy.section_sim_speed")),
            font_size="12sp",
            size_hint_y=None,
            height=24,
            color=Colors.ACCENT,
        )
        self.add_widget(self._sec_sim)
        ts_cfg = self.config.get("simulation", {}).get("time_scale", {})
        ts_default = ts_cfg.get("default", 1.0) if isinstance(ts_cfg, dict) else (ts_cfg or 1.0)
        ts_min = ts_cfg.get("min", 0.1) if isinstance(ts_cfg, dict) else 0.1
        ts_max = ts_cfg.get("max", 30.0) if isinstance(ts_cfg, dict) else 30.0
        ts_step = ts_cfg.get("step", 1.0) if isinstance(ts_cfg, dict) else 1.0
        self.time_slider = ParamSlider(
            tr("galaxy.speed"),
            ts_min, ts_max, ts_default, ts_step, "{:.1f}x",
            callback=self._on_time,
        )
        self.add_widget(self.time_slider)
        if self.simulation:
            self.simulation.set_time_scale(ts_default)

        self.add_widget(Widget(size_hint_y=None, height=section_spacing))

        # === FARBMODUS ===
        self._sec_color = self._lbl(
            text=S.section(tr("galaxy.section_coloring")),
            font_size="12sp",
            size_hint_y=None,
            height=24,
            color=Colors.ACCENT,
        )
        self.add_widget(self._sec_color)
        color_box = BoxLayout(
            size_hint_y=None,
            height=MIN_TOUCH_TARGET * 3,
            spacing=SPACING_SM,
            padding=[0, SPACING_SM],
        )
        self._lbl_colors = self._lbl(
            text=f"{S.PALETTE} {tr('galaxy.colors_label')}",
            size_hint_x=None,
            width=80,
            font_size="14sp",
            color=Colors.ACCENT,
        )
        color_box.add_widget(self._lbl_colors)
        chips_box = BoxLayout(orientation='vertical', spacing=SPACING_SM)
        self._color_btns = {}
        for label, mode in [
            (tr("galaxy.color_distinct"), "distinct"),
            (tr("galaxy.color_position"), "realistic"),
            (tr("galaxy.color_velocity"), "velocity"),
        ]:
            btn = self._btn_rect(
                text=label,
                font_size="12sp",
                background_color=Colors.BG_BUTTON,
                background_normal="",
                height=MIN_TOUCH_TARGET,
            )
            btn.mode = mode
            btn.label = label
            btn.bind(on_release=lambda b, m=mode: self._on_color_chip(m))
            self._color_btns[mode] = btn
            chips_box.add_widget(btn)
        self._color_mode = "distinct"
        self._update_color_chips()
        color_box.add_widget(chips_box)
        self.add_widget(color_box)

        self.add_widget(Widget(size_hint_y=None, height=section_spacing))

        # === VOREINSTELLUNGEN ===
        self._sec_presets = self._lbl(
            text=S.section(tr("galaxy.section_presets")),
            font_size="12sp",
            size_hint_y=None,
            height=24,
            color=Colors.ACCENT,
        )
        self.add_widget(self._sec_presets)
        presets_box = BoxLayout(
            size_hint_y=None,
            height=MIN_TOUCH_TARGET,
            spacing=SPACING_SM,
        )
        self._preset_btns = {}
        for label, preset_id in [
            (tr("galaxy.preset_classic"), "classic"),
            (tr("galaxy.preset_fast"), "fast"),
            (tr("galaxy.preset_merge"), "merge"),
        ]:
            btn = self._btn(
                text=label,
                font_size="12sp",
                background_color=Colors.ACCENT_DIM,
                background_normal="",
                height=MIN_TOUCH_TARGET,
            )
            btn.bind(on_release=lambda b, pid=preset_id: self._apply_preset(pid))
            self._preset_btns[preset_id] = btn
            presets_box.add_widget(btn)
        self.add_widget(presets_box)

        self.add_widget(Widget(size_hint_y=None, height=section_spacing))

        # === PARAMETER-BEREICH ===
        params = BoxLayout(orientation='vertical', size_hint_y=None, spacing=3, padding=[0, 5])
        params.bind(minimum_height=params.setter('height'))

        # Galaxies
        self._sec_galaxy = self._lbl(
            text=S.section(tr("galaxy.section_galaxy")),
            font_size="12sp",
            size_hint_y=None,
            height=24,
            color=Colors.ACCENT,
        )
        params.add_widget(self._sec_galaxy)

        gal = self.config.get("galaxies", {})
        m1, M1, d1, s1 = self._get_slider_cfg(gal, "total_particles", 5000, 30000, 20000, 5000)
        self._add_slider(params, tr("galaxy.particles"), m1, M1, d1, s1, "{:.0f}", "total_particles")
        m2, M2, d2, s2 = self._get_slider_cfg(gal, "mass_ratio", 0.2, 5.0, 1.0, 0.2)
        self._add_slider(params, tr("galaxy.mass_ratio"), m2, M2, d2, s2, "{:.1f}", "mass_ratio")
        m3, M3, d3, s3 = self._get_slider_cfg(gal, "total_mass", 1.0, 4.0, 2.0, 0.5)
        self._add_slider(params, tr("galaxy.total_mass"), m3, M3, d3, s3, "{:.1f}", "total_mass")

        params.add_widget(Widget(size_hint_y=None, height=section_spacing))

        # Collision
        self._sec_collision = self._lbl(
            text=S.section(tr("galaxy.section_collision")),
            font_size="12sp",
            size_hint_y=None,
            height=24,
            color=Colors.ACCENT,
        )
        params.add_widget(self._sec_collision)

        col = self.config.get("collision", {})
        m4, M4, d4, s4 = self._get_slider_cfg(col, "initial_distance", 30.0, 80.0, 50.0, 5.0)
        self._add_slider(params, tr("galaxy.distance"), m4, M4, d4, s4, "{:.0f}", "initial_distance")
        m5, M5, d5, s5 = self._get_slider_cfg(col, "velocity_factor", 0.2, 0.9, 0.5, 0.1)
        self._add_slider(params, tr("galaxy.velocity"), m5, M5, d5, s5, "{:.1f}", "velocity_factor")
        m6, M6, d6, s6 = self._get_slider_cfg(col, "impact_parameter", 0.0, 0.7, 0.3, 0.1)
        self._add_slider(params, tr("galaxy.impact_param"), m6, M6, d6, s6, "{:.1f}", "impact_parameter")
        m7, M7, d7, s7 = self._get_slider_cfg(col, "inclination", 0.0, 90.0, 30.0, 10.0)
        self._add_slider(params, tr("galaxy.inclination"), m7, M7, d7, s7, "{:.0f}" + S.DEGREE, "inclination")

        params.add_widget(Widget(size_hint_y=None, height=section_spacing))

        # Physics (optional, controlled via ui.show_physics_params)
        sim = self.config.get("simulation", {})
        ui_cfg = self.config.get("ui", {})
        show_physics = ui_cfg.get("show_physics_params", False)
        if show_physics:
            self._sec_physics = self._lbl(
                text=S.section(tr("galaxy.section_physics")),
                font_size="12sp",
                size_hint_y=None,
                height=24,
                color=Colors.ACCENT,
            )
            params.add_widget(self._sec_physics)
            m8, M8, d8, s8 = self._get_slider_cfg(sim, "dynamic_friction", 0.0, 0.05, 0.01, 0.005)
            self._add_slider(params, tr("galaxy.friction"), m8, M8, d8, s8, "{:.3f}", "dynamic_friction")
            m9, M9, d9, s9 = self._get_slider_cfg(sim, "softening_length", 0.5, 3.0, 1.0, 0.5)
            self._add_slider(params, tr("galaxy.softening"), m9, M9, d9, s9, "{:.1f}", "softening")
        else:
            self._sec_physics = None
            # Values from config for _apply_params (presets can still set them)
            _, _, d8, _ = self._get_slider_cfg(sim, "dynamic_friction", 0.0, 0.05, 0.01, 0.005)
            _, _, d9, _ = self._get_slider_cfg(sim, "softening_length", 0.5, 3.0, 1.0, 0.5)
            self._params["dynamic_friction"] = d8
            self._params["softening"] = d9

        params.add_widget(Widget(size_hint_y=None, height=section_spacing))

        # Hint (dynamic: immediate / reset needed) – text wraps as needed
        self._hint_lbl = self._lbl(
            text=f"{S.INFO} {tr('galaxy.hint_params')}",
            font_size="11sp",
            size_hint_y=None,
            height=24,
            color=Colors.TEXT_MUTED,
            halign="left",
            valign="top",
        )
        self._hint_lbl.bind(
            size=lambda lbl, sz: setattr(lbl, "text_size", (sz[0] - 4, None)),
            texture_size=lambda lbl, ts: setattr(lbl, "height", max(24, ts[1] + 4)),
        )
        params.add_widget(self._hint_lbl)

        self.add_widget(params)

        # Spacer: fills remaining space, pushes exit button to bottom
        self.add_widget(Widget(size_hint_y=1))

        # === BOTTOM: Close button and status label ===
        self._exit_btn = self._btn(
            text=tr("galaxy.exit_launcher"),
            font_size="14sp",
            size_hint_y=None,
            height=MIN_TOUCH_TARGET,
            background_color=Colors.DANGER,
            background_normal="",
        )
        self._exit_btn.bind(on_release=lambda x: App.get_running_app().stop())
        self.add_widget(self._exit_btn)

        self.stats_lbl = self._lbl(
            text="",
            font_size="12sp",
            size_hint_y=None,
            height=70,
            color=Colors.TEXT_SECONDARY,
        )
        self.add_widget(self.stats_lbl)

    def _on_color_chip(self, mode):
        self._color_mode = mode
        self._update_color_chips()
        if self.color_mode_callback:
            self.color_mode_callback(mode)

    def _update_color_chips(self):
        for mode, btn in self._color_btns.items():
            if mode == self._color_mode:
                btn.background_color = Colors.ACCENT
            else:
                btn.background_color = Colors.BG_BUTTON

    # Parameters that require a reset (galaxies/collision/physics)
    _RESET_PARAMS = frozenset({
        "total_particles", "mass_ratio", "total_mass",
        "initial_distance", "velocity_factor", "impact_parameter", "inclination",
        "dynamic_friction", "softening",
    })

    def _get_slider_cfg(self, section, key, min_d, max_d, default_d, step_d):
        """Get min, max, default, step from config (dict or scalar)."""
        cfg = section.get(key, default_d)
        if isinstance(cfg, dict):
            return (
                cfg.get("min", min_d),
                cfg.get("max", max_d),
                cfg.get("default", default_d),
                cfg.get("step", step_d),
            )
        return (min_d, max_d, cfg if cfg is not None else default_d, step_d)

    def _add_slider(self, container, label, min_v, max_v, default, step, fmt, key):
        slider = ParamSlider(
            label, min_v, max_v, default, step, fmt,
            callback=lambda n, v, k=key: self._on_param(k, v),
        )
        self._params[key] = default
        self._sliders[key] = slider
        container.add_widget(slider)

    def _apply_preset(self, preset_id):
        """Load preset parameters and perform reset."""
        presets = {
            "classic": {
                "total_particles": 20000,
                "mass_ratio": 1.0,
                "total_mass": 2.0,
                "initial_distance": 50.0,
                "velocity_factor": 0.5,
                "impact_parameter": 0.3,
                "inclination": 30.0,
                "dynamic_friction": 0.02,
                "softening": 1.0,
            },
            "fast": {
                "total_particles": 15000,
                "mass_ratio": 1.2,
                "total_mass": 2.0,
                "initial_distance": 40.0,
                "velocity_factor": 0.7,
                "impact_parameter": 0.2,
                "inclination": 45.0,
                "dynamic_friction": 0.01,
                "softening": 0.8,
            },
            "merge": {
                "total_particles": 25000,
                "mass_ratio": 0.8,
                "total_mass": 2.5,
                "initial_distance": 35.0,
                "velocity_factor": 0.4,
                "impact_parameter": 0.1,
                "inclination": 20.0,
                "dynamic_friction": 0.02,
                "softening": 1.2,
            },
        }
        p = presets.get(preset_id, presets["classic"])
        for key, val in p.items():
            self._params[key] = val
            if key in self._sliders:
                sl = self._sliders[key]
                sl.value = val
                sl.slider.value = val
                sl.val_lbl.text = sl.fmt.format(val)
        self._apply_params()

    def _apply_params(self):
        """Applies current parameters to simulation (update_config + reset)."""
        if not self.simulation:
            return

        new_cfg = {
            'simulation': {
                'dynamic_friction': self._params.get('dynamic_friction', 0.01),
                'softening_length': self._params.get('softening', 1.0),
            },
            'galaxies': {
                'total_particles': int(self._params.get('total_particles', 20000)),
                'mass_ratio': self._params.get('mass_ratio', 1.0),
                'total_mass': self._params.get('total_mass', 2.0),
            },
            'collision': {
                'initial_distance': self._params.get('initial_distance', 50.0),
                'velocity_factor': self._params.get('velocity_factor', 0.5),
                'impact_parameter': self._params.get('impact_parameter', 0.3),
                'inclination': self._params.get('inclination', 30.0),
            }
        }

        self.simulation.update_config(new_cfg)
        self.simulation.reset()
        self._pending_reset_changes = False
        self._update_hint(True)

        # Play-Button Sync
        app = App.get_running_app()
        if app and hasattr(app, "onscreen_controls") and app.onscreen_controls:
            app.onscreen_controls.update_play_button(True)

    def _on_reset(self, inst):
        """Reset button – applies parameters and restarts."""
        self._apply_params()

    def _update_hint(self, is_paused):
        """Updates the hint text depending on state."""
        if self._pending_reset_changes:
            self._hint_lbl.text = f"{S.WARNING} {tr('galaxy.hint_need_reset')}"
            self._hint_lbl.color = Colors.ACCENT
            self._hint_lbl.font_size = "14sp"
        else:
            self._hint_lbl.text = f"{S.INFO} {tr('galaxy.hint_live')}"
            self._hint_lbl.color = Colors.TEXT_MUTED
            self._hint_lbl.font_size = "11sp"
        # Update text_size for wrapping
        w = max(self._hint_lbl.width - 4, 50)
        self._hint_lbl.text_size = (w, None)

    def _on_time(self, name, val):
        if self.simulation:
            self.simulation.set_time_scale(val)

    def _on_param(self, key, val):
        self._params[key] = val

        if key not in self._RESET_PARAMS:
            return  # Time lapse, colors etc. – no reset required

        if self.simulation.paused:
            self._apply_params()
        else:
            self._pending_reset_changes = True
            self._update_hint(False)

    def update_stats(self, stats):
        """Updates the status display and hint."""
        self._update_hint(stats.get("paused", True))
        t = stats.get('time', 0)
        d = stats.get('distance', 0)
        n = stats.get('particles', 0)
        ma = stats.get('mass_a', 1)
        mb = stats.get('mass_b', 1)
        is_merged = stats.get('is_merged', False)
        merge_time = stats.get('merge_time')
        passages = stats.get('passages', 0)
        galaxy_count = stats.get('galaxy_count', 2)
        mean_radius = stats.get('mean_radius', 0)

        if galaxy_count == 1:
            # Single galaxy mode
            self.stats_lbl.color = Colors.ACCENT
            self.stats_lbl.text = (
                f"t={t:.1f} | N={n}\n"
                f"<r>={mean_radius:.2f}\n"
                f"M={ma:.2f}"
            )
        elif is_merged:
            # Merged
            self.stats_lbl.color = (0.8, 0.6, 0.9, 1)  # merged purple
            self.stats_lbl.text = (
                f"t={t:.1f} | N={n}\n"
                f"{S.STAR} {tr('galaxy.merged', t=merge_time)}\n"
                f"M={ma:.2f}"
            )
        else:
            # Two galaxies
            self.stats_lbl.color = Colors.TEXT_SECONDARY
            self.stats_lbl.text = (
                f"t={t:.1f} | d={d:.1f} | N={n}\n"
                f"{tr('galaxy.passages')} {passages}\n"
                f"M: {ma:.2f}/{mb:.2f}"
            )
