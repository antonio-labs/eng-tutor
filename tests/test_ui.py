import json
from pathlib import Path
from uuid import uuid4

from app.course import load_course, load_sample_lesson
from app.database import connect
from app.generation import SampleGenerator
from app.main import create_app
from app.service import utc_now


STATIC_DIR = Path(__file__).parents[1] / "app" / "static"


def test_app_serves_three_view_frontend(tmp_path) -> None:
    app = create_app(tmp_path / "tutor.db", SampleGenerator())
    paths = {route.path for route in app.routes}
    html = (STATIC_DIR / "index.html").read_text()
    javascript = (STATIC_DIR / "app.js").read_text()

    assert {"/", "/static", "/api/health"} <= paths
    assert "#app" in javascript
    assert "renderHome" in javascript
    assert "renderLesson" in javascript
    assert "renderResult" in javascript
    assert "localStorage.setItem" in javascript
    assert "localStorage.removeItem" in javascript
    assert "button(\"Riprova\"" in javascript
    assert "renderExplanationMarkdown" in javascript
    assert all(
        practice_type in javascript
        for practice_type in [
            "form_choice",
            "context_completion",
            "error_correction",
        ]
    )
    assert "createTextNode" in javascript
    assert all(
        tag in javascript
        for tag in ['"h3"', '"ul"', '"blockquote"', '"strong"', '"code"']
    )
    assert "innerHTML" not in javascript
    assert "correct_answers}/6" not in javascript
    assert "—" not in html + javascript


def test_separate_database_can_render_completed_curriculum_state(tmp_path) -> None:
    database_path = tmp_path / "completed-curriculum.db"
    service = create_app(database_path, SampleGenerator()).state.tutor_service
    lesson = load_sample_lesson()
    answers = {
        exercise.id: exercise.correct_option for exercise in lesson.exercises
    }
    correct_answers = len(lesson.exercises)
    with connect(database_path) as connection:
        for unit in load_course().units:
            content = lesson.model_copy(update={"unit_id": unit.id})
            connection.execute(
                """INSERT INTO lessons
                   (id, unit_id, content_json, status, answers_json,
                    correct_answers, created_at, completed_at)
                   VALUES (?, ?, ?, 'completed', ?, ?, ?, ?)""",
                (
                    str(uuid4()),
                    unit.id,
                    content.model_dump_json(),
                    json.dumps(answers),
                    correct_answers,
                    utc_now(),
                    utc_now(),
                ),
            )

    summary = service.summary()
    assert summary.path_completed is True
    assert summary.completed_units == summary.total_units == 36
