import os
import json
from dataclasses import dataclass
from typing import Any

from litellm import completion, supports_response_schema

from app.models import CurriculumUnit, LessonContent


class GenerationUnavailable(Exception):
    pass


@dataclass(frozen=True)
class LLMConfig:
    model: str
    api_key: str
    api_base: str | None = None

    @classmethod
    def from_env(cls) -> "LLMConfig":
        model = os.getenv("LLM_MODEL", "").strip()
        api_key = os.getenv("LLM_API_KEY", "").strip()
        if not model or not api_key:
            raise GenerationUnavailable(
                "Configura LLM_MODEL e LLM_API_KEY per creare una nuova lezione."
            )
        return cls(
            model=model,
            api_key=api_key,
            api_base=os.getenv("LLM_API_BASE", "").strip() or None,
        )


class LiteLLMGenerator:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.model = config.model
        self.provider = (
            config.model.split("/", 1)[0] if "/" in config.model else "configured"
        )

    @classmethod
    def from_env(cls) -> "LiteLLMGenerator":
        return cls(LLMConfig.from_env())

    def __call__(self, unit: CurriculumUnit) -> LessonContent:
        prompt = {
            "level": "A1",
            "unit": {
                "id": unit.id,
                "title": unit.title,
                "objective": unit.objective,
            },
            "languages": {
                "explanation_and_rationales": "Italian",
                "examples_questions_and_options": "English",
            },
            "format": {
                "instructions": (
                    "Return only JSON. Keep vocabulary at A1 level. Create exactly "
                    "three examples and six distinct multiple-choice questions with "
                    "three distinct options, one correct option and one rationale each."
                ),
                "json_schema": LessonContent.model_json_schema(),
            },
        }
        try:
            native_schema = supports_response_schema(model=self.config.model)
        except Exception:
            native_schema = False
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "api_key": self.config.api_key,
            "messages": [
                {
                    "role": "user",
                    "content": json.dumps(prompt, ensure_ascii=False),
                }
            ],
            "response_format": (
                LessonContent if native_schema else {"type": "json_object"}
            ),
            "num_retries": 0,
            "timeout": 60,
        }
        if self.config.api_base:
            kwargs["api_base"] = self.config.api_base
        response = completion(**kwargs)
        return LessonContent.model_validate_json(response.choices[0].message.content)
