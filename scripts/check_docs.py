"""Keep public documentation synchronized with the local API and configuration surface."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
API_SOURCE = ROOT / "rag_workbench" / "api.py"
API_DOC = ROOT / "docs" / "api" / "README.md"
CONFIG_DOC = ROOT / "docs" / "reference" / "configuration.md"
INDEX_DOC = ROOT / "docs" / "README.md"
REQUIRED_ENVIRONMENT_VARIABLES = (
    "RAG_WORKBENCH_LOCAL_ADMIN_TOKEN",
    "RAG_WORKBENCH_CORS_ORIGINS",
    "RAG_WORKBENCH_DATABASE_URL",
    "RAG_WORKBENCH_STORAGE",
    "RAG_WORKBENCH_DENSE_MODE",
    "RAG_WORKBENCH_GENERATION_MODE",
    "RAG_WORKBENCH_QDRANT_URL",
    "RAG_WORKBENCH_QDRANT_COLLECTION",
    "RAG_WORKBENCH_OLLAMA_URL",
    "RAG_WORKBENCH_OLLAMA_MODEL",
    "VITE_API_URL",
    "VITE_PROXY_TARGET",
)
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def extract_routes(source: Path) -> set[tuple[str, str]]:
    tree = ast.parse(source.read_text(encoding="utf-8"))
    routes: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            method = decorator.func.attr.upper()
            if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            if decorator.args and isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
                routes.add((method, decorator.args[0].value))
    return routes


def local_markdown_link_errors(root: Path) -> list[str]:
    """Return missing relative Markdown links without probing external URLs."""
    errors: list[str] = []
    documents = [root / name for name in ("README.md", "Goals.md", "ARCHITECTURE.md", "CONTRIBUTING.md", "SECURITY.md", "AGENT.md", "AGENTS.md")]
    documents.extend((root / "docs").rglob("*.md"))
    for document in documents:
        if not document.exists():
            continue
        for target in LINK_PATTERN.findall(document.read_text(encoding="utf-8")):
            target = target.split("#", 1)[0].strip().strip("<>")
            if not target or urlparse(target).scheme or target.startswith("/"):
                continue
            if not (document.parent / target).resolve().exists():
                errors.append(f"{document.relative_to(root)} links to missing {target}")
    return errors


def main() -> int:
    errors: list[str] = []
    api_reference = API_DOC.read_text(encoding="utf-8")
    configuration = CONFIG_DOC.read_text(encoding="utf-8")
    index = INDEX_DOC.read_text(encoding="utf-8")

    for method, path in sorted(extract_routes(API_SOURCE)):
        marker = f"`{method} {path}`"
        if marker not in api_reference:
            errors.append(f"API reference is missing {marker}")
    for variable in REQUIRED_ENVIRONMENT_VARIABLES:
        if variable not in configuration:
            errors.append(f"Configuration reference is missing {variable}")
    for path in ("api/README.md", "architecture/system.md", "reference/configuration.md", "user-guide/first-local-run.md"):
        if path not in index:
            errors.append(f"Documentation index is missing {path}")
    errors.extend(local_markdown_link_errors(ROOT))

    if errors:
        print("Documentation validation failed:", *errors, sep="\n- ")
        return 1
    print(f"Documentation validation passed for {len(extract_routes(API_SOURCE))} API routes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
