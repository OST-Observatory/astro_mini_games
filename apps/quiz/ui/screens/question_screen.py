"""Question screen: question, optional image, 4 answer buttons, timer"""

import random
from pathlib import Path

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label

from ui.theme import Colors, SPACING_XS, SPACING_MD, SPACING_LG, MIN_TOUCH_TARGET
from ui.rounded_button import RoundedButton
from ui.widgets.gif_image import GifImage
from ui.widgets.timer_bar import TimerBar


def _font_kw():
    from shared.fonts import get_safe_font
    return {"font_name": get_safe_font()}


class AnswerButton(RoundedButton):
    """Answer button with rounded corners and touch feedback."""

    def __init__(self, **kwargs):
        super().__init__(
            **_font_kw(),
            font_size="18sp",
            size_hint_y=None,
            height=MIN_TOUCH_TARGET + 12,
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
            **kwargs
        )

    def on_press(self):
        # Opacity feedback instead of size_hint_y (None cannot be animated)
        anim = Animation(opacity=0.85, duration=0.05) + Animation(opacity=1, duration=0.1)
        anim.start(self)


class QuestionScreen(FloatLayout):
    """Shows a question and 4 answer buttons with timer."""

    def __init__(self, on_answer=None, **kwargs):
        super().__init__(**kwargs)
        self.on_answer_callback = on_answer
        self.timer_event = None
        self.question_start = 0.0
        self.timer_total = 20

    def show_question(self, question: dict, timer_seconds: int):
        """Display the question and start the timer."""
        self.clear_widgets()
        self.timer_total = timer_seconds
        self.question_start = Clock.get_time()

        # Layout
        box = BoxLayout(
            orientation="vertical",
            size_hint=(0.9, 0.85),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            spacing=SPACING_MD,
            padding=SPACING_MD * 2,
        )

        # Optional image above timer (max height limited, width = answer buttons if possible)
        IMAGE_MAX_HEIGHT = 800
        IMAGE_MARGIN_BOTTOM = SPACING_LG  # Spacing to timer
        image_path = question.get("image")
        image_credit = question.get("image_credit", "").strip()
        if image_path:
            quiz_root = Path(__file__).resolve().parent.parent.parent
            full_path = (quiz_root / image_path).resolve()
            if full_path.is_file():
                img_container = BoxLayout(
                    orientation="vertical",
                    size_hint=(1, None),
                    spacing=SPACING_XS,
                    padding=(0, 0, 0, IMAGE_MARGIN_BOTTOM),
                )
                is_gif = image_path.lower().endswith(".gif")
                if is_gif:
                    img = GifImage(
                        source=image_path,
                        size_hint=(1, None),
                        height=IMAGE_MAX_HEIGHT,
                    )
                else:
                    img = Image(
                        source=str(full_path),
                        size_hint=(1, None),
                        height=IMAGE_MAX_HEIGHT,
                        keep_ratio=True,
                        allow_stretch=True,
                    )
                img_container.add_widget(img)
                if image_credit:
                    credit_label = Label(
                        text=image_credit,
                        **_font_kw(),
                        font_size="12sp",
                        color=Colors.TEXT_MUTED,
                        halign="center",
                        size_hint_y=None,
                        height=40,
                    )
                    credit_label.bind(
                        size=lambda *x: setattr(credit_label, "text_size", (credit_label.width, None)),
                    )
                    img_container.add_widget(credit_label)
                img_container.height = (
                    IMAGE_MAX_HEIGHT
                    + (SPACING_XS + 40 if image_credit else 0)
                    + IMAGE_MARGIN_BOTTOM
                )
                box.add_widget(img_container)

        # Points/streak
        font_kw = _font_kw()
        self.stats_label = Label(
            text="",
            **font_kw,
            font_size="16sp",
            color=Colors.TEXT_SECONDARY,
            size_hint_y=None,
            height=30,
        )
        box.add_widget(self.stats_label)

        # Timer
        self.timer_bar = TimerBar(size_hint_y=None, height=14)
        self.timer_bar.progress = 1.0
        box.add_widget(self.timer_bar)

        # Question
        q_label = Label(
            text=question["text"],
            **font_kw,
            font_size="22sp",
            color=Colors.TEXT_PRIMARY,
            halign="center",
            valign="middle",
            size_hint_y=None,
        )
        q_label.bind(size=lambda *x: setattr(q_label, "text_size", (q_label.width, None)))
        q_label.height = 100
        box.add_widget(q_label)

        # Answers – order random per question
        answers_shuffled = list(enumerate(question["answers"]))
        random.shuffle(answers_shuffled)
        for orig_idx, ans_text in answers_shuffled:
            btn = AnswerButton(text=ans_text)
            btn.answer_index = orig_idx  # Original index for game_logic.submit_answer
            btn.bind(on_release=self._on_answer)
            box.add_widget(btn)

        self.add_widget(box)
        self._question = question
        self._answer_buttons = box.children[-4:]  # always the 4 answer buttons

        # Start timer
        if self.timer_event:
            self.timer_event.cancel()
        self.timer_event = Clock.schedule_interval(self._update_timer, 0.05)

    def update_stats(self, points: int, streak: int):
        """Updates the statistics display."""
        if hasattr(self, "stats_label") and self.stats_label:
            s = f"Punkte: {points}"
            if streak > 1:
                s += f"  |  Streak: {streak}x"
            self.stats_label.text = s

    def _update_timer(self, dt):
        elapsed = Clock.get_time() - self.question_start
        progress = max(0, 1.0 - elapsed / self.timer_total)
        self.timer_bar.progress = progress

        if progress <= 0:
            self.timer_event.cancel()
            self.timer_event = None
            if self.on_answer_callback:
                self.on_answer_callback(timeout=True)

    def _on_answer(self, instance):
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

        if self.on_answer_callback:
            elapsed = Clock.get_time() - self.question_start
            self.on_answer_callback(answer_index=instance.answer_index, elapsed=elapsed)

    def on_leave(self):
        """Clean up when leaving the screen (cancel timer)."""
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
