"""Statistics overlay for usage data from usage.jsonl."""

import json
from collections import defaultdict
from pathlib import Path

from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

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


def _format_duration(sec):
    """Formats seconds as mm:ss."""
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m}:{s:02d}"


class StatsOverlay(FloatLayout):
    """Overlay with usage statistics. Close by tap outside or button."""

    def __init__(self, app_name_map=None, on_dismiss=None, **kwargs):
        super().__init__(**kwargs)
        self.app_name_map = app_name_map or {}
        self.on_dismiss_callback = on_dismiss
        self._build()

    def _build(self):
        with self.canvas.before:
            Color(0, 0, 0, 0.85)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=self._on_size)
        self.bind(on_touch_down=self._on_touch)

        main_box = BoxLayout(
            orientation="vertical",
            size_hint=(0.9, 0.85),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            padding=20,
            spacing=10,
        )

        title = Label(
            text=tr("stats.title"),
            font_size="28sp",
            size_hint_y=None,
            height=50,
        )
        main_box.add_widget(title)

        scroll = ScrollView(size_hint_y=1)
        content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=5)
        content.bind(minimum_height=content.setter("height"))

        stats = _load_usage_data()
        if not stats:
            content.add_widget(
                Label(text=tr("stats.no_data"), font_size="18sp", size_hint_y=None, height=40)
            )
        else:
            for app_id, data in sorted(stats.items(), key=lambda x: -x[1]["duration"]):
                name = self.app_name_map.get(app_id, app_id)
                count = data["count"]
                dur = _format_duration(data["duration"])
                row = Label(
                    text=f"{name}: {count}×, {dur}",
                    font_size="18sp",
                    size_hint_y=None,
                    height=35,
                )
                content.add_widget(row)

        scroll.add_widget(content)
        main_box.add_widget(scroll)

        btn = Button(
            text=tr("stats.close"),
            size_hint_y=None,
            height=50,
            on_release=lambda _: self._dismiss(),
        )
        main_box.add_widget(btn)

        self.add_widget(main_box)

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
