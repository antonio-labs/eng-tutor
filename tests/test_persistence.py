import sqlite3

import pytest

from app.curriculum import load_sample_lesson
from app.database import connect
from app.main import create_app
from app.service import generate_sample


def correct_answers() -> dict[str, int]:
    lesson = load_sample_lesson()
    return {exercise.id: exercise.correct_option for exercise in lesson.exercises}


def test_active_lesson_and_result_survive_restart_without_exposing_answers(tmp_path) -> None:
    database_path = tmp_path / "tutor.db"
    first_process = create_app(database_path, generate_sample).state.tutor_service
    started = first_process.start_or_resume()
    assert started is not None

    restarted = create_app(database_path, generate_sample).state.tutor_service
    resumed = restarted.start_or_resume()
    assert resumed is not None
    assert resumed.id == started.id
    assert "correct_option" not in resumed.model_dump_json()
    assert "rationale" not in resumed.model_dump_json()

    completed = restarted.submit_lesson(resumed.id, correct_answers())
    after_lost_response = create_app(database_path, generate_sample).state.tutor_service
    repeated = after_lost_response.submit_lesson(resumed.id, {"ignored": 0})

    assert repeated == completed
    assert after_lost_response.get_result(resumed.id) == completed


def test_database_save_error_leaves_generation_recoverable(tmp_path) -> None:
    database_path = tmp_path / "tutor.db"
    service = create_app(database_path, generate_sample).state.tutor_service
    with connect(database_path) as connection:
        connection.execute(
            """CREATE TRIGGER fail_lesson_save BEFORE INSERT ON lessons
               BEGIN SELECT RAISE(ABORT, 'simulated disk error'); END"""
        )

    with pytest.raises(sqlite3.IntegrityError, match="simulated disk error"):
        service.start_or_resume()

    with connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM lessons").fetchone()[0] == 0
        assert connection.execute(
            "SELECT outcome FROM generation_calls"
        ).fetchone()[0] == "error"
        connection.execute("DROP TRIGGER fail_lesson_save")

    assert service.start_or_resume() is not None


def test_discard_and_next_start_survive_restart(tmp_path) -> None:
    database_path = tmp_path / "tutor.db"
    service = create_app(database_path, generate_sample).state.tutor_service
    lesson = service.start_or_resume()
    assert lesson is not None
    service.discard_lesson(lesson.id)

    restarted = create_app(database_path, generate_sample).state.tutor_service
    replacement = restarted.start_or_resume()

    assert replacement is not None
    assert replacement.id != lesson.id
    assert replacement.unit.id == lesson.unit.id
    assert restarted.history()[0].status == "discarded"
