import sqlite3

import pytest

from app.database import SCHEMA, connect, initialize_database


def test_database_initialization_is_repeatable_and_enforces_active_states(tmp_path) -> None:
    database_path = tmp_path / "tutor.db"
    initialize_database(database_path)
    initialize_database(database_path)

    with connect(database_path) as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert tables == {"lessons", "generation_calls"}

        lesson = (
            "lesson-1",
            "A1-01",
            "{}",
            "active",
            "2026-09-19T10:00:00+00:00",
        )
        connection.execute(
            """INSERT INTO lessons (id, unit_id, content_json, status, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            lesson,
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """INSERT INTO lessons (id, unit_id, content_json, status, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                ("lesson-2", "A1-01", "{}", "active", lesson[-1]),
            )

        connection.execute(
            """INSERT INTO generation_calls
               (id, generation_group_id, outcome, created_at)
               VALUES (?, ?, ?, ?)""",
            ("call-1", "group-1", "error", lesson[-1]),
        )
        assert connection.execute(
            "SELECT lesson_id FROM generation_calls WHERE id = 'call-1'"
        ).fetchone()["lesson_id"] is None


def test_database_expands_score_range_without_losing_old_lessons(tmp_path) -> None:
    database_path = tmp_path / "legacy.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            SCHEMA.replace(
                "correct_answers BETWEEN 0 AND 18",
                "correct_answers BETWEEN 0 AND 6",
            )
        )
        connection.execute(
            """INSERT INTO lessons
               (id, unit_id, content_json, status, correct_answers, created_at,
                completed_at)
               VALUES ('old', 'A1-01', '{}', 'completed', 6, 'created', 'done')"""
        )
        connection.execute(
            """INSERT INTO generation_calls
               (id, generation_group_id, lesson_id, outcome, created_at)
               VALUES ('call', 'group', 'old', 'succeeded', 'created')"""
        )

    initialize_database(database_path)

    with connect(database_path) as connection:
        assert connection.execute(
            "SELECT correct_answers FROM lessons WHERE id = 'old'"
        ).fetchone()["correct_answers"] == 6
        assert connection.execute(
            "SELECT lesson_id FROM generation_calls WHERE id = 'call'"
        ).fetchone()["lesson_id"] == "old"
        connection.execute(
            """INSERT INTO lessons
               (id, unit_id, content_json, status, correct_answers, created_at,
                completed_at)
               VALUES ('new', 'A1-02', '{}', 'completed', 18, 'created', 'done')"""
        )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
