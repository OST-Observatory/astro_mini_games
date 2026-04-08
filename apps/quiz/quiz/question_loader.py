"""Load and parse the question pool from YAML."""

import random
from pathlib import Path


DIFFICULTY_ORDER = ("laie", "amateur", "astronom")  # easy → hard


def get_questions_yaml_path() -> Path:
    """Localized questions file; fallback to German."""
    from shared.i18n import get_locale

    base = Path(__file__).resolve().parent.parent / "data"
    loc = get_locale()
    cand = base / f"questions.{loc}.yaml"
    if cand.is_file():
        return cand
    return base / "questions.de.yaml"


def load_categories_from_questions_file(questions_path: Path = None) -> list:
    """Category list (id, name) from the localized questions YAML."""
    import yaml

    path = questions_path or get_questions_yaml_path()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("categories", [])


def _normalize_difficulty(d) -> str:
    """Convert numbers (1,2,3) and legacy labels to laie/amateur/astronom."""
    if d is None:
        return "laie"
    if isinstance(d, int):
        return {1: "laie", 2: "amateur", 3: "astronom"}.get(d, "laie")
    s = str(d).lower().strip()
    # Backward compatibility with old labels
    legacy = {"einsteiger": "laie", "fortgeschrittene": "amateur", "amateurastronom": "astronom"}
    return legacy.get(s, s) if s in legacy else s


def _difficulty_satisfies(question_diff: str, max_difficulty: str) -> bool:
    """
    True if question_diff is at or below max_difficulty.
    Amateur includes Laie, Astronom includes Laie + Amateur.
    """
    try:
        return DIFFICULTY_ORDER.index(question_diff) <= DIFFICULTY_ORDER.index(max_difficulty)
    except ValueError:
        return False


def get_category_difficulty_map(questions_path: Path = None) -> dict:
    """
    Derive category-difficulty mapping from questions.
    - Category with only one difficulty -> fixed level (laie|amateur|astronom)
    - Category with multiple difficulties -> flexible (None, questions filtered individually)
    """
    import yaml

    if questions_path is None:
        questions_path = get_questions_yaml_path()

    with open(questions_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    questions = data.get("questions", [])
    # Per category: set of occurring difficulties
    cat_difficulties = {}
    for q in questions:
        cat = q.get("category")
        if not cat:
            continue
        d = _normalize_difficulty(q.get("difficulty", "laie"))
        cat_difficulties.setdefault(cat, set()).add(d)

    result = {}
    for cat, diffs in cat_difficulties.items():
        if len(diffs) == 1:
            result[cat] = next(iter(diffs))
    return result


def get_question_count_per_category(
    difficulty: str,
    category_difficulty_map: dict,
    questions_path: Path = None,
) -> dict:
    """
    Return question count per category (inclusive: selected level + easier).
    """
    import yaml

    if questions_path is None:
        questions_path = get_questions_yaml_path()

    with open(questions_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    questions = data.get("questions", [])
    diff = (difficulty or "laie").lower().strip()
    cat_map = category_difficulty_map or {}
    counts = {}

    for q in questions:
        q_cat = q.get("category")
        if not q_cat:
            continue
        q_diff = _normalize_difficulty(q.get("difficulty", "laie"))
        mapped = cat_map.get(q_cat)

        # Inclusive filter logic: selected level includes easier
        if mapped is not None:
            if not _difficulty_satisfies(mapped, diff):
                continue
        else:
            if not _difficulty_satisfies(q_diff, diff):
                continue

        counts[q_cat] = counts.get(q_cat, 0) + 1

    return counts


def get_categories_for_difficulty(
    categories: list,
    difficulty: str,
    category_difficulty_map: dict,
    min_questions: int = None,
    questions_path: Path = None,
) -> list:
    """
    Return categories available for the selected difficulty.
    Amateur includes Laie questions, Astronom includes Laie + Amateur.
    If min_questions is set, only categories with at least that many questions are shown.
    """
    diff = difficulty or "laie"
    result = []
    for c in categories:
        cat_id = c.get("id")
        if not cat_id:
            continue
        mapped = category_difficulty_map.get(cat_id)
        if mapped is None:
            # Flexible category
            result.append(c)
        elif _difficulty_satisfies(mapped, diff):
            result.append(c)

    if min_questions is not None and min_questions > 0:
        counts = get_question_count_per_category(
            diff, category_difficulty_map, questions_path
        )
        result = [c for c in result if counts.get(c.get("id"), 0) >= min_questions]

    return result


def load_questions(
    questions_path: Path = None,
    categories: list = None,
    difficulty: str = None,
    category_difficulty_map: dict = None,
) -> list:
    """
    Load questions from questions.yaml, filtered by categories and difficulty.
    Difficulty is inclusive: Amateur = Laie+Amateur, Astronom = all.
    """
    import yaml

    if questions_path is None:
        questions_path = get_questions_yaml_path()

    with open(questions_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    questions = data.get("questions", [])
    diff = (difficulty or "laie").lower().strip()
    cat_map = category_difficulty_map or {}

    filtered = []
    for q in questions:
        q_cat = q.get("category")
        q_diff = _normalize_difficulty(q.get("difficulty", "laie"))

        # Category filter
        if categories and q_cat not in categories:
            continue

        # Difficulty filter (inclusive: Amateur = Laie+Amateur, Astronom = all)
        mapped = cat_map.get(q_cat)
        if mapped is not None:
            if not _difficulty_satisfies(mapped, diff):
                continue
        else:
            if not _difficulty_satisfies(q_diff, diff):
                continue

        filtered.append(q)

    return filtered


def shuffle_and_limit(questions: list, limit: int = None) -> list:
    """Shuffle questions and limit to limit."""
    shuffled = questions.copy()
    random.shuffle(shuffled)
    if limit:
        shuffled = shuffled[:limit]
    return shuffled
