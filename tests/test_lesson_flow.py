from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from app.curriculum import load_sample_lesson
from app.main import create_app
from app.service import GenerationInProgress


def test_start_saves_then_resumes_and_summary_uses_curriculum_total(tmp_path) -> None:
    app = create_app(tmp_path / "tutor.db")
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

    def slow_generator(unit):
        entered.set()
        assert release.wait(timeout=2)
        return load_sample_lesson().model_copy(update={"unit_id": unit.id})

    app = create_app(tmp_path / "tutor.db", slow_generator)
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
    app = create_app(tmp_path / "tutor.db")
    assert {route.path for route in app.routes} >= {
        "/api/summary",
        "/api/lessons/start",
        "/api/lessons/{lesson_id}",
    }
