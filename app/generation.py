import json
import os
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any

from litellm import completion, completion_cost
from litellm.exceptions import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    BadRequestError,
    BudgetExceededError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServiceUnavailableError,
    Timeout,
    UnsupportedParamsError,
)
from pydantic import ValidationError

from app.models import CurriculumUnit, LessonContent


class GenerationUnavailable(Exception):
    pass


class GenerationFailed(Exception):
    pass


@dataclass(frozen=True)
class ErrorDisposition:
    outcome: str
    retryable: bool
    user_message: str


@dataclass(frozen=True)
class CallMetrics:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    pricing_reference: str | None = None


@dataclass(frozen=True)
class GenerationOutput:
    content: LessonContent
    metrics: CallMetrics


class InvalidGenerationResponse(Exception):
    def __init__(self, cause: Exception, metrics: CallMetrics) -> None:
        super().__init__(str(cause))
        self.cause = cause
        self.metrics = metrics


def classify_generation_error(error: Exception) -> ErrorDisposition:
    if isinstance(error, (ValidationError, json.JSONDecodeError)):
        return ErrorDisposition(
            "invalid",
            True,
            "Il provider ha restituito una lezione non valida. Riprova.",
        )
    if isinstance(error, (Timeout, TimeoutError)):
        return ErrorDisposition(
            "timeout", True, "La generazione ha superato il tempo disponibile. Riprova."
        )
    if isinstance(error, BudgetExceededError) or (
        isinstance(error, BadRequestError)
        and "insufficient balance" in str(error).lower()
    ):
        return ErrorDisposition(
            "error",
            False,
            "Il saldo o il limite di spesa del provider non consente la generazione.",
        )
    if isinstance(
        error,
        (
            AuthenticationError,
            BadRequestError,
            NotFoundError,
            PermissionDeniedError,
            UnsupportedParamsError,
        ),
    ):
        return ErrorDisposition(
            "error",
            False,
            "La configurazione o le credenziali del provider non sono valide.",
        )
    if isinstance(
        error,
        (
            APIConnectionError,
            APIError,
            InternalServerError,
            RateLimitError,
            ServiceUnavailableError,
            ConnectionError,
        ),
    ):
        return ErrorDisposition(
            "error", True, "Il provider non è temporaneamente disponibile. Riprova."
        )
    return ErrorDisposition(
        "unknown", False, "La generazione è stata interrotta con esito sconosciuto."
    )


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
        return self.generate_once(unit, timeout=60).content

    def generate_once(self, unit: CurriculumUnit, timeout: float) -> GenerationOutput:
        prompt = {
            "level": "A1",
            "unit": {
                "id": unit.id,
                "title": unit.title,
                "objective": unit.objective,
            },
            "languages": {
                "explanation_example_notes_and_rationales": "Italian",
                "example_sentences_questions_and_options": "English",
            },
            "format": {
                "instructions": (
                    "Return only JSON. Teach and test English grammar only; Italian "
                    "is only for explanations, example notes and rationales. Keep "
                    "every example sentence, question, option and correct answer in "
                    "English and strictly within the unit objective. Keep vocabulary "
                    "at A1 level. Create exactly three examples and six distinct, "
                    "self-contained multiple-choice questions with three distinct "
                    "options, exactly one unambiguously correct option and one "
                    "rationale each. Do not use distractors that are valid under "
                    "another plausible interpretation."
                ),
                "json_schema": LessonContent.model_json_schema(),
            },
        }
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "api_key": self.config.api_key,
            "messages": [
                {
                    "role": "user",
                    "content": json.dumps(prompt, ensure_ascii=False),
                }
            ],
            "response_format": {"type": "json_object"},
            "num_retries": 0,
            "timeout": timeout,
        }
        if self.config.api_base:
            kwargs["api_base"] = self.config.api_base
        response = completion(**kwargs)
        metrics = self._metrics(response)
        try:
            content = LessonContent.model_validate_json(
                response.choices[0].message.content
            )
        except ValidationError as error:
            raise InvalidGenerationResponse(error, metrics) from error
        return GenerationOutput(content=content, metrics=metrics)

    @staticmethod
    def _metrics(response: Any) -> CallMetrics:
        usage = getattr(response, "usage", None)

        def usage_value(name: str) -> int | None:
            value = (
                usage.get(name)
                if isinstance(usage, dict)
                else getattr(usage, name, None)
            )
            return int(value) if value is not None else None

        hidden = getattr(response, "_hidden_params", None) or {}
        cost = hidden.get("response_cost")
        if cost is None:
            try:
                cost = completion_cost(completion_response=response)
            except Exception:
                cost = None
        cost_value = float(cost) if cost is not None else None
        return CallMetrics(
            prompt_tokens=usage_value("prompt_tokens"),
            completion_tokens=usage_value("completion_tokens"),
            total_tokens=usage_value("total_tokens"),
            cost_usd=cost_value,
            pricing_reference=(
                f"LiteLLM {version('litellm')} bundled/community model cost map"
                if cost_value is not None
                else None
            ),
        )
