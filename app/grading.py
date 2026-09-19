from collections.abc import Mapping

from app.models import (
    PASSING_CORRECT_ANSWERS,
    AnswerResult,
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
        percentage=round(correct_answers / len(results) * 100),
        passed=correct_answers >= PASSING_CORRECT_ANSWERS,
    )
