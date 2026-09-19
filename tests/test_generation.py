import pytest

from app.generation import GenerationUnavailable, LLMConfig, LiteLLMGenerator
from app.main import create_app
from app.service import generate_sample


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
