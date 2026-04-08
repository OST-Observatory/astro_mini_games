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
from shared.i18n import tr


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
        self._last_planet_name: str | None = None
        self._last_sim_date = None
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
        if self._last_planet_name and self.opacity > 0.01:
            self._populate_content(self._last_planet_name, self._last_sim_date)

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
        if has_planet:
            lines.append(desc)
            for k in ("distance", "period", "mass", "size", "type"):
                val = _planet_field(planet_name, k)
                field_key = f"sonnensystem_info.planet.{planet_name}.{k}"
                if val != field_key:
                    lines.append(key_labels[k] + val)
        self.label_info.text = "\n\n".join(lines) if lines else tr("sonnensystem_info.no_data")
        self._sync_info_text_width()

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

    def show(self, planet_name: str, sim_date=None):
        """Display planet info (name, description, distance, period, mass, etc.)."""
        self._last_planet_name = planet_name
        self._last_sim_date = sim_date
        self._populate_content(planet_name, sim_date)
        self.opacity = 1
        self.disabled = False

    def hide(self):
        """Fade out and disable the info panel."""
        anim = Animation(opacity=0, duration=0.2)
        anim.start(self)
        self.disabled = True
