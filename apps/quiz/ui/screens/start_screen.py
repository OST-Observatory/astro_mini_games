"""Start screen: category, difficulty, quiz start"""

from kivy.graphics import Color, RoundedRectangle
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner, SpinnerOption

from ui.theme import Colors, SPACING_LG, SPACING_MD, SPACING_SM, MIN_TOUCH_TARGET, RADIUS_LG
from ui.rounded_button import RoundedButton
from quiz.question_loader import get_categories_for_difficulty
from shared.i18n import tr

DIFFICULTY_IDS = ("laie", "amateur", "astronom")

ROUND_OPTIONS = ["5", "10", "15", "20"]


class QuizSpinnerOption(SpinnerOption):
    """Dropdown option - darker background for distinction."""

    def __init__(self, **kwargs):
        super().__init__(
            background_color=Colors.BG_SPINNER_OPTION,
            background_normal="",
            color=Colors.TEXT_PRIMARY,
            **kwargs
        )


def _font():
    from shared.fonts import get_safe_font
    return get_safe_font()


class _ChipButton(RoundedButton):
    """Chip button with active/inactive display."""

    def __init__(self, value, is_active=False, **kwargs):
        self._value = value
        self._is_active = is_active
        self._active_color = kwargs.pop("background_color", Colors.ACCENT)
        self._inactive_color = Colors.BG_BUTTON
        initial = self._active_color if is_active else self._inactive_color
        super().__init__(background_color=initial, **kwargs)
        self._update_color()

    def _update_color(self):
        self.set_display_color(self._active_color if self._is_active else self._inactive_color)

    def set_active(self, active: bool):
        """Set active state and update visual appearance."""
        self._is_active = active
        self._update_color()


