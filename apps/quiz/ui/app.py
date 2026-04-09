"""Main quiz app with screen management."""

import yaml
from pathlib import Path

from shared.base_app import AstroApp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout

from quiz.question_loader import (
    get_category_difficulty_map,
    get_localized_question_for_display,
    load_categories_from_questions_file,
    load_questions,
    shuffle_and_limit,
)
from shared.i18n import tr
from quiz.game_logic import QuizGame
from ui.screens.start_screen import StartScreen
from ui.screens.question_screen import QuestionScreen
from ui.screens.result_screen import ResultScreen
from ui.theme import Colors


class QuizApp(AstroApp):
    """Astro quiz Kivy application."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_path = Path(__file__).parent.parent / "config.yaml"
        self.config_data = {}
        self.game = None
        self.start_screen = None
        self.question_screen = None
        self.result_screen = None
        self.current_screen = None

    def build(self):
        """Build the quiz UI: start screen, question screen, result screen."""
        self.title = tr("quiz.title")
        Window.bind(on_keyboard=self._on_keyboard)
        self._load_config()
        # Make quiz images (incl. GIFs) available for resource_find
        from kivy.resources import resource_add_path
        quiz_root = Path(__file__).resolve().parent.parent
        resource_add_path(str(quiz_root))

        root = FloatLayout()
        with root.canvas.before:
            Color(*Colors.BG_VIEW)
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(size=self._update_bg)

        categories = load_categories_from_questions_file()
        category_difficulty_map = get_category_difficulty_map()
        self.start_screen = StartScreen(
            categories=categories,
            category_difficulty_map=category_difficulty_map,
            on_start=self._start_game,
            on_exit=self.stop,
        )
        self.question_screen = QuestionScreen(on_answer=self._on_answer)
        self.result_screen = ResultScreen(on_restart=self._to_start, on_exit=self.stop)

        root.add_widget(self.start_screen)
        self.current_screen = "start"
        Clock.schedule_once(self._trigger_redraw, 0.05)
        return root

    def _trigger_redraw(self, dt):
        """Pi-KMS: Touch triggers repaint - re-insert widget to force redraw."""
        root = self.root
        if not root or not root.children:
            return
        child = root.children[0]
        root.remove_widget(child)
        Clock.schedule_once(lambda d: root.add_widget(child), 0)

    def _update_bg(self, instance, value):
        self._bg_rect.pos = instance.pos
        self._bg_rect.size = instance.size

    def _load_config(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config_data = yaml.safe_load(f)

    def _start_game(self, category_filter=None, questions_count=10, difficulty=None):
        game_config = self.config_data.get("game", {})
        categories = [category_filter] if category_filter else None
        cat_diff_map = get_category_difficulty_map()
        questions = load_questions(
            categories=categories,
            difficulty=difficulty,
            category_difficulty_map=cat_diff_map,
        )
        questions = shuffle_and_limit(questions, limit=questions_count)

        if not questions:
            return

        self.game = QuizGame(questions, game_config, difficulty=difficulty or "laie")
        self._to_question()

    def _to_question(self):
        self._root_clear_screen_overlays()
        q = self.game.current_question
        if not q:
            self._to_result()
            return

        timer_sec = self.config_data.get("game", {}).get("timer_seconds", 20)
        q_display = get_localized_question_for_display(q)
        self.question_screen.show_question(q_display, timer_sec)
        self.question_screen.update_stats(self.game.points, self.game.streak)
        self.root.add_widget(self.question_screen)
        self.ensure_lang_switcher_on_top()
        self.current_screen = "question"

    def _on_answer(self, answer_index=None, elapsed=0, timeout=False):
        if timeout:
            self.game.timeout()
        else:
            self.game.submit_answer(answer_index, elapsed)

        self._to_question()

    def _to_result(self):
        self._root_clear_screen_overlays()
        self.result_screen.show_result(
            points=self.game.points,
            correct=self.game.correct_count,
            total=self.game.total_questions,
            max_streak=self.game.max_streak,
            answer_history=self.game.answer_history,
        )
        self.root.add_widget(self.result_screen)
        self.ensure_lang_switcher_on_top()
        self.current_screen = "result"

    def _to_start(self):
        self._root_clear_screen_overlays()
        self.root.add_widget(self.start_screen)
        self.ensure_lang_switcher_on_top()
        self.current_screen = "start"

    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:  # ESC
            self.stop()
            return True
        return False

    def _apply_locale(self):
        super()._apply_locale()
        self.title = tr("quiz.title")
        cats = load_categories_from_questions_file()
        cmap = get_category_difficulty_map()
        if self.start_screen:
            self.start_screen.categories = cats
            self.start_screen._category_difficulty_map = cmap
            self.start_screen.apply_locale()
        if self.current_screen == "question" and self.game and self.game.current_question:
            timer_sec = self.config_data.get("game", {}).get("timer_seconds", 20)
            q_display = get_localized_question_for_display(self.game.current_question)
            self.question_screen.show_question(q_display, timer_sec)
            self.question_screen.update_stats(self.game.points, self.game.streak)
        elif self.current_screen == "result" and self.result_screen:
            self.result_screen.apply_locale()
