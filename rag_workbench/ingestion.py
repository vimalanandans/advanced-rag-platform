"""Local source conversion with immutable, inspectable evidence identifiers."""

from __future__ import annotations

import hashlib
from pathlib import Path

from pypdf import PdfReader

from rag_workbench.contracts import Evidence


def ingest_path(path: Path, corpus_id: str = "local-demo") -> list[Evidence]:
    source = path.resolve().as_uri()
    revision = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    if path.suffix.lower() == ".pdf":
        pages = PdfReader(str(path)).pages
        blocks = [(f"page:{index}", page.extract_text() or "") for index, page in enumerate(pages, start=1)]
    else:
        blocks = _markdown_blocks(path.read_text(encoding="utf-8"))
    return [
        Evidence(
            id=f"{corpus_id}:{path.stem}:{locator}", document_id=f"{corpus_id}:{path.stem}",
            source_uri=source, revision=revision, content=text.strip(), title=path.stem, locator=locator,
            metadata={"corpus_id": corpus_id, "content_type": path.suffix.lower().lstrip(".")},
            approval_state="approved" if text.strip() else "review_required",
        )
        for index, (locator, text) in enumerate(blocks, start=1) if text.strip()
    ]


def _markdown_blocks(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    heading = "section:1"
    buffer: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            if buffer:
                sections.append((heading, "\n".join(buffer)))
            heading = f"section:{line.lstrip('#').strip().lower().replace(' ', '-') or len(sections) + 1}"
            buffer = [line]
        else:
            buffer.append(line)
    if buffer:
        sections.append((heading, "\n".join(buffer)))
    return [(f"{locator}:{index}", block) for index, (locator, block) in enumerate(sections, start=1)]
