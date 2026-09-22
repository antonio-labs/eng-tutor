from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from app.course import load_sample_lesson
from app.generation import (
    CallMetrics,
    GenerationInProgress,
    GenerationOutput,
    SampleGenerator,
)
from app.main import create_app
from app.service import LessonStateError


def test_start_saves_then_resumes_and_summary_uses_curriculum_total(tmp_path) -> None:
    app = create_app(tmp_path / "tutor.db", SampleGenerator())
    service = app.state.tutor_service

    first = service.start_or_resume()
    resumed = service.start_or_resume()
    summary = service.summary()

    assert first is not None
    assert resumed is not None
    assert resumed.id == first.id
    assert summary.total_units == 36
    assert summary.completed_units == 0
    assert summary.active_lesson_id == first.id
    assert summary.next_unit and summary.next_unit.id == "A1-01"
    assert "correct_option" not in first.model_dump_json()
    assert "rationale" not in first.model_dump_json()


def test_concurrent_starts_do_not_run_two_generators(tmp_path) -> None:
    entered = Event()
    release = Event()

    class SlowGenerator:
        provider = "mock"
        model = "slow-sample"

        def generate_once(self, unit_content, timeout):
            entered.set()
            assert release.wait(timeout=2)
            return GenerationOutput(
                load_sample_lesson(unit_content),
                CallMetrics(),
            )

    app = create_app(tmp_path / "tutor.db", SlowGenerator())
    service = app.state.tutor_service

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(service.start_or_resume)
        assert entered.wait(timeout=2)
        second = pool.submit(service.start_or_resume)
        with pytest.raises(GenerationInProgress):
            second.result(timeout=2)
        release.set()
        assert first.result(timeout=2) is not None


def test_lesson_routes_are_exposed(tmp_path) -> None:
    app = create_app(tmp_path / "tutor.db", SampleGenerator())
    assert {route.path for route in app.routes} >= {
        "/api/summary",
        "/api/lessons/start",
        "/api/lessons/{lesson_id}",
        "/api/lessons/{lesson_id}/submit",
        "/api/lessons/{lesson_id}/discard",
        "/api/lessons/{lesson_id}/result",
        "/api/history",
    }


def test_submission_is_validated_saved_atomically_and_idempotent(tmp_path) -> None:
    app = create_app(tmp_path / "tutor.db", SampleGenerator())
    service = app.state.tutor_service
    lesson = service.start_or_resume()
    assert lesson is not None
    private_lesson = load_sample_lesson()
    answers = {
        exercise.id: exercise.correct_option for exercise in private_lesson.exercises
    }

    with pytest.raises(ValueError):
        service.submit_lesson(lesson.id, {"q1": 0})

    completed = service.submit_lesson(lesson.id, answers)
    duplicate = service.submit_lesson(
        lesson.id,
        {
            exercise.id: (exercise.correct_option + 1) % 3
            for exercise in private_lesson.exercises
        },
    )

    assert completed.result.correct_answers == 6
    assert completed.result.total_exercises == 6
    assert duplicate == completed
    assert service.summary().completed_units == 1
    assert service.summary().next_unit and service.summary().next_unit.id == "A1-02"


def test_discard_preserves_cost_and_does_not_advance(tmp_path) -> None:
    app = create_app(tmp_path / "tutor.db", SampleGenerator())
    service = app.state.tutor_service
    first = service.start_or_resume()
    assert first is not None

    discarded = service.discard_lesson(first.id)
    repeated = service.discard_lesson(first.id)
    replacement = service.start_or_resume()

    assert repeated == discarded
    assert discarded.cost.status == "known"
    assert discarded.cost.known_usd == 0
    assert replacement is not None
    assert replacement.id != first.id
    assert replacement.unit.id == first.unit.id
    with pytest.raises(LessonStateError):
        service.submit_lesson(first.id, {})


def test_history_reopens_completed_results_and_rejects_completed_discard(tmp_path) -> None:
    app = create_app(tmp_path / "tutor.db", SampleGenerator())
    service = app.state.tutor_service
    lesson = service.start_or_resume()
    assert lesson is not None
    private_lesson = load_sample_lesson()
    answers = {
        exercise.id: exercise.correct_option for exercise in private_lesson.exercises
    }
    completed = service.submit_lesson(lesson.id, answers)

    assert service.get_result(lesson.id) == completed
    assert service.history()[0].status == "completed"
    assert service.history()[0].correct_answers == 6
    assert service.history()[0].total_exercises == 6
    with pytest.raises(LessonStateError):
        service.discard_lesson(lesson.id)
