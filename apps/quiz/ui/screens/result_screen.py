"""Result screen: points, stats, name input, leaderboard, restart."""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from ui.theme import Colors, SPACING_LG, SPACING_SM, MIN_TOUCH_TARGET
from ui.rounded_button import RoundedButton


def _font_kw():
    from shared.fonts import get_safe_font
    return {"font_name": get_safe_font()}


class ResultScreen(FloatLayout):
    """Shows result, name input, leaderboard and restart button."""

    def __init__(self, on_restart=None, on_exit=None, **kwargs):
        super().__init__(**kwargs)
        self.on_restart_callback = on_restart
        self.on_exit_callback = on_exit
        self._current_points = 0
        self._current_correct = 0
        self._current_total = 0
        self._already_submitted = False

    def show_result(
        self,
        points: int,
        correct: int,
        total: int,
        max_streak: int,
        answer_history: list = None,
    ):
        """Display the result."""
        self.clear_widgets()
        self._current_points = points
        self._current_correct = correct
        self._current_total = total
        self._already_submitted = False
        font_kw = _font_kw()

        scroll = ScrollView(size_hint=(1, 1))
        box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=SPACING_LG,
            padding=SPACING_LG * 2,
        )
        box.bind(minimum_height=box.setter("height"))

        title = Label(
            text="Quiz beendet!",
            **font_kw,
            font_size="32sp",
            bold=True,
            color=Colors.ACCENT,
            size_hint_y=None,
            height=50,
        )
        box.add_widget(title)

        score = Label(
            text=f"{points} Punkte",
            **font_kw,
            font_size="28sp",
            color=Colors.TEXT_PRIMARY,
            size_hint_y=None,
            height=50,
        )
        box.add_widget(score)

        stats = Label(
            text=f"{correct} von {total} richtig\nBester Streak: {max_streak}",
            **font_kw,
            font_size="18sp",
            color=Colors.TEXT_SECONDARY,
            halign="center",
            size_hint_y=None,
        )
        stats.bind(size=lambda *x: setattr(stats, "text_size", (stats.width, None)))
        stats.height = 80
        box.add_widget(stats)

        # Evaluation per question (3 columns)
        if answer_history:
            eval_label = Label(
                text="Auswertung",
                **font_kw,
                font_size="20sp",
                bold=True,
                color=Colors.ACCENT,
                size_hint_y=None,
                height=40,
            )
            box.add_widget(eval_label)

            eval_grid = GridLayout(
                cols=3,
                size_hint_y=None,
                spacing=SPACING_SM,
                padding=(0, SPACING_SM, 0, 0),
            )
            eval_grid.bind(minimum_height=eval_grid.setter("height"))
            for i, (q, user_idx, was_correct) in enumerate(answer_history, 1):
                cell = self._build_eval_cell(q, i, user_idx, was_correct, font_kw)
                eval_grid.add_widget(cell)
            box.add_widget(eval_grid)

        # Spacer
        box.add_widget(BoxLayout(size_hint_y=None, height=SPACING_LG * 5))

        # Leaderboard
        leaderboard_label = Label(
            text="Bestenliste",
            **font_kw,
            font_size="20sp",
            bold=True,
            color=Colors.ACCENT,
            size_hint_y=None,
            height=40,
        )
        box.add_widget(leaderboard_label)

        self._name_input = TextInput(
            **font_kw,
            font_size="18sp",
            multiline=False,
            size_hint_y=None,
            height=MIN_TOUCH_TARGET,
            background_color=Colors.BG_CARD,
            foreground_color=Colors.TEXT_PRIMARY,
            hint_text="Name eingeben…",
            write_tab=False,
        )
        box.add_widget(self._name_input)

        submit_btn = RoundedButton(
            text="In Bestenliste eintragen",
            **font_kw,
            font_size="18sp",
            size_hint_y=None,
            height=MIN_TOUCH_TARGET,
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        submit_btn.bind(on_release=self._on_submit_leaderboard)
        box.add_widget(submit_btn)

        self._leaderboard_label = Label(
            text=self._format_leaderboard(),
            **font_kw,
            font_size="16sp",
            color=Colors.TEXT_SECONDARY,
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        self._leaderboard_label.bind(
            size=lambda *x: setattr(self._leaderboard_label, "text_size", (self._leaderboard_label.width, None)),
            texture_size=lambda lbl, val: setattr(lbl, "height", val[1] + 20),
        )
        box.add_widget(self._leaderboard_label)

        box.add_widget(BoxLayout(size_hint_y=None, height=SPACING_LG))

        restart_btn = RoundedButton(
            text="Nochmal spielen",
            **font_kw,
            font_size="22sp",
            size_hint_y=None,
            height=MIN_TOUCH_TARGET + 16,
            background_color=Colors.ACCENT,
            color=Colors.TEXT_PRIMARY,
        )
        restart_btn.bind(on_release=lambda x: self.on_restart_callback() if self.on_restart_callback else None)
        box.add_widget(restart_btn)

        exit_btn = RoundedButton(
            text="Zurück zur App-Übersicht",
            **font_kw,
            font_size="16sp",
            size_hint_y=None,
            height=MIN_TOUCH_TARGET,
            background_color=Colors.BG_BUTTON,
            color=Colors.TEXT_PRIMARY,
        )
        exit_btn.bind(on_release=lambda x: self.on_exit_callback() if self.on_exit_callback else None)
        box.add_widget(exit_btn)

        scroll.add_widget(box)
        self.add_widget(scroll)

        # Confetti when >30% correct, amount scales with score
        if total > 0 and correct / total >= 0.3:
            from ui.confetti import ConfettiOverlay
            confetti = ConfettiOverlay(on_done=None)
            self.add_widget(confetti)
            confetti.start(ratio=correct / total)

    def _build_eval_cell(self, q, num, user_idx, correct, font_kw):
        """Create a compact cell for evaluation (3 columns, space-saving)."""
        text = (q.get("text", "") or "").strip()
        if len(text) > 70:
            text = text[:67] + "..."
        symbol = "✓" if correct else "✗"
        status_color = Colors.CORRECT if correct else Colors.WRONG
        answers = q.get("answers") or []
        if correct:
            ans = answers[user_idx] if user_idx is not None and 0 <= user_idx < len(answers) else "–"
            if len(ans) > 65:
                ans = ans[:62] + "..."
            line = f"{num}. {symbol} {text}\n   {ans}"
        else:
            corr_idx = q.get("correct", 0)
            corr_ans = answers[corr_idx] if 0 <= corr_idx < len(answers) else "?"
            if len(corr_ans) > 65:
                corr_ans = corr_ans[:62] + "..."
            line = f"{num}. {symbol} {text}\n   → {corr_ans}"
        lbl = Label(
            text=line,
            **font_kw,
            font_size="14sp",
            color=status_color,
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        lbl.bind(
            size=lambda inst, v: setattr(inst, "text_size", (inst.width, None)),
            texture_size=lambda inst, v: setattr(inst, "height", v[1] + 2),
        )
        return lbl

    def _format_leaderboard(self) -> str:
        from quiz.leaderboard import get_top_scores
        scores = get_top_scores()
        if not scores:
            return "Noch keine Einträge."
        lines = []
        for i, s in enumerate(scores, 1):
            name = (s.get("name", "?") or "?")[:20]
            pts = s.get("points", 0)
            lines.append(f"{i}. {name}: {pts} Punkte")
        return "\n".join(lines)

    def _on_submit_leaderboard(self, instance):
        if self._already_submitted:
            return
        name = (self._name_input.text or "").strip()
        if not name:
            return
        self._already_submitted = True
        from quiz.leaderboard import add_score
        rank = add_score(
            name=name,
            points=self._current_points,
            correct=self._current_correct,
            total=self._current_total,
        )
        self._leaderboard_label.text = self._format_leaderboard()
        if rank <= 3:
            self._leaderboard_label.text = (
                f"Glückwunsch! Du bist auf Platz {rank}!\n\n"
                + self._leaderboard_label.text
            )
