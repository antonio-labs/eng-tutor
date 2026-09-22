import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from app import curriculum
from app.curriculum import (
    load_curriculum,
    load_explanation_markdown,
    load_sample_lesson,
    next_unit,
)
from app.grading import grade_lesson
from app.main import app, root
from app.models import AttemptResult, Exercise, LessonContent


REQUIRED_EXPLANATION_SECTIONS = [
    "Quando si usa",
    "Come si forma",
    "Attenzione",
    "Errori comuni",
]
FORBIDDEN_MARKDOWN = {
    "HTML": r"</?[A-Za-z][^>]*>",
    "immagini o link": r"!?\[[^\]\n]+\]\([^\)\n]+\)",
    "titoli non supportati": r"(?m)^#{1,2}\s|^#{4,}\s",
    "liste numerate": r"(?m)^\s*\d+[.)]\s",
    "blocchi di codice": r"(?m)^```",
    "tabelle": r"(?m)^\s*\|",
    "testo barrato": r"~~",
    "corsivo con asterischi": r"(?<!\*)\*(?!\*)[^*\n]+\*(?!\*)",
    "corsivo con underscore": r"(?<!_)_(?!_)[^_\n]+_(?!_)",
}


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


def test_explanation_loader_validates_id_file_and_content(
    tmp_path, monkeypatch
) -> None:
    unit_id = load_curriculum()[0].id
    content = "### Quando si usa\n\nContenuto verificato.\n"
    monkeypatch.setattr(curriculum, "EXPLANATIONS_DIR", tmp_path)
    (tmp_path / f"{unit_id}.md").write_text(content, encoding="utf-8")

    assert load_explanation_markdown(unit_id) == content
    with pytest.raises(ValueError, match="A1-99"):
        load_explanation_markdown("A1-99")

    (tmp_path / f"{unit_id}.md").unlink()
    with pytest.raises(FileNotFoundError, match=unit_id):
        load_explanation_markdown(unit_id)

    (tmp_path / f"{unit_id}.md").write_text(" \n", encoding="utf-8")
    with pytest.raises(ValueError, match=unit_id):
        load_explanation_markdown(unit_id)


def test_explanations_cover_curriculum_and_use_supported_markdown() -> None:
    unit_ids = {unit.id for unit in load_curriculum()}
    files = {
        path.stem: path for path in curriculum.EXPLANATIONS_DIR.glob("*.md")
    }

    assert set(files) == unit_ids
    for unit_id in sorted(unit_ids):
        content = load_explanation_markdown(unit_id)
        sections = list(re.finditer(r"(?m)^### (.+)$", content))

        assert [match.group(1) for match in sections] == REQUIRED_EXPLANATION_SECTIONS
        assert not content[: sections[0].start()].strip()
        for index, section in enumerate(sections):
            end = sections[index + 1].start() if index + 1 < len(sections) else None
            assert content[section.end() : end].strip(), (
                f"{unit_id}: sezione vuota {section.group(1)}"
            )
        for feature, pattern in FORBIDDEN_MARKDOWN.items():
            assert not re.search(pattern, content), (
                f"{unit_id}: Markdown non supportato ({feature})"
            )


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
    assert all("correct_option" not in item for item in browser_payload["exercises"])
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
