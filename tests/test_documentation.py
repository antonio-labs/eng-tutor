import re
from pathlib import Path


ROOT = Path(__file__).parents[1]
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def test_local_markdown_links_resolve() -> None:
    documents = [
        *ROOT.glob("*.md"),
        *(ROOT / "docs").rglob("*.md"),
        *(ROOT / "research").rglob("*.md"),
    ]
    broken = []
    for document in documents:
        for raw_target in MARKDOWN_LINK.findall(document.read_text(encoding="utf-8")):
            target = raw_target.split("#", 1)[0].strip().strip("<>")
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if not (document.parent / target).resolve().exists():
                broken.append(f"{document.relative_to(ROOT)} -> {raw_target}")

    assert not broken, "broken local Markdown links:\n" + "\n".join(broken)
