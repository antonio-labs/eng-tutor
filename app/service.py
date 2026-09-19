import json
import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.curriculum import load_curriculum, load_sample_lesson, next_unit
from app.database import connect, initialize_database
from app.grading import grade_lesson
from app.models import (
    AttemptResult,
    CompletedLesson,
    CurriculumUnit,
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
        generator: Callable[[CurriculumUnit], LessonContent] = generate_sample,
    ) -> None:
        self.database_path = database_path
        self.generator = generator
        self.curriculum = load_curriculum()
        initialize_database(database_path)

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

            call_id = str(uuid4())
            group_id = str(uuid4())
            try:
                connection.execute(
                    """INSERT INTO generation_calls
                       (id, generation_group_id, provider, model, outcome, created_at)
                       VALUES (?, ?, 'mock', 'sample-lesson', 'in_progress', ?)""",
                    (call_id, group_id, utc_now()),
                )
            except sqlite3.IntegrityError as error:
                raise GenerationInProgress from error

        try:
            content = self.generator(unit)
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
                       SET lesson_id = ?, outcome = 'succeeded', cost_usd = 0,
                           pricing_reference = 'simulated: no external call', finished_at = ?
                       WHERE id = ?""",
                    (lesson_id, utc_now(), call_id),
                )
                row = connection.execute(
                    "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
                ).fetchone()
            return self._row_to_session(row)
        except Exception:
            with connect(self.database_path) as connection:
                connection.execute(
                    """UPDATE generation_calls
                       SET outcome = 'error', finished_at = ? WHERE id = ?""",
                    (utc_now(), call_id),
                )
            raise

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
                return self._completed_lesson(row, content, saved_answers)

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
            return self._completed_lesson(completed_row, content, answers)

    @staticmethod
    def _attempts(connection: sqlite3.Connection) -> list[AttemptResult]:
        rows = connection.execute(
            """SELECT unit_id, correct_answers FROM lessons
               WHERE status = 'completed'"""
        ).fetchall()
        return [AttemptResult(**dict(row)) for row in rows]

    def _row_to_session(self, row: sqlite3.Row) -> LessonSession:
        content = LessonContent.model_validate_json(row["content_json"])
        unit = next(unit for unit in self.curriculum if unit.id == row["unit_id"])
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
    ) -> CompletedLesson:
        unit = next(unit for unit in self.curriculum if unit.id == row["unit_id"])
        return CompletedLesson(
            id=row["id"],
            unit=unit,
            result=grade_lesson(content, answers),
            completed_at=row["completed_at"],
        )
