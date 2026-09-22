from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
OptionIndex = Annotated[int, Field(strict=True, ge=0, le=2)]
EXERCISES_PER_LESSON = 6
PASSING_CORRECT_ANSWERS = 5


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CurriculumUnit(Model):
    id: NonEmptyText
    title: NonEmptyText
    objective: NonEmptyText


class CourseUnitContent(Model):
    unit: CurriculumUnit
    explanation: NonEmptyText


class LessonExample(Model):
    sentence: NonEmptyText
    note: NonEmptyText


class Exercise(Model):
    id: NonEmptyText
    question: NonEmptyText
    options: list[NonEmptyText] = Field(min_length=3, max_length=3)
    correct_option: OptionIndex
    rationale: NonEmptyText

    @model_validator(mode="after")
    def options_are_distinct(self) -> "Exercise":
        if len(set(self.options)) != 3:
            raise ValueError("exercise options must be distinct")
        return self


class LessonContent(Model):
    unit_id: NonEmptyText
    explanation: NonEmptyText
    examples: list[LessonExample] = Field(min_length=3, max_length=3)
    exercises: list[Exercise] = Field(
        min_length=EXERCISES_PER_LESSON,
        max_length=EXERCISES_PER_LESSON,
    )

    @model_validator(mode="after")
    def exercise_ids_are_unique(self) -> "LessonContent":
        ids = [exercise.id for exercise in self.exercises]
        if len(set(ids)) != len(ids):
            raise ValueError("exercise ids must be unique")
        return self

    def for_browser(self) -> "LessonView":
        return LessonView(
            unit_id=self.unit_id,
            explanation=self.explanation,
            examples=self.examples,
            exercises=[
                PublicExercise(id=item.id, question=item.question, options=item.options)
                for item in self.exercises
            ],
        )


class PublicExercise(Model):
    id: NonEmptyText
    question: NonEmptyText
    options: list[NonEmptyText] = Field(min_length=3, max_length=3)


class LessonTiming(Model):
    explanation_and_examples_minutes: Literal[3] = 3
    exercises_minutes: Literal[9] = 9
    review_minutes: Literal[3] = 3
    total_minutes: Literal[15] = 15


class LessonView(Model):
    unit_id: NonEmptyText
    explanation: NonEmptyText
    examples: list[LessonExample]
    exercises: list[PublicExercise]
    timing: LessonTiming = Field(default_factory=LessonTiming)


class LessonSession(Model):
    id: NonEmptyText
    status: Literal["active", "completed", "discarded"]
    unit: CurriculumUnit
    content: LessonView
    created_at: NonEmptyText


class LearningSummary(Model):
    completed_units: int = Field(ge=0)
    total_units: int = Field(gt=0)
    next_unit: CurriculumUnit | None
    active_lesson_id: str | None
    path_completed: bool
    generation_available: bool
    generation_unavailable_reason: str | None = None


class AnswerResult(Model):
    exercise_id: NonEmptyText
    selected_option: OptionIndex
    selected_answer: NonEmptyText
    correct_option: OptionIndex
    solution: NonEmptyText
    rationale: NonEmptyText
    is_correct: bool


class LessonResult(Model):
    unit_id: NonEmptyText
    answers: list[AnswerResult]
    correct_answers: int = Field(ge=0, le=EXERCISES_PER_LESSON)
    total_exercises: int = Field(gt=0)
    percentage: int = Field(ge=0, le=100)
    passed: bool


class AnswerSubmission(Model):
    answers: dict[NonEmptyText, OptionIndex]


class CostSummary(Model):
    status: Literal["known", "partial", "unavailable"]
    known_usd: float | None = Field(default=None, ge=0)


class CompletedLesson(Model):
    id: NonEmptyText
    status: Literal["completed"] = "completed"
    unit: CurriculumUnit
    result: LessonResult
    completed_at: NonEmptyText
    cost: CostSummary


class DiscardedLesson(Model):
    id: NonEmptyText
    status: Literal["discarded"] = "discarded"
    unit: CurriculumUnit
    discarded_at: NonEmptyText
    cost: CostSummary


class HistoryItem(Model):
    id: NonEmptyText
    unit: CurriculumUnit
    status: Literal["completed", "discarded"]
    correct_answers: int | None = Field(
        default=None, ge=0, le=EXERCISES_PER_LESSON
    )
    total_exercises: int | None = Field(default=None, gt=0)
    percentage: int | None = Field(default=None, ge=0, le=100)
    created_at: NonEmptyText
    finished_at: NonEmptyText
    cost: CostSummary


class FailedGeneration(Model):
    generation_group_id: NonEmptyText
    created_at: NonEmptyText
    provider: NonEmptyText
    model: NonEmptyText
    calls: int = Field(gt=0)
    outcomes: list[NonEmptyText]
    cost: CostSummary


class AttemptResult(Model):
    unit_id: NonEmptyText
    correct_answers: int = Field(ge=0, le=EXERCISES_PER_LESSON)