class StartScreen(FloatLayout):
    """Start screen with difficulty, category and question count."""

    def __init__(
        self,
        categories: list,
        category_difficulty_map: dict = None,
        on_start=None,
        on_exit=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.on_start_callback = on_start
        self.on_exit_callback = on_exit
        self.categories = categories
        self._category_difficulty_map = category_difficulty_map or {}
        self._difficulty_ids = list(DIFFICULTY_IDS)
        self._selected_difficulty = "laie"
        self._selected_rounds = "10"
        self._difficulty_buttons = []
        self._round_buttons = []
        self._build_ui()

    def apply_locale(self):
        """Refresh visible strings (categories may be updated separately)."""
        self._title_label.text = tr("quiz.title")
        self._intro_label.text = tr("quiz.intro")
        self._difficulty_caption.text = tr("quiz.difficulty_label")
        self._round_caption.text = tr("quiz.rounds_label")
        self._category_caption.text = tr("quiz.category_label")
        self._start_btn.text = tr("quiz.start")
        self._exit_btn.text = tr("quiz.back_launcher")
        for btn in self._difficulty_buttons:
            btn.text = tr(f"quiz.diff_{btn._value}")
        self._update_category_spinner()

    def _build_ui(self):
        f = _font()
        font_kw = {"font_name": f} if f else {}

        box = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            spacing=SPACING_LG * 1.5,
            padding=SPACING_LG * 2,
        )
        box.bind(minimum_height=box.setter("height"))

        # Title (centered)
        title_anchor = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint_x=1,
            size_hint_y=None,
            height=95,
        )
        self._title_label = Label(
            text=tr("quiz.title"),
            font_size="44sp",
            bold=True,
            **font_kw,
            color=Colors.TEXT_PRIMARY,
            size_hint_x=None,
        )
        title_anchor.add_widget(self._title_label)
        box.add_widget(title_anchor)

        # Intro text
        self._intro_label = Label(
            text=tr("quiz.intro"),
            **font_kw,
            font_size="22sp",
            color=Colors.TEXT_SECONDARY,
            size_hint_y=None,
            halign="center",
            valign="middle",
        )
        self._intro_label.bind(
            texture_size=lambda lbl, val: setattr(lbl, "height", val[1] + 24),
            size=lambda lbl, val: setattr(lbl, "text_size", (val[0], None)),
        )
        box.add_widget(self._intro_label)

        # Spacer between intro and settings
        box.add_widget(BoxLayout(size_hint_y=None, height=SPACING_LG * 20))

        # Card container for settings
        card = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=SPACING_LG,
            padding=SPACING_LG * 1.5,
        )
        with card.canvas.before:
            Color(*Colors.BG_CARD)
            card._bg_rect = RoundedRectangle(
                pos=card.pos, size=card.size, radius=[RADIUS_LG] * 4
            )
        card.bind(pos=self._update_card_rect, size=self._update_card_rect)

        # Difficulty as chips
        self._difficulty_caption = Label(
            text=tr("quiz.difficulty_label"),
            **font_kw,
            font_size="17sp",
            color=Colors.TEXT_SECONDARY,
            size_hint_y=None,
            height=36,
        )
        card.add_widget(self._difficulty_caption)

        diff_row = BoxLayout(orientation="horizontal", spacing=SPACING_SM, size_hint_y=None, height=MIN_TOUCH_TARGET)
        for diff_id in DIFFICULTY_IDS:
            btn = _ChipButton(
                diff_id,
                is_active=(diff_id == self._selected_difficulty),
                text=tr(f"quiz.diff_{diff_id}"),
                **font_kw,
                font_size="17sp",
                size_hint_x=1,
                background_color=Colors.ACCENT,
                color=Colors.TEXT_PRIMARY,
            )
            btn.bind(on_release=lambda b, d=diff_id: self._on_difficulty_clicked(d))
            self._difficulty_buttons.append(btn)
            diff_row.add_widget(btn)
        card.add_widget(diff_row)

        # Questions per round as chips
        self._round_caption = Label(
            text=tr("quiz.rounds_label"),
            **font_kw,
            font_size="17sp",
            color=Colors.TEXT_SECONDARY,
            size_hint_y=None,
            height=36,
        )
        card.add_widget(self._round_caption)

        round_row = BoxLayout(orientation="horizontal", spacing=SPACING_SM, size_hint_y=None, height=MIN_TOUCH_TARGET)
        for r in ROUND_OPTIONS:
            btn = _ChipButton(
                r,
                is_active=(r == self._selected_rounds),
                text=r,
                **font_kw,
                font_size="17sp",
                size_hint_x=1,
                background_color=Colors.ACCENT,
                color=Colors.TEXT_PRIMARY,
            )
            btn.bind(on_release=lambda b, v=r: self._on_rounds_clicked(v))
            self._round_buttons.append(btn)
            round_row.add_widget(btn)
        card.add_widget(round_row)

        # Category (spinner stays, as it's dynamic)
        self._category_caption = Label(
            text=tr("quiz.category_label"),
            **font_kw,
            font_size="17sp",
            color=Colors.TEXT_SECONDARY,
            size_hint_y=None,
            height=70,
        )
        card.add_widget(self._category_caption)

        self._update_category_spinner()
        card.add_widget(self.category_spinner)

        box.add_widget(card)

        # Spacing between settings and start button
        box.add_widget(BoxLayout(size_hint_y=None, height=SPACING_LG * 20))

        # Start button (prominent)
        self._start_btn = RoundedButton(
            text=tr("quiz.start"),
            **font_kw,
            font_size="26sp",
            size_hint_y=None,
            height=MIN_TOUCH_TARGET + 28,
            background_color=Colors.ACCENT,
            color=Colors.TEXT_PRIMARY,
            radius=RADIUS_LG,
        )
        self._start_btn.bind(on_release=self._on_start)
        box.add_widget(self._start_btn)

        self._exit_btn = RoundedButton(
            text=tr("quiz.back_launcher"),
            **font_kw,
            font_size="15sp",
            size_hint_y=None,
            height=MIN_TOUCH_TARGET,
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        self._exit_btn.bind(on_release=self._on_exit)
        box.add_widget(self._exit_btn)

        scroll = ScrollView(
            size_hint=(0.9, 0.9),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            do_scroll_x=False,
            bar_width=10,
        )
        scroll.add_widget(box)
        self.add_widget(scroll)

    def _update_card_rect(self, instance, value=None):
        instance._bg_rect.pos = instance.pos
        instance._bg_rect.size = instance.size

    def _on_difficulty_clicked(self, diff_id: str):
        self._selected_difficulty = diff_id
        for btn in self._difficulty_buttons:
            btn.set_active(btn._value == diff_id)
        self._update_category_spinner()

    def _on_rounds_clicked(self, value: str):
        self._selected_rounds = value
        for btn in self._round_buttons:
            btn.set_active(btn._value == value)
        self._update_category_spinner()

    def _update_category_spinner(self):
        """Update category spinner: difficulty + only categories with enough questions."""
        difficulty_id = self._selected_difficulty
        min_questions = int(self._selected_rounds)
        allowed = get_categories_for_difficulty(
            self.categories,
            difficulty_id,
            self._category_difficulty_map,
            min_questions=min_questions,
        )
        all_label = tr("quiz.category_all")
        cat_values = [all_label] + [c.get("name", c.get("id", "")) for c in allowed]
        cat_ids = [None] + [c.get("id") for c in allowed]
        f = _font()
        font_kw = {"font_name": f} if f else {}
        if hasattr(self, "category_spinner") and self.category_spinner:
            self.category_spinner.values = cat_values
            self.category_spinner.text = cat_values[0] if cat_values else all_label
        else:
            self.category_spinner = Spinner(
                text=cat_values[0] if cat_values else all_label,
                values=cat_values,
                **font_kw,
                font_size="17sp",
                size_hint_y=None,
                height=MIN_TOUCH_TARGET,
                background_color=Colors.BG_SPINNER_SELECTED,
                background_normal="",
                color=Colors.TEXT_PRIMARY,
                option_cls=QuizSpinnerOption,
            )
        self._category_ids = cat_ids

    def _on_start(self, instance):
        if self.on_start_callback:
            idx = self.category_spinner.values.index(self.category_spinner.text)
            category_id = self._category_ids[idx] if idx < len(self._category_ids) else None
            count = int(self._selected_rounds)
            difficulty = self._selected_difficulty
            self.on_start_callback(
                category_filter=category_id,
                questions_count=count,
                difficulty=difficulty,
            )

    def _on_exit(self, instance):
        if self.on_exit_callback:
            self.on_exit_callback()
