import os
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.curriculum import load_curriculum
from app.generation import GenerationUnavailable, LiteLLMGenerator
from app.models import (
    AnswerSubmission,
    CompletedLesson,
    CurriculumUnit,
    DiscardedLesson,
    HistoryItem,
    LearningSummary,
    LessonContent,
    LessonSession,
)
from app.service import (
    GenerationInProgress,
    LessonNotFound,
    LessonStateError,
    TutorService,
)


curriculum = load_curriculum()
STATIC_DIR = Path(__file__).parent / "static"


def root() -> dict[str, str | int]:
    return {
        "name": "AI English Tutor",
        "status": "ok",
        "curriculum_units": len(curriculum),
    }


def get_curriculum() -> list[CurriculumUnit]:
    return curriculum


def create_app(
    database_path: Path | None = None,
    generator: Callable[[CurriculumUnit], LessonContent] | None = None,
) -> FastAPI:
    application = FastAPI(title="AI English Tutor", version="0.1.0")
    path = database_path or Path(os.getenv("DATABASE_PATH", "data/tutor.db"))
    if generator is None:
        try:
            generator = LiteLLMGenerator.from_env()
        except GenerationUnavailable:
            generator = None
    service = TutorService(path, generator)

    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @application.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    application.add_api_route("/api/health", root, methods=["GET"])
    application.add_api_route(
        "/api/curriculum",
        get_curriculum,
        methods=["GET"],
        response_model=list[CurriculumUnit],
    )

    @application.get("/api/summary", response_model=LearningSummary)
    def get_summary() -> LearningSummary:
        return service.summary()

    @application.post("/api/lessons/start", response_model=LessonSession)
    def start_lesson() -> LessonSession:
        try:
            lesson = service.start_or_resume()
        except GenerationInProgress as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La generazione di una lezione è già in corso.",
            ) from error
        except GenerationUnavailable as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(error),
            ) from error
        if lesson is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Percorso di grammatica A1 completato.",
            )
        return lesson

    @application.get("/api/lessons/{lesson_id}", response_model=LessonSession)
    def get_lesson(lesson_id: UUID) -> LessonSession:
        lesson = service.get_lesson(str(lesson_id))
        if lesson is None:
            raise HTTPException(status_code=404, detail="Lezione non trovata.")
        return lesson

    @application.post(
        "/api/lessons/{lesson_id}/submit", response_model=CompletedLesson
    )
    def submit_lesson(lesson_id: UUID, submission: AnswerSubmission) -> CompletedLesson:
        try:
            return service.submit_lesson(str(lesson_id), submission.answers)
        except LessonNotFound as error:
            raise HTTPException(status_code=404, detail="Lezione non trovata.") from error
        except (LessonStateError, ValueError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @application.post(
        "/api/lessons/{lesson_id}/discard", response_model=DiscardedLesson
    )
    def discard_lesson(lesson_id: UUID) -> DiscardedLesson:
        try:
            return service.discard_lesson(str(lesson_id))
        except LessonNotFound as error:
            raise HTTPException(status_code=404, detail="Lezione non trovata.") from error
        except LessonStateError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @application.get("/api/history", response_model=list[HistoryItem])
    def get_history() -> list[HistoryItem]:
        return service.history()

    @application.get(
        "/api/lessons/{lesson_id}/result", response_model=CompletedLesson
    )
    def get_result(lesson_id: UUID) -> CompletedLesson:
        try:
            return service.get_result(str(lesson_id))
        except LessonNotFound as error:
            raise HTTPException(status_code=404, detail="Lezione non trovata.") from error
        except LessonStateError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    application.state.tutor_service = service
    return application


app = create_app()
