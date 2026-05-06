"""Slide-in panel with planet info."""

from datetime import date, datetime

from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from ui.theme import Colors, SPACING_MD, RADIUS_LG, MIN_TOUCH_TARGET
from ui.rounded_button import RoundedButton
from shared.i18n import tr

from simulation.planet_data import SEDNA_PERIHELION_AU, SEDNA_SEMI_MAJOR_AU


def _font():
    from shared.fonts import get_safe_font
    return get_safe_font()


def _planet_field(planet_name: str, field: str) -> str:
    return tr(f"sonnensystem_info.planet.{planet_name}.{field}")


def _planet_display_name(planet_name: str) -> str:
    key = f"sonnensystem_info.display_name.{planet_name}"
    s = tr(key)
    return planet_name if s == key else s


class InfoPanel(BoxLayout):
    """Slide-in panel with planet info."""

    def __init__(self, on_open_oort=None, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(None, 1),
            width=350,
            padding=SPACING_MD,
            spacing=SPACING_MD,
            **kwargs
        )
        self.pos_hint = {"right": 1, "top": 1}
        self._last_planet_name: str | None = None
        self._last_sim_date = None
        self._last_oort_reference_au: float | None = None
        self._on_open_oort = on_open_oort
        self.bind(parent=self._update_width)
        with self.canvas.before:
            Color(*Colors.BG_PANEL)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[RADIUS_LG] * 4)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.add_widget(Widget(size_hint_y=1))

        self._body = BoxLayout(
            orientation="vertical",
            spacing=6,
            size_hint_y=None,
        )
        self.label_name = Label(
            text="",
            font_name=_font(),
            font_size="26sp",
            bold=True,
            color=Colors.ACCENT,
            size_hint_y=None,
            height=40,
            halign="left",
            valign="bottom",
        )
        self.label_name.bind(
            size=lambda *x: setattr(self.label_name, "text_size", (self.label_name.width, None)),
            texture_size=lambda lbl, s: setattr(lbl, "height", max(40, s[1])),
        )
        self._body.add_widget(self.label_name)

        self._info_scroll = ScrollView(
            size_hint_y=None,
            height=dp(400),
            do_scroll_x=False,
            bar_width=8,
        )
        self.label_info = Label(
            text="",
            font_name=_font(),
            font_size="20sp",
            color=Colors.TEXT_SECONDARY,
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        self._info_scroll.bind(width=self._sync_info_text_width)
        self.label_info.bind(
            texture_size=lambda lbl, s: setattr(lbl, "height", max(s[1], 1)),
        )
        self._info_scroll.add_widget(self.label_info)
        self._body.add_widget(self._info_scroll)

        self._oort_link_btn = RoundedButton(
            text="",
            font_name=_font(),
            font_size="15sp",
            size_hint_y=None,
            height=0,
            opacity=0,
            disabled=True,
            background_color=Colors.ACCENT,
            color=Colors.TEXT_PRIMARY,
        )
        self._oort_link_btn.bind(on_release=self._on_oort_link_pressed)
        self._body.add_widget(self._oort_link_btn)

        self.label_sim_time = Label(
            text="",
            font_name=_font(),
            font_size="14sp",
            color=Colors.TEXT_SECONDARY,
            size_hint_y=None,
            height=24,
            halign="left",
        )
        self.label_sim_time.bind(
            size=lambda *x: setattr(self.label_sim_time, "text_size", (self.label_sim_time.width, None)),
        )
        self._body.add_widget(self.label_sim_time)

        self.add_widget(self._body)
        self.add_widget(Widget(size_hint_y=1))

        self._close_btn = Button(
            text=tr("sonnensystem_info.close"),
            font_name=_font(),
            font_size="20sp",
            size_hint_y=None,
            height=MIN_TOUCH_TARGET,
            background_color=Colors.BG_BUTTON,
            background_normal="",
        )
        self._close_btn.bind(on_release=lambda x: self.hide())
        self.add_widget(self._close_btn)
        self.opacity = 0
        self.disabled = True

    def apply_i18n(self):
        """Refresh strings after locale change (close button + visible panel only)."""
        self._close_btn.text = tr("sonnensystem_info.close")
        if (
            self._oort_link_btn.height > 1
            and self._oort_link_btn.opacity > 0.01
            and self._on_open_oort
        ):
            self._oort_link_btn.text = tr("sonnensystem.open_oort_view")
        if self._last_planet_name and self.opacity > 0.01:
            self._populate_content(self._last_planet_name, self._last_sim_date)

    def _on_oort_link_pressed(self, *_args):
        if self._on_open_oort:
            self._on_open_oort()
        self.hide()

    def _sync_info_text_width(self, *_args):
        w = self._info_scroll.width
        if w > 8:
            self.label_info.text_size = (w - 16, None)

    def _update_bg(self, *args):
        if hasattr(self, "_bg_rect"):
            self._bg_rect.pos = self.pos
            self._bg_rect.size = self.size

    def _update_width(self, *args):
        if self.parent and self.parent.width > 0:
            self.width = max(280, min(400, self.parent.width * 0.35))

    def _populate_content(self, planet_name: str, sim_date):
        desc = _planet_field(planet_name, "desc")
        desc_key = f"sonnensystem_info.planet.{planet_name}.desc"
        has_planet = desc != desc_key

        self.label_name.text = _planet_display_name(planet_name)
        key_labels = {
            "desc": "",
            "distance": tr("sonnensystem_info.label_distance"),
            "period": tr("sonnensystem_info.label_period"),
            "mass": tr("sonnensystem_info.label_mass"),
            "type": tr("sonnensystem_info.label_type"),
            "size": tr("sonnensystem_info.label_size"),
        }
        lines = []
        skip_oort_details = planet_name == "belt_oort"
        if has_planet:
            lines.append(desc)
            for k in ("distance", "period", "mass", "size", "type"):
                if skip_oort_details and k in ("period", "mass", "size"):
                    continue
                val = _planet_field(planet_name, k)
                field_key = f"sonnensystem_info.planet.{planet_name}.{k}"
                if val != field_key:
                    lines.append(key_labels[k] + val)

        if (
            has_planet
            and planet_name == "belt_oort"
            and self._last_oort_reference_au is not None
            and self._last_oort_reference_au > 0
        ):
            ref = float(self._last_oort_reference_au)

            def _nom_px(au: float, w: int, h: int) -> float:
                return au * 0.425 * min(w, h) / ref

            kw = {
                "ref_au": ref,
                "px50_fhd": _nom_px(50.0, 1920, 1080),
                "px50_qhd": _nom_px(50.0, 2560, 1440),
                "px_sedna_fhd": _nom_px(SEDNA_SEMI_MAJOR_AU, 1920, 1080),
                "px_sedna_qhd": _nom_px(SEDNA_SEMI_MAJOR_AU, 2560, 1440),
                "sedna_a": SEDNA_SEMI_MAJOR_AU,
                "sedna_q": SEDNA_PERIHELION_AU,
            }
            scale_key = "sonnensystem_info.planet.belt_oort.scale_nominal"
            scale_txt = tr(scale_key, **kw)
            if scale_txt != scale_key:
                lines.append(scale_txt)

        self.label_info.text = "\n\n".join(lines) if lines else tr("sonnensystem_info.no_data")
        self._sync_info_text_width()

        show_oort_link = (
            has_planet
            and planet_name == "belt_kuiper"
            and self._on_open_oort is not None
            and self._last_oort_link_available
        )
        if show_oort_link:
            self._oort_link_btn.text = tr("sonnensystem.open_oort_view")
            self._oort_link_btn.height = MIN_TOUCH_TARGET
            self._oort_link_btn.opacity = 1
            self._oort_link_btn.disabled = False
        else:
            self._oort_link_btn.text = ""
            self._oort_link_btn.height = 0
            self._oort_link_btn.opacity = 0
            self._oort_link_btn.disabled = True

        if sim_date is not None:
            fmt = tr("sonnensystem_info.sim_date_fmt")
            if isinstance(sim_date, datetime):
                d = sim_date.date()
            elif isinstance(sim_date, date):
                d = sim_date
            else:
                d = sim_date
            try:
                s = d.strftime(fmt)
            except (ValueError, TypeError):
                s = str(d)
            self.label_sim_time.text = tr("sonnensystem_info.sim_time", s=s)
        else:
            self.label_sim_time.text = ""

    def show(
        self,
        planet_name: str,
        sim_date=None,
        *,
        oort_link_available: bool = False,
        oort_reference_au: float | None = None,
    ):
        """Display planet info (name, description, distance, period, mass, etc.)."""
        self._last_planet_name = planet_name
        self._last_sim_date = sim_date
        self._last_oort_link_available = oort_link_available
        self._last_oort_reference_au = oort_reference_au
        self._populate_content(planet_name, sim_date)
        self.opacity = 1
        self.disabled = False

    def hide(self):
        """Fade out and disable the info panel."""
        anim = Animation(opacity=0, duration=0.2)
        anim.start(self)
        self.disabled = True
