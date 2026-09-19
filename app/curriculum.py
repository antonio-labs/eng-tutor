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


def load_curriculum() -> list[CurriculumUnit]:
    units = TypeAdapter(list[CurriculumUnit]).validate_json(
        (DATA_DIR / "curriculum.json").read_text(encoding="utf-8")
    )
    ids = [unit.id for unit in units]
    if len(set(ids)) != len(ids):
        raise ValueError("curriculum unit ids must be unique")
    return units


def load_sample_lesson() -> LessonContent:
    return LessonContent.model_validate_json(
        (DATA_DIR / "sample_lesson.json").read_text(encoding="utf-8")
    )


def next_unit(
    curriculum: Iterable[CurriculumUnit], attempts: Iterable[AttemptResult]
) -> CurriculumUnit | None:
    passed_ids = {
        attempt.unit_id
        for attempt in attempts
        if attempt.correct_answers >= PASSING_CORRECT_ANSWERS
    }
    return next((unit for unit in curriculum if unit.id not in passed_ids), None)
