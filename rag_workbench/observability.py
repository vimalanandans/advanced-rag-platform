"""Durable local and PostgreSQL trace stores for immutable run manifests."""

from __future__ import annotations

import os
import tempfile
from uuid import UUID
from pathlib import Path
from typing import Protocol

from rag_workbench.contracts import RunManifest


class TraceStore(Protocol):
    def save(self, manifest: RunManifest) -> None: ...
    def get(self, run_id: str) -> RunManifest: ...
    def list(self) -> list[RunManifest]: ...


class TraceConflictError(ValueError):
    """A terminal run ID already names a different immutable record."""


def _assert_same(existing: RunManifest, proposed: RunManifest) -> None:
    if existing.model_dump(mode="json") != proposed.model_dump(mode="json"):
        raise TraceConflictError("terminal run record cannot be overwritten")


def _safe_run_id(run_id: str) -> str:
    try:
        return str(UUID(run_id))
    except (ValueError, AttributeError) as error:
        raise KeyError("invalid run ID") from error


class LocalTraceStore:
    """In-memory implementation for deterministic unit tests."""

    def __init__(self) -> None:
        self._runs: dict[str, RunManifest] = {}

    def save(self, manifest: RunManifest) -> None:
        if manifest.run_id in self._runs:
            _assert_same(self._runs[manifest.run_id], manifest)
            return
        self._runs[manifest.run_id] = manifest.model_copy(deep=True)

    def get(self, run_id: str) -> RunManifest:
        return self._runs[run_id].model_copy(deep=True)

    def list(self) -> list[RunManifest]:
        return [item.model_copy(deep=True) for item in reversed(list(self._runs.values()))]


class JsonTraceStore:
    """Atomic, no-overwrite local terminal records; identical retries are idempotent."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, manifest: RunManifest) -> None:
        target = self.directory / f"{_safe_run_id(manifest.run_id)}.json"
        fd, temporary = tempfile.mkstemp(prefix=".trace-", dir=self.directory)
        try:
            with os.fdopen(fd, "w") as output:
                output.write(manifest.model_dump_json())
                output.flush()
                os.fsync(output.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                _assert_same(self.get(manifest.run_id), manifest)
        finally:
            os.unlink(temporary)

    def get(self, run_id: str) -> RunManifest:
        target = self.directory / f"{_safe_run_id(run_id)}.json"
        if not target.exists():
            raise KeyError(run_id)
        return RunManifest.model_validate_json(target.read_text())

    def list(self) -> list[RunManifest]:
        paths = sorted(self.directory.glob("*.json"), key=lambda path: path.stat().st_mtime_ns, reverse=True)
        return [RunManifest.model_validate_json(path.read_text()) for path in paths]


class PostgresTraceStore:
    """PostgreSQL implementation used by Compose; database values stay inside the adapter."""

    def __init__(self, database_url: str) -> None:
        import psycopg

        self._connection = psycopg.connect(database_url, autocommit=True)
        with self._connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS run_manifests (
                    run_id UUID PRIMARY KEY,
                    manifest JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)

    def save(self, manifest: RunManifest) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO run_manifests (run_id, manifest) VALUES (%s, %s::jsonb) ON CONFLICT (run_id) DO NOTHING",
                (manifest.run_id, manifest.model_dump_json()),
            )
        _assert_same(self.get(manifest.run_id), manifest)

    def get(self, run_id: str) -> RunManifest:
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT manifest::text FROM run_manifests WHERE run_id = %s", (run_id,))
            row = cursor.fetchone()
        if row is None:
            raise KeyError(run_id)
        return RunManifest.model_validate_json(row[0])

    def list(self) -> list[RunManifest]:
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT manifest::text FROM run_manifests ORDER BY updated_at DESC")
            rows = cursor.fetchall()
        return [RunManifest.model_validate_json(row[0]) for row in rows]


def trace_store_from_environment() -> TraceStore:
    database_url = os.environ.get("RAG_WORKBENCH_DATABASE_URL")
    if database_url:
        return PostgresTraceStore(database_url)
    storage = os.environ.get("RAG_WORKBENCH_STORAGE")
    if storage:
        return JsonTraceStore(Path(storage) / "traces")
    return LocalTraceStore()
