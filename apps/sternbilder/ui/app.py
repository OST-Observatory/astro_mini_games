"""Constellation finder main app."""

import random
from pathlib import Path

from shared.base_app import AstroApp
from shared.i18n import tr
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from star_map.data_loader import (
    load_constellations,
    load_config,
    get_session_constellations,
    format_constellation_name,
)
from star_map.hit_test import find_constellation_at
from shared.widgets.confetti import ConfettiOverlay
from ui.theme import Colors, MIN_TOUCH_TARGET, RADIUS_MD
from ui.rounded_button import RoundedButton
from visualization.renderer import StarMapRenderer
from ui.feedback_overlay import FeedbackOverlay


def _font():
    from shared.fonts import get_safe_font
    return get_safe_font()


def _style_icon_arrow_button(btn):
    """Center single-line arrow glyphs (Kivy Label defaults valign to 'bottom')."""
    btn.halign = "center"
    btn.valign = "middle"
    btn.padding = [0, 0, 0, 5]
    btn.bind(size=lambda inst, s: setattr(inst, "text_size", s))


class LearnSwipeLayer(Widget):
    """Full-area layer below other UI; horizontal swipe = next / previous page."""

    def __init__(self, on_swipe_next, on_swipe_prev, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self._on_swipe_next = on_swipe_next
        self._on_swipe_prev = on_swipe_prev
        self._start_x = None

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        self._start_x = touch.x
        touch.grab(self)
        return True

    def on_touch_move(self, touch):
        return touch.grab_current is self

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        if self._start_x is None:
            return True
        dx = touch.x - self._start_x
        self._start_x = None
        thr = dp(56)
        if dx < -thr:
            self._on_swipe_next()
        elif dx > thr:
            self._on_swipe_prev()
        return True


class SternbilderApp(AstroApp):
    """Constellation finder Kivy application."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen = "start"  # start | learn | quiz_choice | quiz_tap | quiz_mc
        self.learn_page = 0
        self.session_constellations = []
        self.quiz_variant = "tap"  # "tap" | "mc"
        self.quiz_target = None
        self.quiz_mc_options = []
        self.quiz_remaining = []
        self.quiz_wrong_attempts = 0
        self.points = 0
        self._widgets = {}

    def _apply_locale(self):
        super()._apply_locale()
        self._sync_sternbilder_texts()

    def _refresh_constellation_labels_for_locale(self):
        """Refresh constellation display strings after the UI language changes."""
        if getattr(self, "screen", None) == "learn" and self.session_constellations:
            self._update_learn_page()
        if (
            getattr(self, "screen", None) == "quiz_tap"
            and getattr(self, "quiz_target", None)
            and self.session_constellations
        ):
            c = load_constellations()
            display = format_constellation_name(c.get(self.quiz_target, {}))
            self.quiz_label.text = f"{tr('sternbilder.find_label')} {display}"
        if getattr(self, "screen", None) == "quiz_mc" and getattr(
            self, "quiz_mc_options", None
        ):
            c = load_constellations()
            for i, btn in enumerate(self._mc_buttons):
                if i < len(self.quiz_mc_options):
                    key = self.quiz_mc_options[i]
                    btn.text = format_constellation_name(c.get(key, {}))

    def _sync_sternbilder_texts(self):
        if getattr(self, "_sb_start_heading", None):
            self._sb_start_heading.text = tr("sternbilder.heading_learn")
            self._sb_start_intro.text = tr("sternbilder.intro")
            self._sb_learn_btn.text = tr("sternbilder.learn_tab")
            self._sb_quiz_btn.text = tr("sternbilder.to_quiz")
            self._sb_back_start.text = tr("sternbilder.back_launcher")
        if getattr(self, "_sb_quiz_title", None):
            self._sb_quiz_title.text = tr("sternbilder.quiz_heading")
            self._sb_quiz_intro.text = tr("sternbilder.quiz_intro")
            self._sb_mode_tap.text = tr("sternbilder.mode_map_tap")
            self._sb_mode_mc.text = tr("sternbilder.mode_mc")
            self._sb_back_quiz_choice.text = tr("sternbilder.back_launcher")
        if getattr(self, "_sb_quiz_end_home", None):
            self._sb_quiz_end_home.text = tr("sternbilder.back_home")
            self._sb_quiz_end_launcher.text = tr("sternbilder.back_launcher")
        if getattr(self, "_sb_swipe_hint", None):
            self._sb_swipe_hint.text = tr("sternbilder.swipe_hint")
        if getattr(self, "_sb_mode_tap2", None):
            self._sb_mode_tap2.text = tr("sternbilder.mode_map_tap")
            self._sb_mode_mc2.text = tr("sternbilder.mode_mc")
        self._refresh_constellation_labels_for_locale()

    def _get_config(self):
        cfg = load_config()
        session = cfg.get("session", {})
        return {
            "learn_count": session.get("learn_count", 7),
            "quiz_count": session.get("quiz_count", 7),
            "always_include_iau": session.get("always_include_iau", "Ursa Major"),
            "always_include": session.get("always_include"),
        }

    def build(self):
        """Build the constellation app UI: star map, screens, feedback overlay."""
        self.title = "Sternbilder"
        Window.bind(on_keyboard=self._on_keyboard)

        self.root = FloatLayout()
        with self.root.canvas.before:
            Color(*Colors.BG_VIEW)
            self._bg_rect = Rectangle(pos=self.root.pos, size=self.root.size)
        self.root.bind(size=self._update_bg)

        self.star_map = StarMapRenderer(size_hint=(1, 1), on_tap=self._on_tap)
        self.root.add_widget(self.star_map)

        self._build_feedback()
        self._build_start_screen()
        self._build_quiz_intro()
        self._build_quiz_end()
        self._build_learn_ui()
        self._build_quiz_ui()

        self._show_screen("start")
        return self.root

    def _build_start_screen(self):
        layout = FloatLayout(size_hint=(1, 1))

        self._sb_start_heading = Label(
            text=tr("sternbilder.heading_learn"),
            font_name=_font(),
            font_size="50sp",
            bold=True,
            color=Colors.TEXT_PRIMARY,
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "top": 0.9},
        )
        self._sb_start_heading.bind(texture_size=self._sb_start_heading.setter("size"))
        layout.add_widget(self._sb_start_heading)

        scroll = ScrollView(size_hint=(0.55, 0.4), pos_hint={"center_x": 0.5, "top": 0.84})
        self._sb_start_intro = Label(
            text=tr("sternbilder.intro"),
            font_name=_font(),
            font_size="25sp",
            color=Colors.TEXT_PRIMARY,
            size_hint=(1, None),
            halign="center",
            valign="middle",
        )
        self._sb_start_intro.bind(
            texture_size=lambda lbl, val: setattr(lbl, "height", val[1] + 40),
            size=lambda lbl, val: setattr(lbl, "text_size", (val[0], None)),
        )
        scroll.add_widget(self._sb_start_intro)
        layout.add_widget(scroll)

        self._sb_learn_btn = RoundedButton(
            text=tr("sternbilder.learn_tab"),
            font_name=_font(),
            font_size="35sp",
            bold=True,
            size_hint=(0.5, 0.1),
            pos_hint={"center_x": 0.5, "center_y": 0.45},
            background_color=Colors.ACCENT,
            background_normal="",
        )
        self._sb_learn_btn.bind(on_release=self._start_learn)
        layout.add_widget(self._sb_learn_btn)

        self._sb_quiz_btn = RoundedButton(
            text=tr("sternbilder.to_quiz"),
            font_name=_font(),
            font_size="35sp",
            bold=True,
            size_hint=(0.5, 0.1),
            pos_hint={"center_x": 0.5, "center_y": 0.32},
            background_color=Colors.BG_BUTTON,
            background_normal="",
        )
        self._sb_quiz_btn.bind(on_release=self._go_quiz_intro_from_start)
        layout.add_widget(self._sb_quiz_btn)

        self._sb_back_start = RoundedButton(
            text=tr("sternbilder.back_launcher"),
            font_name=_font(),
            font_size="16sp",
            size_hint=(0.5, 0.08),
            pos_hint={"center_x": 0.5, "bottom": 0.04},
            background_color=Colors.BG_BUTTON,
        )
        self._sb_back_start.bind(on_release=lambda x: self.stop())
        layout.add_widget(self._sb_back_start)

        self._widgets["start"] = layout

    def _build_quiz_intro(self):
        """Explanation of quiz modes between learn mode and quiz."""
        layout = FloatLayout(size_hint=(1, 1))

        self._sb_quiz_title = Label(
            text=tr("sternbilder.quiz_heading"),
            font_name=_font(),
            font_size="40sp",
            bold=True,
            color=Colors.TEXT_PRIMARY,
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "top": 0.92},
        )
        self._sb_quiz_title.bind(texture_size=self._sb_quiz_title.setter("size"))
        layout.add_widget(self._sb_quiz_title)

        scroll = ScrollView(size_hint=(0.7, 0.45), pos_hint={"center_x": 0.5, "top": 0.82})
        self._sb_quiz_intro = Label(
            text=tr("sternbilder.quiz_intro"),
            font_name=_font(),
            font_size="25sp",
            color=Colors.TEXT_PRIMARY,
            size_hint=(1, None),
            halign="left",
            valign="middle",
        )
        self._sb_quiz_intro.bind(
            texture_size=lambda lbl, val: setattr(lbl, "height", val[1] + 40),
            size=lambda lbl, val: setattr(lbl, "text_size", (val[0], None)),
        )
        scroll.add_widget(self._sb_quiz_intro)
        layout.add_widget(scroll)

        self._sb_mode_tap = RoundedButton(
            text=tr("sternbilder.mode_map_tap"),
            font_name=_font(),
            font_size="35sp",
            size_hint=(0.7, 0.1),
            pos_hint={"center_x": 0.5, "center_y": 0.32},
            bold=True,
            background_color=Colors.ACCENT,
            background_normal="",
        )
        self._sb_mode_tap.bind(on_release=lambda x: self._start_quiz_from_intro("tap"))
        layout.add_widget(self._sb_mode_tap)

        self._sb_mode_mc = RoundedButton(
            text=tr("sternbilder.mode_mc"),
            font_name=_font(),
            font_size="35sp",
            size_hint=(0.7, 0.1),
            pos_hint={"center_x": 0.5, "center_y": 0.18},
            bold=True,
            background_color=Colors.ACCENT_2,
            background_normal="",
        )
        self._sb_mode_mc.bind(on_release=lambda x: self._start_quiz_from_intro("mc"))
        layout.add_widget(self._sb_mode_mc)

        self._sb_back_quiz_choice = RoundedButton(
            text=tr("sternbilder.back_launcher"),
            font_name=_font(),
            font_size="16sp",
            size_hint=(0.5, 0.08),
            pos_hint={"center_x": 0.5, "bottom": 0.04},
            background_color=Colors.BG_BUTTON,
        )
        self._sb_back_quiz_choice.bind(on_release=lambda x: self.stop())
        layout.add_widget(self._sb_back_quiz_choice)

        self._widgets["quiz_intro"] = layout

    def _build_quiz_end(self):
        """Quiz finished - show points."""
        layout = FloatLayout(size_hint=(1, 1))

        self._quiz_end_label = Label(
            text="",
            font_name=_font(),
            font_size="24sp",
            color=Colors.TEXT_PRIMARY,
            size_hint=(0.9, None),
            pos_hint={"center_x": 0.5, "center_y": 0.55},
            halign="center",
        )
        self._quiz_end_label.bind(texture_size=self._quiz_end_label.setter("size"))
        layout.add_widget(self._quiz_end_label)

        self._sb_quiz_end_home = RoundedButton(
            text=tr("sternbilder.back_home"),
            font_name=_font(),
            font_size="35sp",
            bold=True,
            size_hint=(0.5, 0.1),
            pos_hint={"center_x": 0.5, "center_y": 0.35},
            background_color=Colors.ACCENT,
            background_normal="",
        )
        self._sb_quiz_end_home.bind(on_release=lambda x: self._show_screen("start"))
        layout.add_widget(self._sb_quiz_end_home)

        self._sb_quiz_end_launcher = RoundedButton(
            text=tr("sternbilder.back_launcher"),
            font_name=_font(),
            font_size="16sp",
            size_hint=(0.5, 0.08),
            pos_hint={"center_x": 0.5, "bottom": 0.04},
            background_color=Colors.BG_BUTTON,
        )
        self._sb_quiz_end_launcher.bind(on_release=lambda x: self.stop())
        layout.add_widget(self._sb_quiz_end_launcher)

        self._widgets["quiz_end"] = layout

    def _show_quiz_end(self):
        """Show quiz finished."""
        total = len(self.session_constellations)
        if self.quiz_variant == "tap":
            max_points = total * (total + 1) // 2  # 7+6+5+...+1
        else:
            max_points = total * 3
        lines = [
            tr("sternbilder.quiz_done_title"),
            "",
            tr("sternbilder.quiz_score", points=self.points, max_points=max_points),
            tr("sternbilder.quiz_all_found", n=total),
        ]
        if self.quiz_wrong_attempts > 0:
            wk = "sternbilder.quiz_wrong_many" if self.quiz_wrong_attempts > 1 else "sternbilder.quiz_wrong_one"
            lines.append(tr(wk, n=self.quiz_wrong_attempts))
        self._quiz_end_label.text = "\n".join(lines)
        self._quiz_end_label.size_hint_x = 0.9
        self.star_map.opacity = 0
        self._show_screen("quiz_end")
        self._start_quiz_end_confetti(max_points)

    def _start_quiz_end_confetti(self, max_points: int) -> None:
        layout = self._widgets["quiz_end"]
        for w in list(layout.children):
            if isinstance(w, ConfettiOverlay):
                layout.remove_widget(w)
        if max_points <= 0:
            return
        ratio = self.points / max_points
        if ratio < 0.3:
            return
        confetti = ConfettiOverlay(on_done=None)
        layout.add_widget(confetti)
        confetti.start(ratio=max(0.3, min(1.0, ratio)))

    def _build_learn_ui(self):
        layout = FloatLayout(size_hint=(1, 1))

        learn_swipe = LearnSwipeLayer(
            on_swipe_next=self._learn_next,
            on_swipe_prev=self._learn_back,
        )
        layout.add_widget(learn_swipe)

        title = Label(
            text="",
            font_name=_font(),
            font_size="35sp",
            bold=True,
            color=Colors.TEXT_PRIMARY,
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "top": 0.96},
        )
        title.bind(texture_size=title.setter("size"))
        layout.add_widget(title)
        self._learn_title = title

        note = Label(
            text="",
            font_name=_font(),
            font_size="25sp",
            color=Colors.TEXT_SECONDARY,
            size_hint=(0.85, None),
            pos_hint={"center_x": 0.5, "top": 0.90},
            halign="center",
        )
        note.bind(texture_size=lambda l, v: setattr(l, "height", max(v[1] + 10, 20)))
        layout.add_widget(note)
        self._learn_note = note

        nav_btn_size = max(MIN_TOUCH_TARGET + 24, int(dp(72)))
        back_btn = RoundedButton(
            text="◀",
            font_name=_font(),
            font_size="42sp",
            bold=True,
            size_hint=(None, None),
            size=(nav_btn_size, nav_btn_size),
            pos_hint={"x": 0.02, "center_y": 0.5},
            background_color=Colors.BG_BUTTON,
        )
        back_btn.bind(on_release=self._learn_back)
        _style_icon_arrow_button(back_btn)
        layout.add_widget(back_btn)
        self._learn_back_btn = back_btn

        next_btn = RoundedButton(
            text="▶",
            font_name=_font(),
            font_size="42sp",
            bold=True,
            size_hint=(None, None),
            size=(nav_btn_size, nav_btn_size),
            pos_hint={"right": 0.98, "center_y": 0.5},
            background_color=Colors.ACCENT,
        )
        next_btn.bind(on_release=self._learn_next)
        _style_icon_arrow_button(next_btn)
        layout.add_widget(next_btn)
        self._learn_next_btn = next_btn

        self._sb_swipe_hint = Label(
            text=tr("sternbilder.swipe_hint"),
            font_name=_font(),
            font_size="12sp",
            color=Colors.TEXT_SECONDARY,
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "bottom": 0.12},
        )
        self._sb_swipe_hint.bind(texture_size=self._sb_swipe_hint.setter("size"))
        layout.add_widget(self._sb_swipe_hint)

        self._widgets["learn"] = layout

    def _build_quiz_ui(self):
        layout = FloatLayout(size_hint=(1, 1))

        quiz_label_box = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "top": 0.95},
            padding=(30, 16),
        )

        def _update_quiz_box_bg(inst, val):
            quiz_label_box._bg_rect.pos = inst.pos
            quiz_label_box._bg_rect.size = inst.size

        with quiz_label_box.canvas.before:
            Color(*Colors.BG_PANEL)
            quiz_label_box._bg_rect = RoundedRectangle(
                pos=quiz_label_box.pos,
                size=quiz_label_box.size,
                radius=[RADIUS_MD, RADIUS_MD, RADIUS_MD, RADIUS_MD],
            )
        quiz_label_box.bind(pos=_update_quiz_box_bg, size=_update_quiz_box_bg)

        def _on_quiz_label_texture(inst, val):
            inst.size = val
            quiz_label_box.size = (val[0] + 60, val[1] + 32)

        self.quiz_label = Label(
            text="",
            font_name=_font(),
            font_size="32sp",
            bold=True,
            color=Colors.ACCENT,
            size_hint=(None, None),
            halign="center",
        )
        self.quiz_label.bind(texture_size=_on_quiz_label_texture)
        quiz_label_box.add_widget(self.quiz_label)
        layout.add_widget(quiz_label_box)
        self._quiz_label_box = quiz_label_box

        self._quiz_variant_box = BoxLayout(
            orientation="horizontal",
            size_hint=(0.9, 0.08),
            pos_hint={"center_x": 0.5, "bottom": 0.02},
            spacing=15,
        )
        self._sb_mode_tap2 = RoundedButton(
            text=tr("sternbilder.mode_map_tap"),
            font_name=_font(),
            size_hint_x=None,
            width=160,
            background_color=Colors.BG_BUTTON,
            background_normal="",
        )
        self._sb_mode_tap2.bind(on_release=lambda x: self._set_quiz_variant("tap"))
        self._sb_mode_mc2 = RoundedButton(
            text=tr("sternbilder.mode_mc"),
            font_name=_font(),
            size_hint_x=None,
            width=160,
            background_color=Colors.BG_BUTTON,
            background_normal="",
        )
        self._sb_mode_mc2.bind(on_release=lambda x: self._set_quiz_variant("mc"))
        self._quiz_variant_box.add_widget(self._sb_mode_tap2)
        self._quiz_variant_box.add_widget(self._sb_mode_mc2)
        layout.add_widget(self._quiz_variant_box)
        self._quiz_tap_btn = self._sb_mode_tap2
        self._quiz_mc_btn = self._sb_mode_mc2

        mc_options = BoxLayout(
            orientation="vertical",
            size_hint=(0.25, 0.25),
            pos_hint={"center_x": 0.5, "bottom": 0.14},
            spacing=10,
        )
        self._mc_buttons = []
        for i in range(3):
            btn = RoundedButton(
                text="",
                font_name=_font(),
                font_size="16sp",
                size_hint_y=None,
                height=MIN_TOUCH_TARGET,
                background_color=Colors.BG_BUTTON,
            )
            btn.bind(on_release=lambda b, idx=i: self._on_mc_choice(idx))
            mc_options.add_widget(btn)
            self._mc_buttons.append(btn)
        layout.add_widget(mc_options)
        self._mc_options_box = mc_options

        self._widgets["quiz_choice"] = layout
        self._widgets["quiz_tap"] = layout
        self._widgets["quiz_mc"] = layout

    def _build_feedback(self):
        self.feedback = FeedbackOverlay()

    def _update_bg(self, instance, value):
        self._bg_rect.pos = instance.pos
        self._bg_rect.size = instance.size

    def _show_screen(self, name: str):
        """Show only the given screen (quiz app pattern: clear + add)."""
        self.screen = name

        for child in self.root.children[:]:
            if child is self.star_map or child is self.feedback:
                continue
            if self._keep_when_clearing_root_overlays(child):
                continue
            self.root.remove_widget(child)

        overlay = self._widgets.get(name)
        if overlay and overlay not in self.root.children:
            self.root.add_widget(overlay)

        self.star_map.opacity = 0 if name in ("start", "quiz_intro", "quiz_end") else 1
        self.star_map.bottom_reserve_fraction = 0.0
        self.star_map.top_reserve_fraction = 0.0
        if name in ("start", "quiz_intro", "quiz_end"):
            self.star_map.display_only_constellation = None
            self.star_map.highlight_asterism_pairs = False
            if name == "start":
                self.star_map.session_constellations = None

        if name == "learn":
            self._update_learn_page()
        elif name in ("quiz_tap", "quiz_mc"):
            self._update_quiz_variant_buttons()
            self._quiz_variant_box.opacity = 0
            self.star_map.bottom_reserve_fraction = 0.15 if name == "quiz_mc" else 0.0
            self.star_map.top_reserve_fraction = 0.05 if name == "quiz_tap" else 0.0
            if name == "quiz_tap":
                self._quiz_label_box.opacity = 1
                self._mc_options_box.opacity = 0
            else:
                self._quiz_label_box.opacity = 0
                self._mc_options_box.opacity = 1
        elif name == "quiz_choice":
            self._quiz_label_box.opacity = 0
            self._quiz_variant_box.opacity = 0
            self._mc_options_box.opacity = 0

        self.ensure_lang_switcher_on_top()
        self.star_map._draw()

    def _start_learn(self, *args):
        cfg = self._get_config()
        self.session_constellations = get_session_constellations(
            cfg["learn_count"],
            cfg.get("always_include"),
            cfg.get("always_include_iau"),
        )
        self.learn_page = 0
        self.star_map.session_constellations = self.session_constellations
        self._show_screen("learn")

    def _update_learn_page(self):
        if not self.session_constellations:
            return
        idx = self.learn_page
        const_key = self.session_constellations[idx]
        constellations = load_constellations()
        const_data = constellations.get(const_key, {})

        display = format_constellation_name(const_data)
        self._learn_title.text = display

        if const_key == "Große Bärin":
            self._learn_note.text = tr("sternbilder.big_dipper_note")
            self._learn_note.opacity = 1
        else:
            self._learn_note.text = ""
            self._learn_note.opacity = 0

        self._learn_back_btn.text = "◀"
        self._learn_next_btn.text = "▶"

        self.star_map.display_only_constellation = const_key
        self.star_map.highlight_asterism_pairs = const_key == "Große Bärin"
        self.star_map.highlighted_constellation = None
        self.star_map._draw()

    def _learn_back(self, *args):
        if self.learn_page > 0:
            self.learn_page -= 1
            self._update_learn_page()
        else:
            self._show_screen("start")

    def _learn_next(self, *args):
        if self.learn_page < len(self.session_constellations) - 1:
            self.learn_page += 1
            self._update_learn_page()
        else:
            self._show_quiz_intro()

    def _show_quiz_intro(self):
        """After learn mode: intro with quiz explanation, keeps session_constellations."""
        self.star_map.display_only_constellation = None
        self.star_map.highlight_asterism_pairs = False
        self.star_map.opacity = 0
        self._show_screen("quiz_intro")

    def _go_quiz_intro_from_start(self, *args):
        """From start screen: load session and show quiz intro."""
        cfg = self._get_config()
        self.session_constellations = get_session_constellations(
            cfg["quiz_count"],
            cfg.get("always_include"),
            cfg.get("always_include_iau"),
        )
        self.star_map.session_constellations = self.session_constellations
        self._show_quiz_intro()

    def _start_quiz_from_intro(self, variant: str):
        """From quiz intro: choose variant and start quiz."""
        self.quiz_variant = variant
        self.quiz_remaining = list(self.session_constellations)
        random.shuffle(self.quiz_remaining)
        self.points = 0
        self.quiz_wrong_attempts = 0
        self.star_map.display_only_constellation = None
        self.star_map.highlight_asterism_pairs = False
        self.star_map.session_constellations = self.session_constellations
        if variant == "tap":
            self._start_quiz_tap()
        else:
            self._start_quiz_mc()

    def _set_quiz_variant(self, variant: str):
        self.quiz_variant = variant
        if variant == "tap":
            self._start_quiz_tap()
        else:
            self._start_quiz_mc()

    def _start_quiz_tap(self):
        if not self.quiz_remaining:
            self._show_quiz_end()
            return
        self.quiz_points_this_question = len(self.quiz_remaining)  # 7, 6, 5, ...
        self._wrong_attempts_this_question = 0
        self.quiz_target = self.quiz_remaining.pop()
        constellations = load_constellations()
        display = format_constellation_name(constellations.get(self.quiz_target, {}))
        self.quiz_label.text = f"{tr('sternbilder.find_label')} {display}"
        self.star_map.highlighted_constellation = None
        self._show_screen("quiz_tap")

    def _start_quiz_mc(self):
        if not self.quiz_remaining:
            self._show_quiz_end()
            return
        self.quiz_points_this_question = 3
        self._wrong_attempts_this_question = 0
        self.quiz_target = self.quiz_remaining.pop()
        constellations = load_constellations()
        others = [c for c in self.session_constellations if c != self.quiz_target]
        wrong = random.sample(others, min(2, len(others)))
        options = [self.quiz_target] + wrong
        random.shuffle(options)
        self.quiz_mc_options = options

        for i, btn in enumerate(self._mc_buttons):
            if i < len(options):
                key = options[i]
                btn.text = format_constellation_name(constellations.get(key, {}))
                btn.opacity = 1
                btn.disabled = False
            else:
                btn.text = ""
                btn.opacity = 0
                btn.disabled = True

        self.star_map.highlighted_constellation = self.quiz_target
        self._show_screen("quiz_mc")

    def _update_quiz_variant_buttons(self):
        tap_color = Colors.ACCENT if self.quiz_variant == "tap" else Colors.BG_BUTTON
        mc_color = Colors.ACCENT if self.quiz_variant == "mc" else Colors.BG_BUTTON
        self._quiz_tap_btn.set_display_color(tap_color)
        self._quiz_mc_btn.set_display_color(mc_color)

    def _on_tap(self, x, y):
        const = find_constellation_at(
            self.star_map.stars,
            self.star_map.constellations,
            self.star_map.stars_by_id,
            x, y,
            self.star_map.screen_coords,
            const_filter=self.session_constellations if self.session_constellations else None,
        )
        if const and self.screen == "quiz_tap":
            self.star_map.highlighted_constellation = const
            self.star_map._draw()
            if const == self.quiz_target:
                self.points += max(0, self.quiz_points_this_question - self._wrong_attempts_this_question)
                constellations = load_constellations()
                display = format_constellation_name(constellations.get(const, {}))
                if self.feedback not in self.root.children:
                    self.root.add_widget(self.feedback)
                self.feedback.show_correct(display)
                self._next_quiz_after_feedback()
            else:
                self.quiz_wrong_attempts += 1
                self._wrong_attempts_this_question += 1
                constellations = load_constellations()
                display = format_constellation_name(constellations.get(const, {}))
                if self.feedback not in self.root.children:
                    self.root.add_widget(self.feedback)
                self.feedback.show_wrong(display)

    def _on_mc_choice(self, idx: int):
        if idx >= len(self.quiz_mc_options):
            return
        chosen = self.quiz_mc_options[idx]
        constellations = load_constellations()
        display = format_constellation_name(constellations.get(chosen, {}))
        if self.feedback not in self.root.children:
            self.root.add_widget(self.feedback)
        if chosen == self.quiz_target:
            self.points += max(0, 3 - self._wrong_attempts_this_question)
            self.feedback.show_correct(display)
            self._next_quiz_after_feedback()
        else:
            self.quiz_wrong_attempts += 1
            self._wrong_attempts_this_question += 1
            self.feedback.show_wrong(display)

    def _next_quiz_after_feedback(self):
        def _after_feedback(*args):
            if self.quiz_variant == "tap":
                self._start_quiz_tap()
            else:
                self._start_quiz_mc()

        from kivy.clock import Clock
        Clock.schedule_once(_after_feedback, 1.8)

    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:
            if self.screen == "start":
                self.stop()
            elif self.screen == "learn":
                self._show_screen("start")
            elif self.screen in ("quiz_intro", "quiz_end"):
                self._show_screen("start")
            elif self.screen in ("quiz_tap", "quiz_mc"):
                self._show_screen("start")
            return True
        return False
