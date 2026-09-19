import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.curriculum import load_curriculum, load_sample_lesson, next_unit
from app.grading import grade_lesson
from app.main import app, root
from app.models import AttemptResult, Exercise, LessonContent


def test_curriculum_matches_documented_coverage() -> None:
    units = load_curriculum()
    source_rows = []
    for line in (Path(__file__).parents[1] / "A1-CURRICULUM.md").read_text().splitlines():
        if line.startswith("| A1-"):
            _, unit_id, title, objective, _, _ = [cell.strip() for cell in line.split("|")]
            source_rows.append((unit_id, title.replace("*", ""), objective))

    assert len(units) == 36
    assert [unit.id for unit in units] == [f"A1-{number:02}" for number in range(1, 37)]
    assert len({unit.id for unit in units}) == 36
    assert all(unit.title and unit.objective for unit in units)
    assert [(unit.id, unit.title, unit.objective) for unit in units] == source_rows


def test_sample_lesson_is_valid_and_hides_answers_from_browser() -> None:
    lesson = load_sample_lesson()
    browser_payload = lesson.for_browser().model_dump()

    assert len(lesson.examples) == 3
    assert len(lesson.exercises) == 6
    assert browser_payload["timing"] == {
        "explanation_and_examples_minutes": 3,
        "exercises_minutes": 9,
        "review_minutes": 3,
        "total_minutes": 15,
    }
    assert all("correct_option" not in item for item in browser_payload["exercises"])
    assert all("rationale" not in item for item in browser_payload["exercises"])


def test_lesson_validation_rejects_invalid_structure() -> None:
    lesson_data = json.loads(
        (Path(__file__).parents[1] / "app/data/sample_lesson.json").read_text()
    )
    lesson_data["exercises"][1]["id"] = lesson_data["exercises"][0]["id"]
    with pytest.raises(ValidationError):
        LessonContent.model_validate(lesson_data)

    with pytest.raises(ValidationError):
        Exercise(
            id="q",
            question="Choose",
            options=["same", "same", "other"],
            correct_option=0,
            rationale="Reason",
        )


@pytest.mark.parametrize(
    ("wrong_answers", "correct", "percentage", "passed"),
    [(2, 4, 67, False), (1, 5, 83, True)],
)
def test_grading_uses_correct_count_for_threshold(
    wrong_answers: int, correct: int, percentage: int, passed: bool
) -> None:
    lesson = load_sample_lesson()
    answers = {exercise.id: exercise.correct_option for exercise in lesson.exercises}
    for exercise in lesson.exercises[:wrong_answers]:
        answers[exercise.id] = (exercise.correct_option + 1) % 3

    result = grade_lesson(lesson, answers)

    assert result.correct_answers == correct
    assert result.percentage == percentage
    assert result.passed is passed
    assert all(answer.selected_answer for answer in result.answers)
    assert all(answer.solution and answer.rationale for answer in result.answers)


def test_progression_handles_no_results_retries_and_completion() -> None:
    units = load_curriculum()

    assert next_unit(units, []) == units[0]
    assert next_unit(units, [AttemptResult(unit_id="A1-01", correct_answers=4)]) == units[0]
    assert next_unit(
        units,
        [
            AttemptResult(unit_id="A1-01", correct_answers=4),
            AttemptResult(unit_id="A1-01", correct_answers=5),
        ],
    ) == units[1]
    assert next_unit(
        units,
        [AttemptResult(unit_id=unit.id, correct_answers=5) for unit in units],
    ) is None


def test_local_api_starts_with_curriculum() -> None:
    assert root()["curriculum_units"] == 36
    assert {route.path for route in app.routes} >= {"/", "/api/curriculum", "/docs"}
