import json
from types import SimpleNamespace

import pytest
from litellm.exceptions import AuthenticationError, RateLimitError, Timeout
from pydantic import ValidationError

from app.curriculum import load_curriculum, load_sample_lesson
from app.database import connect, initialize_database
from app.generation import (
    GenerationFailed,
    GenerationUnavailable,
    LLMConfig,
    LiteLLMGenerator,
)
from app.main import create_app
from app.models import LessonContent
from app.service import TutorService, generate_sample, utc_now


class SequenceGenerator:
    provider = "test-provider"
    model = "test-model"

    def __init__(self, effects) -> None:
        self.effects = iter(effects)
        self.calls = 0
        self.timeouts = []

    def generate_once(self, unit, timeout):
        self.calls += 1
        self.timeouts.append(timeout)
        effect = next(self.effects)
        if isinstance(effect, Exception):
            raise effect
        return effect.model_copy(update={"unit_id": unit.id})


def test_llm_configuration_reads_backend_environment(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MODEL", "provider/model")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_API_BASE", "https://example.test/v1")

    generator = LiteLLMGenerator.from_env()

    assert generator.config == LLMConfig(
        model="provider/model",
        api_key="test-key",
        api_base="https://example.test/v1",
    )
    assert generator.provider == "provider"


def test_missing_configuration_blocks_only_new_generation(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_BASE", raising=False)
    database_path = tmp_path / "tutor.db"

    configured_for_test = create_app(database_path, generate_sample).state.tutor_service
    saved = configured_for_test.start_or_resume()
    assert saved is not None

    offline = create_app(database_path).state.tutor_service
    summary = offline.summary()

    assert summary.generation_available is False
    assert summary.generation_unavailable_reason
    assert offline.get_lesson(saved.id) is not None
    assert offline.start_or_resume().id == saved.id

    offline.discard_lesson(saved.id)
    with pytest.raises(GenerationUnavailable):
        offline.start_or_resume()


@pytest.mark.parametrize(
    ("native_schema", "expected_format"),
    [(True, LessonContent), (False, {"type": "json_object"})],
)
def test_generation_sends_only_lesson_context_and_validates_json(
    monkeypatch, native_schema, expected_format
) -> None:
    captured = {}
    unit = load_curriculum()[0]
    payload = load_sample_lesson().model_dump_json()

    def fake_completion(**kwargs):
        captured.update(kwargs)
        message = SimpleNamespace(content=payload)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    monkeypatch.setattr("app.generation.completion", fake_completion)
    monkeypatch.setattr(
        "app.generation.supports_response_schema", lambda **_: native_schema
    )
    generator = LiteLLMGenerator(LLMConfig("provider/model", "test-key"))

    lesson = generator(unit)
    sent = json.loads(captured["messages"][0]["content"])

    assert lesson == load_sample_lesson()
    assert captured["response_format"] == expected_format
    assert set(sent) == {"level", "unit", "languages", "format"}
    assert sent["level"] == "A1"
    assert sent["unit"] == unit.model_dump()
    assert "history" not in captured["messages"][0]["content"].lower()
    assert all(exercise.rationale for exercise in lesson.exercises)


def test_invalid_output_retries_once_and_records_both_calls(tmp_path) -> None:
    try:
        LessonContent.model_validate({})
    except ValidationError as invalid_output:
        generator = SequenceGenerator([invalid_output, load_sample_lesson()])

    service = TutorService(tmp_path / "tutor.db", generator)
    lesson = service.start_or_resume()

    assert lesson is not None
    assert generator.calls == 2
    assert all(0 < timeout <= 60 for timeout in generator.timeouts)
    with connect(service.database_path) as connection:
        calls = connection.execute(
            "SELECT outcome, lesson_id FROM generation_calls ORDER BY created_at"
        ).fetchall()
    assert [call["outcome"] for call in calls] == ["invalid", "succeeded"]
    assert len({call["lesson_id"] for call in calls}) == 1


def test_recoverable_errors_stop_after_two_calls(tmp_path) -> None:
    error = RateLimitError("busy", "test-provider", "test-model")
    generator = SequenceGenerator([error, error])
    service = TutorService(tmp_path / "tutor.db", generator)

    with pytest.raises(GenerationFailed, match="temporaneamente"):
        service.start_or_resume()

    assert generator.calls == 2
    with connect(service.database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM lessons").fetchone()[0] == 0
        assert [
            row[0]
            for row in connection.execute(
                "SELECT outcome FROM generation_calls ORDER BY created_at"
            )
        ] == ["error", "error"]


@pytest.mark.parametrize(
    "error",
    [
        AuthenticationError("bad key", "test-provider", "test-model"),
        RuntimeError("unexpected interruption"),
    ],
)
def test_fatal_or_unknown_errors_do_not_retry(tmp_path, error) -> None:
    generator = SequenceGenerator([error, load_sample_lesson()])
    service = TutorService(tmp_path / "tutor.db", generator)

    with pytest.raises(GenerationFailed):
        service.start_or_resume()

    assert generator.calls == 1


def test_timeout_is_recorded_and_receives_remaining_deadline(tmp_path) -> None:
    timeout = Timeout("slow", "test-model", "test-provider")
    generator = SequenceGenerator([timeout, timeout])
    service = TutorService(tmp_path / "tutor.db", generator)

    with pytest.raises(GenerationFailed, match="tempo"):
        service.start_or_resume()

    assert generator.calls == 2
    assert 0 < generator.timeouts[1] <= generator.timeouts[0] <= 60
    with connect(service.database_path) as connection:
        assert [
            row[0] for row in connection.execute("SELECT outcome FROM generation_calls")
        ] == ["timeout", "timeout"]


def test_interrupted_in_progress_call_becomes_unknown_on_restart(tmp_path) -> None:
    database_path = tmp_path / "tutor.db"
    initialize_database(database_path)
    with connect(database_path) as connection:
        connection.execute(
            """INSERT INTO generation_calls
               (id, generation_group_id, outcome, created_at)
               VALUES ('interrupted', 'group', 'in_progress', ?)""",
            (utc_now(),),
        )

    TutorService(database_path, generate_sample)

    with connect(database_path) as connection:
        row = connection.execute(
            "SELECT outcome, prompt_tokens, cost_usd FROM generation_calls"
        ).fetchone()
    assert dict(row) == {
        "outcome": "unknown",
        "prompt_tokens": None,
        "cost_usd": None,
    }
