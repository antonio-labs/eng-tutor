import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from time import monotonic
from typing import Any, Protocol
from uuid import uuid4

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
from pydantic import Field, ValidationError

from app.course import load_sample_lesson
from app.database import connect
from app.models import (
    EXERCISES_PER_LESSON,
    CostSummary,
    CourseUnitContent,
    Exercise,
    FailedGeneration,
    LessonContent,
    LessonExample,
    Model,
)


MAX_GENERATION_CALLS = 2
GENERATION_DEADLINE_SECONDS = 60
GENERATION_UNAVAILABLE_MESSAGE = (
    "Configura LLM_MODEL e LLM_API_KEY per creare una nuova lezione."
)


class _GeneratedPractice(Model):
    examples: list[LessonExample] = Field(min_length=3, max_length=3)
    exercises: list[Exercise] = Field(
        min_length=EXERCISES_PER_LESSON,
        max_length=EXERCISES_PER_LESSON,
    )


class GenerationUnavailable(Exception):
    pass


class GenerationFailed(Exception):
    pass


class GenerationInProgress(Exception):
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


class PracticeGenerator(Protocol):
    provider: str
    model: str

    def generate_once(
        self, unit_content: CourseUnitContent, timeout: float
    ) -> GenerationOutput: ...


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
            raise GenerationUnavailable(GENERATION_UNAVAILABLE_MESSAGE)
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

    def generate_once(
        self, unit_content: CourseUnitContent, timeout: float
    ) -> GenerationOutput:
        unit = unit_content.unit
        explanation = unit_content.explanation.strip()
        prompt = {
            "level": "A1",
            "unit": {
                "id": unit.id,
                "title": unit.title,
                "objective": unit.objective,
            },
            "verified_explanation_markdown": explanation,
            "languages": {
                "example_notes_and_rationales": "Italian",
                "example_sentences_questions_and_options": "English",
            },
            "format": {
                "instructions": (
                    "Use the verified explanation as authoritative context. Do not "
                    "return or rewrite the explanation and do not return a unit ID. "
                    "Return only JSON containing the requested practice. Teach and "
                    "test English grammar only; Italian is only for example notes "
                    "and rationales. Keep every example sentence, question, option "
                    "and correct answer in English and strictly within the unit "
                    "objective. Keep vocabulary at A1 level. Create exactly three "
                    "examples and six distinct, self-contained multiple-choice "
                    "questions with three distinct options, exactly one "
                    "unambiguously correct option and one rationale each. Do not use "
                    "distractors that are valid under another plausible "
                    "interpretation."
                ),
                "json_schema": _GeneratedPractice.model_json_schema(),
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
            practice = _GeneratedPractice.model_validate_json(
                response.choices[0].message.content
            )
            content = LessonContent(
                unit_id=unit.id,
                explanation=explanation,
                examples=practice.examples,
                exercises=practice.exercises,
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


class SampleGenerator:
    provider = "mock"
    model = "sample-lesson"

    def generate_once(
        self, unit_content: CourseUnitContent, timeout: float
    ) -> GenerationOutput:
        _ = timeout
        return GenerationOutput(load_sample_lesson(unit_content), CallMetrics())


class LessonGeneration:
    def __init__(
        self,
        database_path: Path,
        generator: PracticeGenerator | None,
    ) -> None:
        self.database_path = database_path
        self.generator = generator
        with connect(database_path) as connection:
            connection.execute(
                """UPDATE generation_calls
                   SET outcome = 'unknown', finished_at = ?
                   WHERE outcome = 'in_progress'""",
                (_utc_now(),),
            )

    @property
    def available(self) -> bool:
        return self.generator is not None

    def create_or_resume(self, unit_content: CourseUnitContent) -> str:
        with connect(self.database_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            active = connection.execute(
                "SELECT id FROM lessons WHERE status = 'active'"
            ).fetchone()
            if active:
                return active["id"]
            if self.generator is None:
                raise GenerationUnavailable(GENERATION_UNAVAILABLE_MESSAGE)

            group_id = str(uuid4())
            try:
                call_id = self._insert_call(connection, group_id)
            except sqlite3.IntegrityError as error:
                raise GenerationInProgress from error

        generated = False
        metrics = CallMetrics()
        try:
            content, call_id, metrics = self._generate(
                unit_content, group_id, call_id
            )
            generated = True
            lesson_id = str(uuid4())
            with connect(self.database_path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """INSERT INTO lessons
                       (id, unit_id, content_json, status, created_at)
                       VALUES (?, ?, ?, 'active', ?)""",
                    (
                        lesson_id,
                        unit_content.unit.id,
                        content.model_dump_json(),
                        _utc_now(),
                    ),
                )
                connection.execute(
                    """UPDATE generation_calls
                       SET lesson_id = ? WHERE generation_group_id = ?""",
                    (lesson_id, group_id),
                )
                connection.execute(
                    """UPDATE generation_calls
                       SET outcome = 'succeeded',
                           prompt_tokens = ?, completion_tokens = ?, total_tokens = ?,
                           cost_usd = CASE WHEN provider = 'mock' THEN 0 ELSE ? END,
                           pricing_reference = CASE WHEN provider = 'mock'
                               THEN 'simulated: no external call' ELSE ? END,
                           finished_at = ?
                       WHERE id = ?""",
                    (
                        metrics.prompt_tokens,
                        metrics.completion_tokens,
                        metrics.total_tokens,
                        metrics.cost_usd,
                        metrics.pricing_reference,
                        _utc_now(),
                        call_id,
                    ),
                )
            return lesson_id
        except Exception:
            if generated:
                self._finish_call(call_id, "succeeded", metrics=metrics)
            raise

    def failed_generations(self) -> list[FailedGeneration]:
        with connect(self.database_path) as connection:
            rows = connection.execute(
                """SELECT generation_group_id, MIN(created_at) AS created_at,
                          MAX(provider) AS provider, MAX(model) AS model,
                          GROUP_CONCAT(outcome) AS outcomes,
                          COUNT(*) AS calls, COUNT(cost_usd) AS known_calls,
                          SUM(cost_usd) AS known_usd
                   FROM generation_calls
                   WHERE lesson_id IS NULL AND outcome != 'in_progress'
                   GROUP BY generation_group_id
                   ORDER BY created_at DESC"""
            ).fetchall()
        return [
            FailedGeneration(
                generation_group_id=row["generation_group_id"],
                created_at=row["created_at"],
                provider=row["provider"] or "non disponibile",
                model=row["model"] or "non disponibile",
                calls=row["calls"],
                outcomes=row["outcomes"].split(","),
                cost=_cost_from_counts(row),
            )
            for row in rows
        ]

    def _generate(
        self,
        unit_content: CourseUnitContent,
        group_id: str,
        call_id: str,
    ) -> tuple[LessonContent, str, CallMetrics]:
        deadline = monotonic() + GENERATION_DEADLINE_SECONDS

        for attempt in range(MAX_GENERATION_CALLS):
            remaining = deadline - monotonic()
            try:
                if remaining <= 0:
                    raise TimeoutError
                output = self.generator.generate_once(unit_content, timeout=remaining)
                return output.content, call_id, output.metrics
            except Exception as error:
                cause = (
                    error.cause
                    if isinstance(error, InvalidGenerationResponse)
                    else error
                )
                metrics = (
                    error.metrics
                    if isinstance(error, InvalidGenerationResponse)
                    else CallMetrics()
                )
                disposition = classify_generation_error(cause)
                self._finish_call(
                    call_id,
                    disposition.outcome,
                    type(cause).__name__,
                    metrics,
                )
                can_retry = (
                    disposition.retryable
                    and attempt + 1 < MAX_GENERATION_CALLS
                    and monotonic() < deadline
                )
                if not can_retry:
                    raise GenerationFailed(disposition.user_message) from error
                with connect(self.database_path) as connection:
                    call_id = self._insert_call(connection, group_id)

        raise AssertionError("generation loop must return or raise")

    def _insert_call(self, connection: sqlite3.Connection, group_id: str) -> str:
        call_id = str(uuid4())
        connection.execute(
            """INSERT INTO generation_calls
               (id, generation_group_id, provider, model, outcome, created_at)
               VALUES (?, ?, ?, ?, 'in_progress', ?)""",
            (
                call_id,
                group_id,
                self.generator.provider,
                self.generator.model,
                _utc_now(),
            ),
        )
        return call_id

    def _finish_call(
        self,
        call_id: str,
        outcome: str,
        error_message: str | None = None,
        metrics: CallMetrics = CallMetrics(),
    ) -> None:
        with connect(self.database_path) as connection:
            connection.execute(
                """UPDATE generation_calls
                   SET outcome = ?, error_message = ?, finished_at = ?,
                       prompt_tokens = ?, completion_tokens = ?, total_tokens = ?,
                       cost_usd = ?, pricing_reference = ?
                   WHERE id = ? AND outcome = 'in_progress'""",
                (
                    outcome,
                    error_message,
                    _utc_now(),
                    metrics.prompt_tokens,
                    metrics.completion_tokens,
                    metrics.total_tokens,
                    metrics.cost_usd,
                    metrics.pricing_reference,
                    call_id,
                ),
            )


def _cost_from_counts(row: sqlite3.Row) -> CostSummary:
    if row["known_calls"] == 0:
        return CostSummary(status="unavailable")
    return CostSummary(
        status="partial" if row["known_calls"] < row["calls"] else "known",
        known_usd=row["known_usd"],
    )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
