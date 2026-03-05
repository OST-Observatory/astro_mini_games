"""Constellation finder main app."""

import random
from pathlib import Path

from shared.base_app import AstroApp
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from star_map.data_loader import (
    load_constellations,
    load_config,
    get_session_constellations,
    format_constellation_name,
)
from star_map.hit_test import find_constellation_at
from ui.theme import Colors, MIN_TOUCH_TARGET, RADIUS_MD
from ui.rounded_button import RoundedButton
from visualization.renderer import StarMapRenderer
from ui.feedback_overlay import FeedbackOverlay


INTRO_TEXT = (
    "Sternbilder werden je nach Kultur unterschiedlich gedeutet. "
    "Diese App zeigt die von der Internationalen Astronomischen Union (IAU) "
    "offiziell festgelegten Sternbilder am nördlichen Nachthimmel. "
    "Lerne sie kennen und teste dein Wissen im Quiz."
)

BIG_DIPPER_NOTE = (
    "Der Große Wagen ist lediglich ein Teil des Sternbildes Große Bärin."
)

QUIZ_INTRO_TEXT = (
    "Jetzt kannst du dein Wissen testen! Wähle einen Quiz-Modus:\n\n"
    "• Auf Karte tippen: Du siehst den Namen eines Sternbilds und tippst es auf der Sternenkarte an.\n\n"
    "• Multiple Choice: Ein Sternbild wird hervorgehoben. Wähle den richtigen Namen aus drei Antwortmöglichkeiten."
)


