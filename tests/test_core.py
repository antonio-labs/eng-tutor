from pathlib import Path
from shutil import copytree

import pytest
from pydantic import ValidationError

from app.assessment import grade_lesson, next_unit
from app.course import DATA_DIR, load_course, load_sample_lesson
from app.main import app, root
from app.models import AttemptResult, Exercise, LessonContent


def test_course_matches_documented_coverage() -> None:
    units = load_course().units
    source_rows = []
    curriculum_document = Path(__file__).parents[1] / "A1-CURRICULUM.md"
    for line in curriculum_document.read_text().splitlines():
        if line.startswith("| A1-"):
            _, unit_id, title, objective, _, _ = [cell.strip() for cell in line.split("|")]
            source_rows.append((unit_id, title.replace("*", ""), objective))

    assert len(units) == 36
    assert [unit.id for unit in units] == [
        f"A1-{number:02}" for number in range(1, 37)
    ]
    assert all(unit.title and unit.objective for unit in units)
    assert [(unit.id, unit.title, unit.objective) for unit in units] == source_rows


def test_course_loader_validates_the_whole_corpus(tmp_path) -> None:
    data_dir = tmp_path / "data"
    copytree(DATA_DIR, data_dir)
    course = load_course(data_dir)

    assert course.content_for("A1-01").explanation.startswith("### Quando si usa")
    with pytest.raises(ValueError, match="A1-99"):
        course.content_for("A1-99")

    source = data_dir / "grammar_explanations" / "A1-01.md"
    source.write_text("### Quando si usa\n\nSolo una sezione.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sections.*A1-01"):
        load_course(data_dir)

    copytree(DATA_DIR, data_dir, dirs_exist_ok=True)
    source = data_dir / "grammar_explanations" / "A1-01.md"
    source.write_text(
        source.read_text(encoding="utf-8")
        + "\n[link non supportato](https://example.com)\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unsupported Markdown.*A1-01"):
        load_course(data_dir)

    copytree(DATA_DIR, data_dir, dirs_exist_ok=True)
    (data_dir / "grammar_explanations" / "A1-36.md").unlink()
    with pytest.raises(ValueError, match="missing=.*A1-36"):
        load_course(data_dir)


def test_sample_lesson_is_valid_and_hides_answers_from_browser() -> None:
    lesson = load_sample_lesson()
    browser_payload = lesson.for_browser().model_dump()

    assert lesson.explanation.startswith("### Quando si usa")
    assert len(lesson.examples) == 3
    assert len(lesson.exercises) == 6
    assert browser_payload["timing"] == {
        "explanation_and_examples_minutes": 3,
        "exercises_minutes": 9,
        "review_minutes": 3,
        "total_minutes": 15,
    }
    assert all(
        "correct_option" not in item for item in browser_payload["exercises"]
    )
    assert all("rationale" not in item for item in browser_payload["exercises"])


def test_lesson_validation_rejects_invalid_structure() -> None:
    lesson_data = load_sample_lesson().model_dump()
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
def test_assessment_uses_fixed_a1_rules(
    wrong_answers: int, correct: int, percentage: int, passed: bool
) -> None:
    lesson = load_sample_lesson()
    answers = {exercise.id: exercise.correct_option for exercise in lesson.exercises}
    for exercise in lesson.exercises[:wrong_answers]:
        answers[exercise.id] = (exercise.correct_option + 1) % 3

    result = grade_lesson(lesson, answers)

    assert result.correct_answers == correct
    assert result.total_exercises == 6
    assert result.percentage == percentage
    assert result.passed is passed
    assert all(answer.selected_answer for answer in result.answers)
    assert all(answer.solution and answer.rationale for answer in result.answers)


def test_progression_handles_no_results_retries_and_completion() -> None:
    units = load_course().units

    assert next_unit(units, []) == units[0]
    assert next_unit(
        units, [AttemptResult(unit_id="A1-01", correct_answers=4)]
    ) == units[0]
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


def test_local_api_starts_with_course() -> None:
    assert root()["curriculum_units"] == 36
    assert {route.path for route in app.routes} >= {"/", "/api/curriculum", "/docs"}
