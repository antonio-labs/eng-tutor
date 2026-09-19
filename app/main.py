from fastapi import FastAPI

from app.curriculum import load_curriculum
from app.models import CurriculumUnit


app = FastAPI(title="AI English Tutor", version="0.1.0")
curriculum = load_curriculum()


@app.get("/")
def root() -> dict[str, str | int]:
    return {
        "name": "AI English Tutor",
        "status": "ok",
        "curriculum_units": len(curriculum),
    }


@app.get("/api/curriculum", response_model=list[CurriculumUnit])
def get_curriculum() -> list[CurriculumUnit]:
    return curriculum
