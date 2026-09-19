import json
import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from uuid import uuid4

from app.curriculum import load_curriculum, load_sample_lesson, next_unit
from app.database import connect, initialize_database
from app.grading import grade_lesson
from app.generation import (
    CallMetrics,
    GenerationFailed,
    GenerationOutput,
    GenerationUnavailable,
    InvalidGenerationResponse,
    classify_generation_error,
)
from app.models import (
    AttemptResult,
    CompletedLesson,
    CostSummary,
    CurriculumUnit,
    DiscardedLesson,
    FailedGeneration,
    HistoryItem,
    LearningSummary,
    LessonContent,
    LessonSession,
)


class GenerationInProgress(Exception):
    pass


class LessonNotFound(Exception):
    pass


class LessonStateError(Exception):
    pass


MAX_GENERATION_CALLS = 2
GENERATION_DEADLINE_SECONDS = 60


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def generate_sample(unit: CurriculumUnit) -> LessonContent:
    lesson = load_sample_lesson()
    return lesson.model_copy(
        update={
            "unit_id": unit.id,
            "explanation": (
                "CONTENUTO DI ESEMPIO (nessuna chiamata AI). " + lesson.explanation
            ),
        }
    )


class TutorService:
    def __init__(
        self,
        database_path: Path,
        generator: Callable[[CurriculumUnit], LessonContent] | None,
    ) -> None:
        self.database_path = database_path
        self.generator = generator
        self.curriculum = load_curriculum()
        initialize_database(database_path)
        with connect(database_path) as connection:
            connection.execute(
                """UPDATE generation_calls
                   SET outcome = 'unknown', finished_at = ?
                   WHERE outcome = 'in_progress'""",
                (utc_now(),),
            )

    def summary(self) -> LearningSummary:
        with connect(self.database_path) as connection:
            attempts = self._attempts(connection)
            active = connection.execute(
                "SELECT id FROM lessons WHERE status = 'active'"
            ).fetchone()
        following = next_unit(self.curriculum, attempts)
        passed = {
            attempt.unit_id for attempt in attempts if attempt.correct_answers >= 5
        }
        return LearningSummary(
            completed_units=len(passed),
            total_units=len(self.curriculum),
            next_unit=following,
            active_lesson_id=active["id"] if active else None,
            path_completed=following is None,
            generation_available=self.generator is not None,
            generation_unavailable_reason=(
                None
                if self.generator is not None
                else "Configura LLM_MODEL e LLM_API_KEY per creare una nuova lezione."
            ),
        )

    def start_or_resume(self) -> LessonSession | None:
        with connect(self.database_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            active = connection.execute(
                "SELECT * FROM lessons WHERE status = 'active'"
            ).fetchone()
            if active:
                return self._row_to_session(active)

            unit = next_unit(self.curriculum, self._attempts(connection))
            if unit is None:
                return None
            if self.generator is None:
                raise GenerationUnavailable(
                    "Configura LLM_MODEL e LLM_API_KEY per creare una nuova lezione."
                )

            group_id = str(uuid4())
            try:
                call_id = self._insert_generation_call(connection, group_id)
            except sqlite3.IntegrityError as error:
                raise GenerationInProgress from error

        generated = False
        metrics = CallMetrics()
        try:
            content, call_id, metrics = self._generate_content(
                unit, group_id, call_id
            )
            generated = True
            lesson_id = str(uuid4())
            with connect(self.database_path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """INSERT INTO lessons
                       (id, unit_id, content_json, status, created_at)
                       VALUES (?, ?, ?, 'active', ?)""",
                    (
                        lesson_id,
                        unit.id,
                        content.model_dump_json(),
                        utc_now(),
                    ),
                )
                connection.execute(
                    """UPDATE generation_calls
                       SET lesson_id = ? WHERE generation_group_id = ?""",
                    (lesson_id, group_id),
                )
                connection.execute(
                    """UPDATE generation_calls
                       SET outcome = 'succeeded',
                           prompt_tokens = ?, completion_tokens = ?, total_tokens = ?,
                           cost_usd = CASE WHEN provider = 'mock' THEN 0 ELSE ? END,
                           pricing_reference = CASE WHEN provider = 'mock'
                               THEN 'simulated: no external call' ELSE ? END,
                           finished_at = ?
                       WHERE id = ?""",
                    (
                        metrics.prompt_tokens,
                        metrics.completion_tokens,
                        metrics.total_tokens,
                        metrics.cost_usd,
                        metrics.pricing_reference,
                        utc_now(),
                        call_id,
                    ),
                )
                row = connection.execute(
                    "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
                ).fetchone()
            return self._row_to_session(row)
        except Exception:
            if generated:
                self._finish_generation_call(
                    call_id, "succeeded", metrics=metrics
                )
            raise

    def _generate_content(
        self, unit: CurriculumUnit, group_id: str, call_id: str
    ) -> tuple[LessonContent, str, CallMetrics]:
        generate_once = getattr(self.generator, "generate_once", None)
        max_calls = MAX_GENERATION_CALLS if callable(generate_once) else 1
        deadline = monotonic() + GENERATION_DEADLINE_SECONDS

        for attempt in range(max_calls):
            remaining = deadline - monotonic()
            try:
                if remaining <= 0:
                    raise TimeoutError
                output = (
                    generate_once(unit, timeout=remaining)
                    if callable(generate_once)
                    else self.generator(unit)
                )
                if isinstance(output, GenerationOutput):
                    return output.content, call_id, output.metrics
                return output, call_id, CallMetrics()
            except Exception as error:
                cause = (
                    error.cause
                    if isinstance(error, InvalidGenerationResponse)
                    else error
                )
                metrics = (
                    error.metrics
                    if isinstance(error, InvalidGenerationResponse)
                    else CallMetrics()
                )
                disposition = classify_generation_error(cause)
                self._finish_generation_call(
                    call_id,
                    disposition.outcome,
                    type(cause).__name__,
                    metrics,
                )
                can_retry = (
                    disposition.retryable
                    and attempt + 1 < max_calls
                    and monotonic() < deadline
                )
                if not can_retry:
                    raise GenerationFailed(disposition.user_message) from error
                with connect(self.database_path) as connection:
                    call_id = self._insert_generation_call(connection, group_id)

        raise AssertionError("generation loop must return or raise")

    def _insert_generation_call(
        self, connection: sqlite3.Connection, group_id: str
    ) -> str:
        call_id = str(uuid4())
        connection.execute(
            """INSERT INTO generation_calls
               (id, generation_group_id, provider, model, outcome, created_at)
               VALUES (?, ?, ?, ?, 'in_progress', ?)""",
            (
                call_id,
                group_id,
                getattr(self.generator, "provider", "mock"),
                getattr(self.generator, "model", "sample-lesson"),
                utc_now(),
            ),
        )
        return call_id

    def _finish_generation_call(
        self,
        call_id: str,
        outcome: str,
        error_message: str | None = None,
        metrics: CallMetrics = CallMetrics(),
    ) -> None:
        with connect(self.database_path) as connection:
            connection.execute(
                """UPDATE generation_calls
                   SET outcome = ?, error_message = ?, finished_at = ?,
                       prompt_tokens = ?, completion_tokens = ?, total_tokens = ?,
                       cost_usd = ?, pricing_reference = ?
                   WHERE id = ? AND outcome = 'in_progress'""",
                (
                    outcome,
                    error_message,
                    utc_now(),
                    metrics.prompt_tokens,
                    metrics.completion_tokens,
                    metrics.total_tokens,
                    metrics.cost_usd,
                    metrics.pricing_reference,
                    call_id,
                ),
            )

    def failed_generations(self) -> list[FailedGeneration]:
        with connect(self.database_path) as connection:
            rows = connection.execute(
                """SELECT generation_group_id, MIN(created_at) AS created_at,
                          MAX(provider) AS provider, MAX(model) AS model,
                          GROUP_CONCAT(outcome) AS outcomes,
                          COUNT(*) AS calls, COUNT(cost_usd) AS known_calls,
                          SUM(cost_usd) AS known_usd
                   FROM generation_calls
                   WHERE lesson_id IS NULL AND outcome != 'in_progress'
                   GROUP BY generation_group_id
                   ORDER BY created_at DESC"""
            ).fetchall()
        return [
            FailedGeneration(
                generation_group_id=row["generation_group_id"],
                created_at=row["created_at"],
                provider=row["provider"] or "non disponibile",
                model=row["model"] or "non disponibile",
                calls=row["calls"],
                outcomes=row["outcomes"].split(","),
                cost=self._cost_from_counts(row),
            )
            for row in rows
        ]

    def get_lesson(self, lesson_id: str) -> LessonSession | None:
        with connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
            ).fetchone()
        return self._row_to_session(row) if row else None

    def submit_lesson(
        self, lesson_id: str, answers: dict[str, int]
    ) -> CompletedLesson:
        with connect(self.database_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
            ).fetchone()
            if row is None:
                raise LessonNotFound
            if row["status"] == "discarded":
                raise LessonStateError("Una lezione scartata non può essere inviata.")

            content = LessonContent.model_validate_json(row["content_json"])
            if row["status"] == "completed":
                saved_answers = json.loads(row["answers_json"])
                return self._completed_lesson(row, content, saved_answers, connection)

            result = grade_lesson(content, answers)
            completed_at = utc_now()
            connection.execute(
                """UPDATE lessons
                   SET status = 'completed', answers_json = ?, correct_answers = ?,
                       completed_at = ?
                   WHERE id = ? AND status = 'active'""",
                (
                    json.dumps(answers, separators=(",", ":"), sort_keys=True),
                    result.correct_answers,
                    completed_at,
                    lesson_id,
                ),
            )
            completed_row = connection.execute(
                "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
            ).fetchone()
            return self._completed_lesson(completed_row, content, answers, connection)

    def discard_lesson(self, lesson_id: str) -> DiscardedLesson:
        with connect(self.database_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
            ).fetchone()
            if row is None:
                raise LessonNotFound
            if row["status"] == "completed":
                raise LessonStateError("Una lezione completata non può essere scartata.")
            if row["status"] == "active":
                connection.execute(
                    """UPDATE lessons SET status = 'discarded', discarded_at = ?
                       WHERE id = ?""",
                    (utc_now(), lesson_id),
                )
                row = connection.execute(
                    "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
                ).fetchone()
            return DiscardedLesson(
                id=row["id"],
                unit=self._unit(row["unit_id"]),
                discarded_at=row["discarded_at"],
                cost=self._cost(connection, lesson_id),
            )

    def history(self) -> list[HistoryItem]:
        with connect(self.database_path) as connection:
            rows = connection.execute(
                """SELECT * FROM lessons WHERE status IN ('completed', 'discarded')
                   ORDER BY COALESCE(completed_at, discarded_at) DESC"""
            ).fetchall()
            return [
                HistoryItem(
                    id=row["id"],
                    unit=self._unit(row["unit_id"]),
                    status=row["status"],
                    correct_answers=row["correct_answers"],
                    percentage=(
                        round(row["correct_answers"] / 6 * 100)
                        if row["correct_answers"] is not None
                        else None
                    ),
                    created_at=row["created_at"],
                    finished_at=row["completed_at"] or row["discarded_at"],
                    cost=self._cost(connection, row["id"]),
                )
                for row in rows
            ]

    def get_result(self, lesson_id: str) -> CompletedLesson:
        with connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
            ).fetchone()
            if row is None:
                raise LessonNotFound
            if row["status"] != "completed":
                raise LessonStateError("Il risultato è disponibile solo dopo l'invio.")
            content = LessonContent.model_validate_json(row["content_json"])
            return self._completed_lesson(
                row, content, json.loads(row["answers_json"]), connection
            )

    @staticmethod
    def _attempts(connection: sqlite3.Connection) -> list[AttemptResult]:
        rows = connection.execute(
            """SELECT unit_id, correct_answers FROM lessons
               WHERE status = 'completed'"""
        ).fetchall()
        return [AttemptResult(**dict(row)) for row in rows]

    def _row_to_session(self, row: sqlite3.Row) -> LessonSession:
        content = LessonContent.model_validate_json(row["content_json"])
        unit = self._unit(row["unit_id"])
        return LessonSession(
            id=row["id"],
            status=row["status"],
            unit=unit,
            content=content.for_browser(),
            created_at=row["created_at"],
        )

    def _completed_lesson(
        self,
        row: sqlite3.Row,
        content: LessonContent,
        answers: dict[str, int],
        connection: sqlite3.Connection,
    ) -> CompletedLesson:
        unit = self._unit(row["unit_id"])
        return CompletedLesson(
            id=row["id"],
            unit=unit,
            result=grade_lesson(content, answers),
            completed_at=row["completed_at"],
            cost=self._cost(connection, row["id"]),
        )

    def _unit(self, unit_id: str) -> CurriculumUnit:
        return next(unit for unit in self.curriculum if unit.id == unit_id)

    @staticmethod
    def _cost(connection: sqlite3.Connection, lesson_id: str) -> CostSummary:
        row = connection.execute(
            """SELECT COUNT(*) AS calls, COUNT(cost_usd) AS known_calls,
                      SUM(cost_usd) AS known_usd
               FROM generation_calls WHERE lesson_id = ?""",
            (lesson_id,),
        ).fetchone()
        return TutorService._cost_from_counts(row)

    @staticmethod
    def _cost_from_counts(row: sqlite3.Row) -> CostSummary:
        if row["known_calls"] == 0:
            return CostSummary(status="unavailable")
        return CostSummary(
            status="partial" if row["known_calls"] < row["calls"] else "known",
            known_usd=row["known_usd"],
        )
