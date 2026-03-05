"""Quiz game logic: points, streak, timer, next question."""


class QuizGame:
    """Manages the quiz game state."""

    def __init__(self, questions: list, config: dict, difficulty: str = "laie"):
        self.questions = questions
        self.config = config
        self.difficulty = (difficulty or "laie").lower().strip()
        self.current_index = 0
        self.points = 0
        self.correct_count = 0
        self.streak = 0
        self.max_streak = 0
        self.last_answer_time = 0.0
        self.question_start_time = 0.0
        # History: list of (question, user_answer_index, correct)
        self.answer_history = []

    @property
    def current_question(self):
        """Current question or None when done."""
        if 0 <= self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    @property
    def is_finished(self):
        """True when all questions answered."""
        return self.current_index >= len(self.questions)

    @property
    def total_questions(self):
        """Total number of questions in the current round."""
        return len(self.questions)

    def submit_answer(self, answer_index: int, elapsed: float) -> bool:
        """Check answer. Returns True if correct."""
        q = self.current_question
        if not q:
            return False

        correct = answer_index == q["correct"]
        self.last_answer_time = elapsed
        self.answer_history.append((q, answer_index, correct))

        if correct:
            self.correct_count += 1
            self.streak += 1
            if self.streak > self.max_streak:
                self.max_streak = self.streak

            base_points = self.config.get("points_per_correct", 10)
            diff_levels = self.config.get("difficulty_levels", {})
            multiplier = diff_levels.get(self.difficulty, 1.0)
            base_points = int(base_points * multiplier)

            bonus = 0
            if self.config.get("bonus_for_fast") and elapsed <= self.config.get(
                "bonus_threshold_seconds", 5
            ):
                bonus = base_points  # Double points for fast answer
            self.points += base_points + bonus
        else:
            self.streak = 0

        self.current_index += 1
        return correct

    def timeout(self):
        """Time expired - count as wrong, next question."""
        q = self.current_question
        if q:
            self.answer_history.append((q, None, False))
        self.streak = 0
        self.current_index += 1
