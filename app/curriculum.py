import json
from pathlib import Path
from typing import Iterable

from pydantic import TypeAdapter

from app.models import (
    PASSING_CORRECT_ANSWERS,
    AttemptResult,
    CurriculumUnit,
    LessonContent,
)


DATA_DIR = Path(__file__).parent / "data"
EXPLANATIONS_DIR = DATA_DIR / "grammar_explanations"


def load_curriculum() -> list[CurriculumUnit]:
    units = TypeAdapter(list[CurriculumUnit]).validate_json(
        (DATA_DIR / "curriculum.json").read_text(encoding="utf-8")
    )
    ids = [unit.id for unit in units]
    if len(set(ids)) != len(ids):
        raise ValueError("curriculum unit ids must be unique")
    return units


def load_sample_lesson() -> LessonContent:
    practice = json.loads(
        (DATA_DIR / "sample_practice.json").read_text(encoding="utf-8")
    )
    return LessonContent(
        unit_id="A1-01",
        explanation=load_explanation_markdown("A1-01"),
        **practice,
    )


def load_explanation_markdown(unit_id: str) -> str:
    if unit_id not in {unit.id for unit in load_curriculum()}:
        raise ValueError(f"unknown curriculum unit id: {unit_id}")

    path = EXPLANATIONS_DIR / f"{unit_id}.md"
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"missing grammar explanation for unit {unit_id}"
        ) from None
    if not content.strip():
        raise ValueError(f"empty grammar explanation for unit {unit_id}")
    return content


def next_unit(
    curriculum: Iterable[CurriculumUnit], attempts: Iterable[AttemptResult]
) -> CurriculumUnit | None:
    passed_ids = {
        attempt.unit_id
        for attempt in attempts
        if attempt.correct_answers >= PASSING_CORRECT_ANSWERS
    }
    return next((unit for unit in curriculum if unit.id not in passed_ids), None)
