"""Statistics overlay for usage data from usage.jsonl."""

import json
from collections import defaultdict
from pathlib import Path

from kivy.graphics import Color, Rectangle, RoundedRectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from shared.fonts import get_safe_font
from shared.i18n import tr


def _load_usage_data():
    """Loads and aggregates usage.jsonl."""
    usage_file = Path.home() / ".local" / "share" / "astro_mini_games" / "usage.jsonl"
    if not usage_file.exists():
        return {}
    stats = defaultdict(lambda: {"count": 0, "duration": 0.0})
    try:
        with open(usage_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    app_id = entry.get("app_id", "unknown")
                    stats[app_id]["count"] += 1
                    stats[app_id]["duration"] += entry.get("duration_sec", 0)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return dict(stats)


def _format_duration_units(sec: float) -> str:
    """Format elapsed seconds with units (localized)."""
    total = max(0, int(round(float(sec))))
    if total < 60:
        return tr("stats.dur_seconds", n=total)
    minutes, s = divmod(total, 60)
    if minutes < 60:
        return tr("stats.dur_min_sec", m=minutes, s=s)
    h, m = divmod(minutes, 60)
    if m == 0 and s == 0:
        return tr("stats.dur_hours_only", h=h)
    if s == 0:
        return tr("stats.dur_hours_min", h=h, m=m)
    return tr("stats.dur_hour_min_sec", h=h, m=m, s=s)


def _starts_display(count: int) -> str:
    return tr("stats.starts_cell", n=count)


class StatsOverlay(FloatLayout):
    """Overlay with usage statistics. Close by tap outside or button."""

    def __init__(self, app_name_map=None, on_dismiss=None, **kwargs):
        super().__init__(**kwargs)
        self.app_name_map = app_name_map or {}
        self.on_dismiss_callback = on_dismiss
        self._build()

    def _make_label(self, text, *, header=False, halign="left", shorten=False):
        ft = get_safe_font()
        lbl = Label(
            text=text,
            font_name=ft,
            font_size="17sp" if header else "18sp",
            bold=bool(header),
            color=(0.94, 0.95, 1.0, 1),
            valign="middle",
            halign=halign,
            shorten=shorten,
            max_lines=2,
            size_hint_x=None,
            size_hint_y=1,
        )
        lbl.bind(size=lambda instance, _: setattr(instance, "text_size", (instance.width, None)))
        return lbl

    def _header_row(self) -> BoxLayout:
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(46),
            spacing=dp(12),
            padding=[dp(4), dp(8), dp(8), dp(8)],
        )
        c_app = self._make_label(tr("stats.col_app"), header=True, halign="left")
        c_app.size_hint_x = 0.50
        c_st = self._make_label(tr("stats.col_starts"), header=True, halign="right")
        c_st.size_hint_x = 0.22
        c_du = self._make_label(tr("stats.col_duration"), header=True, halign="right")
        c_du.size_hint_x = 0.28
        row.add_widget(c_app)
        row.add_widget(c_st)
        row.add_widget(c_du)
        return row

    def _data_row(self, name: str, count: int, duration_sec: float, *, stripe: bool) -> BoxLayout:
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(12),
            padding=[dp(4), dp(6), dp(8), dp(6)],
        )
        if stripe:
            with row.canvas.before:
                Color(0.08, 0.1, 0.16, 1)
                row._stripe = Rectangle(pos=row.pos, size=row.size)
            row.bind(
                pos=lambda *a: setattr(row._stripe, "pos", row.pos),
                size=lambda *a: setattr(row._stripe, "size", row.size),
            )

        lbl_n = self._make_label(name, halign="left", shorten=True)
        lbl_n.size_hint_x = 0.50
        lbl_n.color = (0.88, 0.90, 0.98, 1)

        lbl_c = self._make_label(_starts_display(count), halign="right")
        lbl_c.size_hint_x = 0.22

        lbl_d = self._make_label(_format_duration_units(duration_sec), halign="right")
        lbl_d.size_hint_x = 0.28

        row.add_widget(lbl_n)
        row.add_widget(lbl_c)
        row.add_widget(lbl_d)
        return row

    def _separator(self) -> Widget:
        line = Widget(size_hint_y=None, height=dp(2))
        with line.canvas.before:
            Color(0.38, 0.42, 0.55, 1)
            line._rect = Rectangle(pos=line.pos, size=line.size)
        line.bind(
            pos=lambda *a: setattr(line._rect, "pos", line.pos),
            size=lambda *a: setattr(line._rect, "size", line.size),
        )
        return line

    def _build(self):
        with self.canvas.before:
            Color(0, 0, 0, 0.88)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=self._on_size)
        self.bind(on_touch_down=self._on_touch)

        panel = FloatLayout(
            size_hint=(0.92, 0.82),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        with panel.canvas.before:
            Color(0.09, 0.1, 0.14, 0.98)
            panel._panel_bg = RoundedRectangle(
                pos=panel.pos,
                size=panel.size,
                radius=[dp(12)] * 4,
            )
        panel.bind(
            pos=lambda *a: setattr(panel._panel_bg, "pos", panel.pos),
            size=lambda *a: setattr(panel._panel_bg, "size", panel.size),
        )

        main_box = BoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            padding=dp(22),
            spacing=dp(14),
            pos_hint={"x": 0, "y": 0},
        )

        title = Label(
            text=tr("stats.title"),
            font_name=get_safe_font(),
            font_size="30sp",
            bold=True,
            color=(0.95, 0.96, 1.0, 1),
            size_hint_y=None,
            height=dp(52),
        )
        main_box.add_widget(title)

        scroll = ScrollView(
            size_hint_y=1,
            bar_width=dp(8),
            bar_color=(0.45, 0.5, 0.62, 0.55),
        )

        rows_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=0)
        rows_box.bind(minimum_height=rows_box.setter("height"))

        stats = _load_usage_data()
        if not stats:
            empty = Label(
                text=tr("stats.no_data"),
                font_name=get_safe_font(),
                font_size="20sp",
                color=(0.75, 0.78, 0.88, 1),
                size_hint_y=None,
                height=dp(52),
                halign="center",
            )
            empty.bind(size=lambda l, s: setattr(l, "text_size", (s[0], None)))
            rows_box.add_widget(empty)
        else:
            rows_box.add_widget(self._header_row())
            rows_box.add_widget(self._separator())
            for i, (app_id, data) in enumerate(
                sorted(stats.items(), key=lambda x: (-x[1]["duration"], x[0]))
            ):
                name = self.app_name_map.get(app_id, app_id)
                stripe = bool(i % 2)
                rows_box.add_widget(
                    self._data_row(
                        name,
                        data["count"],
                        data["duration"],
                        stripe=stripe,
                    )
                )

        scroll.add_widget(rows_box)
        main_box.add_widget(scroll)

        btn = Button(
            text=tr("stats.close"),
            font_name=get_safe_font(),
            font_size="18sp",
            size_hint_y=None,
            height=dp(52),
            background_color=(0.32, 0.36, 0.52, 0.95),
            background_normal="",
            on_release=lambda _: self._dismiss(),
        )
        main_box.add_widget(btn)

        panel.add_widget(main_box)
        self.add_widget(panel)

    def _on_size(self, instance, value):
        self._bg_rect.pos = instance.pos
        self._bg_rect.size = instance.size

    def _on_touch(self, instance, touch):
        if not instance.collide_point(*touch.pos) or touch.grab_current:
            return False
        for child in instance.children:
            try:
                lx, ly = child.to_widget(*touch.pos)
                if child.collide_point(lx, ly):
                    return False
            except Exception:
                pass
        self._dismiss()
        return True

    def _dismiss(self):
        if self.on_dismiss_callback:
            self.on_dismiss_callback()


class StatsTapArea(Widget):
    """Invisible area top center - 8x tap opens statistics overlay."""

    def __init__(self, on_activate=None, **kwargs):
        super().__init__(**kwargs)
        self.on_activate_callback = on_activate
        self._tap_times = []
        self._tap_window_sec = 3.0

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            import time

            now = time.time()
            self._tap_times.append(now)
            cutoff = now - self._tap_window_sec
            self._tap_times = [t for t in self._tap_times if t > cutoff]
            if len(self._tap_times) >= 8:
                self._tap_times.clear()
                if self.on_activate_callback:
                    self.on_activate_callback()
                return True
        return super().on_touch_down(touch)
