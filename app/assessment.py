from collections.abc import Iterable, Mapping
from math import ceil

from app.models import (
    AnswerResult,
    AttemptResult,
    CurriculumUnit,
    LessonContent,
    LessonResult,
)


def grade_lesson(lesson: LessonContent, answers: Mapping[str, int]) -> LessonResult:
    exercise_ids = {exercise.id for exercise in lesson.exercises}
    if set(answers) != exercise_ids:
        raise ValueError("answers must contain every exercise id exactly once")

    results = []
    for exercise in lesson.exercises:
        selected = answers[exercise.id]
        if (
            not isinstance(selected, int)
            or isinstance(selected, bool)
            or selected not in range(len(exercise.options))
        ):
            raise ValueError(f"invalid option for exercise {exercise.id}")
        results.append(
            AnswerResult(
                exercise_id=exercise.id,
                practice_type=exercise.practice_type,
                selected_option=selected,
                selected_answer=exercise.options[selected],
                correct_option=exercise.correct_option,
                solution=exercise.options[exercise.correct_option],
                rationale=exercise.rationale,
                is_correct=selected == exercise.correct_option,
            )
        )

    correct_answers = sum(answer.is_correct for answer in results)
    return LessonResult(
        unit_id=lesson.unit_id,
        answers=results,
        correct_answers=correct_answers,
        total_exercises=len(lesson.exercises),
        percentage=score_percentage(correct_answers, len(lesson.exercises)),
        passed=correct_answers >= passing_correct_answers(len(lesson.exercises)),
    )


def passed_unit_ids(attempts: Iterable[AttemptResult]) -> set[str]:
    return {
        attempt.unit_id
        for attempt in attempts
        if attempt.correct_answers >= passing_correct_answers(attempt.total_exercises)
    }


def next_unit(
    curriculum: Iterable[CurriculumUnit], attempts: Iterable[AttemptResult]
) -> CurriculumUnit | None:
    passed = passed_unit_ids(attempts)
    return next((unit for unit in curriculum if unit.id not in passed), None)


def passing_correct_answers(total_exercises: int) -> int:
    return ceil(total_exercises * 5 / 6)


def score_percentage(correct_answers: int, total_exercises: int) -> int:
    return round(correct_answers / total_exercises * 100)
