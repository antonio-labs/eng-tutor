import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.assessment import (
    grade_lesson,
    next_unit,
    passed_unit_ids,
    score_percentage,
)
from app.course import A1Course, load_course
from app.database import connect, initialize_database
from app.generation import (
    GENERATION_UNAVAILABLE_MESSAGE,
    LessonGeneration,
    PracticeGenerator,
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


class LessonNotFound(Exception):
    pass


class LessonStateError(Exception):
    pass


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class TutorService:
    def __init__(
        self,
        database_path: Path,
        generator: PracticeGenerator | None,
        course: A1Course | None = None,
    ) -> None:
        self.database_path = database_path
        self.course = course or load_course()
        self.curriculum = self.course.units
        initialize_database(database_path)
        self.generation = LessonGeneration(database_path, generator)

    def summary(self) -> LearningSummary:
        with connect(self.database_path) as connection:
            attempts = self._attempts(connection)
            active = connection.execute(
                "SELECT id FROM lessons WHERE status = 'active'"
            ).fetchone()
        following = next_unit(self.curriculum, attempts)
        return LearningSummary(
            completed_units=len(passed_unit_ids(attempts)),
            total_units=len(self.curriculum),
            next_unit=following,
            active_lesson_id=active["id"] if active else None,
            path_completed=following is None,
            generation_available=self.generation.available,
            generation_unavailable_reason=(
                None
                if self.generation.available
                else GENERATION_UNAVAILABLE_MESSAGE
            ),
        )

    def start_or_resume(self) -> LessonSession | None:
        with connect(self.database_path) as connection:
            active = connection.execute(
                "SELECT * FROM lessons WHERE status = 'active'"
            ).fetchone()
            if active:
                return self._row_to_session(active)
            following = next_unit(self.curriculum, self._attempts(connection))

        if following is None:
            return None
        lesson_id = self.generation.create_or_resume(
            self.course.content_for(following.id)
        )
        lesson = self.get_lesson(lesson_id)
        if lesson is None:
            raise AssertionError("generated lesson must be persisted")
        return lesson

    def failed_generations(self) -> list[FailedGeneration]:
        return self.generation.failed_generations()

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
            history = []
            for row in rows:
                total_exercises = len(
                    LessonContent.model_validate_json(row["content_json"]).exercises
                )
                history.append(
                    HistoryItem(
                        id=row["id"],
                        unit=self._unit(row["unit_id"]),
                        status=row["status"],
                        correct_answers=row["correct_answers"],
                        total_exercises=(
                            total_exercises
                            if row["correct_answers"] is not None
                            else None
                        ),
                        percentage=(
                            score_percentage(row["correct_answers"], total_exercises)
                            if row["correct_answers"] is not None
                            else None
                        ),
                        created_at=row["created_at"],
                        finished_at=row["completed_at"] or row["discarded_at"],
                        cost=self._cost(connection, row["id"]),
                    )
                )
            return history

    def get_result(self, lesson_id: str) -> CompletedLesson:
        with connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
            ).fetchone()
            if row is None:
                raise LessonNotFound
            if row["status"] != "completed":
                raise LessonStateError("Il risultato è disponibile solo dopo l’invio.")
            content = LessonContent.model_validate_json(row["content_json"])
            return self._completed_lesson(
                row, content, json.loads(row["answers_json"]), connection
            )

    @staticmethod
    def _attempts(connection: sqlite3.Connection) -> list[AttemptResult]:
        rows = connection.execute(
            """SELECT unit_id, correct_answers, content_json FROM lessons
               WHERE status = 'completed'"""
        ).fetchall()
        return [
            AttemptResult(
                unit_id=row["unit_id"],
                correct_answers=row["correct_answers"],
                total_exercises=len(
                    LessonContent.model_validate_json(row["content_json"]).exercises
                ),
            )
            for row in rows
        ]

    def _row_to_session(self, row: sqlite3.Row) -> LessonSession:
        content = LessonContent.model_validate_json(row["content_json"])
        return LessonSession(
            id=row["id"],
            status=row["status"],
            unit=self._unit(row["unit_id"]),
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
        return CompletedLesson(
            id=row["id"],
            unit=self._unit(row["unit_id"]),
            result=grade_lesson(content, answers),
            completed_at=row["completed_at"],
            cost=self._cost(connection, row["id"]),
        )

    def _unit(self, unit_id: str) -> CurriculumUnit:
        return self.course.content_for(unit_id).unit

    @staticmethod
    def _cost(connection: sqlite3.Connection, lesson_id: str) -> CostSummary:
        row = connection.execute(
            """SELECT COUNT(*) AS calls, COUNT(cost_usd) AS known_calls,
                      SUM(cost_usd) AS known_usd
               FROM generation_calls WHERE lesson_id = ?""",
            (lesson_id,),
        ).fetchone()
        if row["known_calls"] == 0:
            return CostSummary(status="unavailable")
        return CostSummary(
            status="partial" if row["known_calls"] < row["calls"] else "known",
            known_usd=row["known_usd"],
        )
