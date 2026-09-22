import json
import re
from pathlib import Path

from pydantic import TypeAdapter

from app.models import CourseUnitContent, CurriculumUnit, LessonContent


DATA_DIR = Path(__file__).parent / "data"
EXPECTED_UNIT_IDS = tuple(f"A1-{number:02}" for number in range(1, 37))
REQUIRED_EXPLANATION_SECTIONS = (
    "Quando si usa",
    "Come si forma",
    "Attenzione",
    "Errori comuni",
)
FORBIDDEN_MARKDOWN = {
    "HTML": r"</?[A-Za-z][^>]*>",
    "immagini o link": r"!?\[[^\]\n]+\]\([^\)\n]+\)",
    "titoli non supportati": r"(?m)^#{1,2}\s|^#{4,}\s",
    "liste numerate": r"(?m)^\s*\d+[.)]\s",
    "blocchi di codice": r"(?m)^```",
    "tabelle": r"(?m)^\s*\|",
    "testo barrato": r"~~",
    "corsivo con asterischi": r"(?<!\*)\*(?!\*)[^*\n]+\*(?!\*)",
    "corsivo con underscore": r"(?<!_)_(?!_)[^_\n]+_(?!_)",
}


class A1Course:
    def __init__(self, contents: list[CourseUnitContent]) -> None:
        self._contents = tuple(contents)
        self._by_id = {content.unit.id: content for content in contents}

    @property
    def units(self) -> list[CurriculumUnit]:
        return [content.unit for content in self._contents]

    def content_for(self, unit_id: str) -> CourseUnitContent:
        try:
            return self._by_id[unit_id]
        except KeyError:
            raise ValueError(f"unknown curriculum unit id: {unit_id}") from None

    def __len__(self) -> int:
        return len(self._contents)


def load_course(data_dir: Path = DATA_DIR) -> A1Course:
    units = TypeAdapter(list[CurriculumUnit]).validate_json(
        (data_dir / "curriculum.json").read_text(encoding="utf-8")
    )
    ids = tuple(unit.id for unit in units)
    if ids != EXPECTED_UNIT_IDS:
        raise ValueError("curriculum must contain the 36 ordered A1 unit ids")

    explanations_dir = data_dir / "grammar_explanations"
    files = {path.stem: path for path in explanations_dir.glob("*.md")}
    if set(files) != set(ids):
        missing = sorted(set(ids) - set(files))
        unexpected = sorted(set(files) - set(ids))
        raise ValueError(
            f"grammar explanations do not match curriculum: "
            f"missing={missing}, unexpected={unexpected}"
        )

    contents = []
    for unit in units:
        explanation = files[unit.id].read_text(encoding="utf-8")
        _validate_explanation(unit.id, explanation)
        contents.append(CourseUnitContent(unit=unit, explanation=explanation))
    return A1Course(contents)


def load_sample_lesson(
    unit_content: CourseUnitContent | None = None,
    data_dir: Path = DATA_DIR,
) -> LessonContent:
    selected = unit_content or load_course(data_dir).content_for("A1-01")
    practice = json.loads(
        (data_dir / "sample_practice.json").read_text(encoding="utf-8")
    )
    return LessonContent(
        unit_id=selected.unit.id,
        explanation=selected.explanation,
        **practice,
    )


def _validate_explanation(unit_id: str, content: str) -> None:
    if not content.strip():
        raise ValueError(f"empty grammar explanation for unit {unit_id}")

    sections = list(re.finditer(r"(?m)^### (.+)$", content))
    if tuple(match.group(1) for match in sections) != REQUIRED_EXPLANATION_SECTIONS:
        raise ValueError(f"invalid explanation sections for unit {unit_id}")
    if content[: sections[0].start()].strip():
        raise ValueError(f"content before first explanation section for unit {unit_id}")
    for index, section in enumerate(sections):
        end = sections[index + 1].start() if index + 1 < len(sections) else None
        if not content[section.end() : end].strip():
            raise ValueError(f"empty explanation section for unit {unit_id}")
    for feature, pattern in FORBIDDEN_MARKDOWN.items():
        if re.search(pattern, content):
            raise ValueError(f"unsupported Markdown in unit {unit_id}: {feature}")