def _font():
    from shared.fonts import get_safe_font
    return get_safe_font()


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

    def _get_config(self):
        cfg = load_config()
        session = cfg.get("session", {})
        return {
            "learn_count": session.get("learn_count", 7),
            "quiz_count": session.get("quiz_count", 7),
            "always_include": session.get("always_include", "Große Bärin (Ursa Major)"),
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

        heading = Label(
            text="Sternbilder entdecken",
            font_name=_font(),
            font_size="50sp",
            bold=True,
            color=Colors.TEXT_PRIMARY,
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "top": 0.9},
        )
        heading.bind(texture_size=heading.setter("size"))
        layout.add_widget(heading)

        scroll = ScrollView(size_hint=(0.55, 0.4), pos_hint={"center_x": 0.5, "top": 0.84})
        intro = Label(
            text=INTRO_TEXT,
            font_name=_font(),
            font_size="25sp",
            color=Colors.TEXT_PRIMARY,
            size_hint=(1, None),
            halign="center",
            valign="middle",
        )
        intro.bind(
            texture_size=lambda lbl, val: setattr(lbl, "height", val[1] + 40),
            size=lambda lbl, val: setattr(lbl, "text_size", (val[0], None)),
        )
        scroll.add_widget(intro)
        layout.add_widget(scroll)

        learn_btn = RoundedButton(
            text="Sternbilder kennen lernen",
            font_name=_font(),
            font_size="35sp",
            bold=True,
            size_hint=(0.5, 0.1),
            pos_hint={"center_x": 0.5, "center_y": 0.45},
            background_color=Colors.ACCENT,
            background_normal="",
        )
        learn_btn.bind(on_release=self._start_learn)
        layout.add_widget(learn_btn)

        quiz_btn = RoundedButton(
            text="Zum Quiz",
            font_name=_font(),
            font_size="35sp",
            bold=True,
            size_hint=(0.5, 0.1),
            pos_hint={"center_x": 0.5, "center_y": 0.32},
            background_color=Colors.BG_BUTTON,
            background_normal="",
        )
        quiz_btn.bind(on_release=self._go_quiz_intro_from_start)
        layout.add_widget(quiz_btn)

        exit_btn = RoundedButton(
            text="Zurück zur Appübersicht",
            font_name=_font(),
            font_size="16sp",
            size_hint=(0.5, 0.08),
            pos_hint={"center_x": 0.5, "bottom": 0.04},
            background_color=Colors.BG_BUTTON,
        )
        exit_btn.bind(on_release=lambda x: self.stop())
        layout.add_widget(exit_btn)

        self._widgets["start"] = layout

    def _build_quiz_intro(self):
        """Explanation of quiz modes between learn mode and quiz."""
        layout = FloatLayout(size_hint=(1, 1))

        heading = Label(
            text="Bereit für das Quiz?",
            font_name=_font(),
            font_size="40sp",
            bold=True,
            color=Colors.TEXT_PRIMARY,
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "top": 0.92},
        )
        heading.bind(texture_size=heading.setter("size"))
        layout.add_widget(heading)

        scroll = ScrollView(size_hint=(0.7, 0.45), pos_hint={"center_x": 0.5, "top": 0.82})
        intro = Label(
            text=QUIZ_INTRO_TEXT,
            font_name=_font(),
            font_size="25sp",
            color=Colors.TEXT_PRIMARY,
            size_hint=(1, None),
            halign="left",
            valign="middle",
        )
        intro.bind(
            texture_size=lambda lbl, val: setattr(lbl, "height", val[1] + 40),
            size=lambda lbl, val: setattr(lbl, "text_size", (val[0], None)),
        )
        scroll.add_widget(intro)
        layout.add_widget(scroll)

        tap_btn = RoundedButton(
            text="Auf Karte tippen",
            font_name=_font(),
            font_size="35sp",
            size_hint=(0.7, 0.1),
            pos_hint={"center_x": 0.5, "center_y": 0.32},
            bold=True,
            background_color=Colors.ACCENT,
            background_normal="",
        )
        tap_btn.bind(on_release=lambda x: self._start_quiz_from_intro("tap"))
        layout.add_widget(tap_btn)

        mc_btn = RoundedButton(
            text="Multiple Choice",
            font_name=_font(),
            font_size="35sp",
            size_hint=(0.7, 0.1),
            pos_hint={"center_x": 0.5, "center_y": 0.18},
            bold=True,
            background_color=Colors.ACCENT_2,
            background_normal="",
        )
        mc_btn.bind(on_release=lambda x: self._start_quiz_from_intro("mc"))
        layout.add_widget(mc_btn)

        exit_btn = RoundedButton(
            text="Zurück zur Appübersicht",
            font_name=_font(),
            font_size="16sp",
            size_hint=(0.5, 0.08),
            pos_hint={"center_x": 0.5, "bottom": 0.04},
            background_color=Colors.BG_BUTTON,
        )
        exit_btn.bind(on_release=lambda x: self.stop())
        layout.add_widget(exit_btn)

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

        btn = RoundedButton(
            text="Zurück zur Startseite",
            font_name=_font(),
            font_size="35sp",
            bold=True,
            size_hint=(0.5, 0.1),
            pos_hint={"center_x": 0.5, "center_y": 0.35},
            background_color=Colors.ACCENT,
            background_normal="",
        )
        btn.bind(on_release=lambda x: self._show_screen("start"))
        layout.add_widget(btn)

        exit_btn = RoundedButton(
            text="Zurück zur Appübersicht",
            font_name=_font(),
            font_size="16sp",
            size_hint=(0.5, 0.08),
            pos_hint={"center_x": 0.5, "bottom": 0.04},
            background_color=Colors.BG_BUTTON,
        )
        exit_btn.bind(on_release=lambda x: self.stop())
        layout.add_widget(exit_btn)

        self._widgets["quiz_end"] = layout

    def _show_quiz_end(self):
        """Show quiz finished."""
        total = len(self.session_constellations)
        if self.quiz_variant == "tap":
            max_points = total * (total + 1) // 2  # 7+6+5+...+1
        else:
            max_points = total * 3
        lines = [
            "Quiz beendet!",
            "",
            f"{self.points} von {max_points} Punkten",
            f"({total} von {total} Sternbilder gefunden)",
        ]
        if self.quiz_wrong_attempts > 0:
            lines.append(f"({self.quiz_wrong_attempts} Fehlversuch{'e' if self.quiz_wrong_attempts > 1 else ''})")
        self._quiz_end_label.text = "\n".join(lines)
        self._quiz_end_label.size_hint_x = 0.9
        self.star_map.opacity = 0
        self._show_screen("quiz_end")

    def _build_learn_ui(self):
        layout = FloatLayout(size_hint=(1, 1))

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

        nav = BoxLayout(
            orientation="horizontal",
            size_hint=(0.9, 0.08),
            pos_hint={"center_x": 0.5, "bottom": 0.02},
            spacing=20,
        )
        back_btn = RoundedButton(
            text="Zurück",
            font_name=_font(),
            font_size="25sp",
            bold=True,
            size_hint_x=None,
            width=120,
            background_color=Colors.BG_BUTTON,
            background_normal="",
        )
        back_btn.bind(on_release=self._learn_back)
        next_btn = RoundedButton(
            text="Weiter",
            font_name=_font(),
            font_size="25sp",
            bold=True,
            size_hint_x=None,
            width=120,
            background_color=Colors.ACCENT,
            background_normal="",
        )
        next_btn.bind(on_release=self._learn_next)
        nav.add_widget(back_btn)
        nav.add_widget(next_btn)
        layout.add_widget(nav)
        self._learn_back_btn = back_btn
        self._learn_next_btn = next_btn

        hint = Label(
            text="Blättere mit Vor und Zurück durch die Sternbilder.",
            font_name=_font(),
            font_size="12sp",
            color=Colors.TEXT_SECONDARY,
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "bottom": 0.12},
        )
        hint.bind(texture_size=hint.setter("size"))
        layout.add_widget(hint)

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
        tap_btn = RoundedButton(
            text="Auf Karte tippen",
            font_name=_font(),
            size_hint_x=None,
            width=160,
            background_color=Colors.BG_BUTTON,
            background_normal="",
        )
        tap_btn.bind(on_release=lambda x: self._set_quiz_variant("tap"))
        mc_btn = RoundedButton(
            text="Multiple Choice",
            font_name=_font(),
            size_hint_x=None,
            width=160,
            background_color=Colors.BG_BUTTON,
            background_normal="",
        )
        mc_btn.bind(on_release=lambda x: self._set_quiz_variant("mc"))
        self._quiz_variant_box.add_widget(tap_btn)
        self._quiz_variant_box.add_widget(mc_btn)
        layout.add_widget(self._quiz_variant_box)
        self._quiz_tap_btn = tap_btn
        self._quiz_mc_btn = mc_btn

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
            if child is not self.star_map and child is not self.feedback:
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

        self.star_map._draw()

    def _start_learn(self, *args):
        cfg = self._get_config()
        self.session_constellations = get_session_constellations(
            cfg["learn_count"], cfg["always_include"]
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
            self._learn_note.text = BIG_DIPPER_NOTE
            self._learn_note.opacity = 1
        else:
            self._learn_note.text = ""
            self._learn_note.opacity = 0

        self._learn_back_btn.text = "Zurück"
        self._learn_next_btn.text = "Quiz" if idx == len(self.session_constellations) - 1 else "Weiter"

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
            cfg["quiz_count"], cfg["always_include"]
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
        self.quiz_label.text = f"Finde: {display}"
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
