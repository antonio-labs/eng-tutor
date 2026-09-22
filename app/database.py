import sqlite3
from pathlib import Path

from app.models import EXERCISES_PER_LESSON


DEFAULT_DATABASE_PATH = Path("data/tutor.db")


SCHEMA = f"""
CREATE TABLE IF NOT EXISTS lessons (
    id TEXT PRIMARY KEY,
    unit_id TEXT NOT NULL,
    content_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'completed', 'discarded')),
    answers_json TEXT,
    correct_answers INTEGER CHECK (
        correct_answers BETWEEN 0 AND {EXERCISES_PER_LESSON}
    ),
    created_at TEXT NOT NULL,
    completed_at TEXT,
    discarded_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS one_active_lesson
ON lessons ((1)) WHERE status = 'active';

CREATE TABLE IF NOT EXISTS generation_calls (
    id TEXT PRIMARY KEY,
    generation_group_id TEXT NOT NULL,
    lesson_id TEXT REFERENCES lessons(id),
    provider TEXT,
    model TEXT,
    outcome TEXT NOT NULL CHECK (
        outcome IN ('in_progress', 'succeeded', 'invalid', 'timeout', 'error', 'unknown')
    ),
    prompt_tokens INTEGER CHECK (prompt_tokens >= 0),
    completion_tokens INTEGER CHECK (completion_tokens >= 0),
    total_tokens INTEGER CHECK (total_tokens >= 0),
    cost_usd REAL CHECK (cost_usd >= 0),
    pricing_reference TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS one_generation_in_progress
ON generation_calls ((1)) WHERE outcome = 'in_progress';

CREATE INDEX IF NOT EXISTS generation_calls_group
ON generation_calls (generation_group_id, created_at);
"""


def connect(path: Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(path: Path = DEFAULT_DATABASE_PATH) -> None:
    with connect(path) as connection:
        connection.executescript(SCHEMA)
