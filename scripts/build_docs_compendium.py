"""Build docs/doc.md from the Markdown source files under docs/."""

import os
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUTPUT = DOCS / "doc.md"
LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)]+)\)")


def rewrite_relative_links(markdown: str, source: Path) -> str:
    """Keep source-relative links working from the consolidated document."""
    def replace(match: re.Match[str]) -> str:
        label, destination = match.groups()
        path, separator, fragment = destination.partition("#")
        if not path or urlparse(path).scheme or path.startswith(("/", "//")):
            return match.group(0)
        resolved = (source.parent / path).resolve()
        rewritten = Path(os.path.relpath(resolved, DOCS)).as_posix()
        destination = rewritten + (separator + fragment if separator else "")
        return f"[{label}]({destination})"

    return LINK.sub(replace, markdown)


def main() -> None:
    sources = sorted(path for path in DOCS.rglob("*.md") if path != OUTPUT)
    contents = [
        "# Documentation Compendium\n\n"
        "This file combines the Markdown documentation under `docs/` for convenient reading. "
        "Each section names its source file. Individual files remain the editable source of truth; "
        "links in copied sections are relative to the named source file.\n\n"
        "## Contents\n\n"
        + "\n".join(
            f"{index}. `{source.relative_to(DOCS).as_posix()}`"
            for index, source in enumerate(sources, start=1)
        )
    ]
    contents.extend(
        "\n\n---\n\n"
        f"<!-- Source: {source.relative_to(DOCS).as_posix()} -->\n\n"
        f"{rewrite_relative_links(source.read_text(encoding='utf-8').strip(), source)}"
        for source in sources
    )
    OUTPUT.write_text("\n".join(contents) + "\n", encoding="utf-8")
    print(f"Merged {len(sources)} Markdown files into {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
