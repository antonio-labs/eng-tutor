import sqlite3
from shutil import copytree

import pytest

from app.course import DATA_DIR, load_course, load_sample_lesson
from app.database import connect
from app.generation import CallMetrics, GenerationOutput, SampleGenerator
from app.main import create_app


def correct_answers() -> dict[str, int]:
    lesson = load_sample_lesson()
    return {exercise.id: exercise.correct_option for exercise in lesson.exercises}


def test_active_lesson_and_result_survive_restart_without_exposing_answers(tmp_path) -> None:
    database_path = tmp_path / "tutor.db"
    first_process = create_app(database_path, SampleGenerator()).state.tutor_service
    started = first_process.start_or_resume()
    assert started is not None

    restarted = create_app(database_path, SampleGenerator()).state.tutor_service
    resumed = restarted.start_or_resume()
    assert resumed is not None
    assert resumed.id == started.id
    assert "correct_option" not in resumed.model_dump_json()
    assert "rationale" not in resumed.model_dump_json()

    completed = restarted.submit_lesson(resumed.id, correct_answers())
    after_lost_response = create_app(
        database_path, SampleGenerator()
    ).state.tutor_service
    repeated = after_lost_response.submit_lesson(resumed.id, {"ignored": 0})

    assert repeated == completed
    assert after_lost_response.get_result(resumed.id) == completed


def test_database_save_error_leaves_generation_recoverable(tmp_path) -> None:
    database_path = tmp_path / "tutor.db"
    service = create_app(database_path, SampleGenerator()).state.tutor_service
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
        ).fetchone()[0] == "succeeded"
        connection.execute("DROP TRIGGER fail_lesson_save")

    assert service.start_or_resume() is not None


def test_discard_and_next_start_survive_restart(tmp_path) -> None:
    database_path = tmp_path / "tutor.db"
    service = create_app(database_path, SampleGenerator()).state.tutor_service
    lesson = service.start_or_resume()
    assert lesson is not None
    service.discard_lesson(lesson.id)

    restarted = create_app(database_path, SampleGenerator()).state.tutor_service
    replacement = restarted.start_or_resume()

    assert replacement is not None
    assert replacement.id != lesson.id
    assert replacement.unit.id == lesson.unit.id
    assert restarted.history()[0].status == "discarded"


def test_plain_text_historical_explanation_survives_restart(tmp_path) -> None:
    database_path = tmp_path / "tutor.db"
    historical_explanation = "Una spiegazione storica senza sintassi Markdown."
    historical_lesson = load_sample_lesson().model_copy(
        update={"explanation": historical_explanation}
    )

    class HistoricalGenerator:
        provider = "mock"
        model = "historical-sample"

        def generate_once(self, unit_content, timeout):
            return GenerationOutput(
                historical_lesson.model_copy(
                    update={"unit_id": unit_content.unit.id}
                ),
                CallMetrics(),
            )

    first_process = create_app(
        database_path, HistoricalGenerator()
    ).state.tutor_service
    started = first_process.start_or_resume()
    assert started is not None

    restarted = create_app(database_path, SampleGenerator()).state.tutor_service
    resumed = restarted.get_lesson(started.id)

    assert resumed is not None
    assert resumed.content.explanation == historical_explanation
    assert "correct_option" not in resumed.model_dump_json()
    assert "rationale" not in resumed.model_dump_json()


def test_saved_explanation_is_immutable_snapshot(tmp_path) -> None:
    data_dir = tmp_path / "course-data"
    copytree(DATA_DIR, data_dir)
    explanations_dir = data_dir / "grammar_explanations"
    source = explanations_dir / "A1-01.md"
    original = source.read_text(encoding="utf-8")
    selected_course = load_course(data_dir)

    database_path = tmp_path / "tutor.db"
    first_process = create_app(
        database_path,
        SampleGenerator(),
        selected_course,
    ).state.tutor_service
    started = first_process.start_or_resume()
    assert started is not None

    source.write_text(
        "### Quando si usa\n\nVersione modificata dopo il salvataggio.",
        encoding="utf-8",
    )
    restarted = create_app(database_path, SampleGenerator()).state.tutor_service
    resumed = restarted.get_lesson(started.id)

    assert resumed is not None
    assert resumed.content.explanation == original.strip()
