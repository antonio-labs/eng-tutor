import os
from dataclasses import dataclass
from typing import Any

from litellm import completion

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
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "api_key": self.config.api_key,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Genera una lezione A1 in JSON per "
                        f"{unit.title}. Obiettivo: {unit.objective}"
                    ),
                }
            ],
            "response_format": {"type": "json_object"},
            "num_retries": 0,
            "timeout": 60,
        }
        if self.config.api_base:
            kwargs["api_base"] = self.config.api_base
        response = completion(**kwargs)
        return LessonContent.model_validate_json(response.choices[0].message.content)
