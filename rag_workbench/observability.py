"""Durable local and PostgreSQL trace stores for immutable run manifests."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol

from rag_workbench.contracts import RunManifest


class TraceStore(Protocol):
    def save(self, manifest: RunManifest) -> None: ...
    def get(self, run_id: str) -> RunManifest: ...
    def list(self) -> list[RunManifest]: ...


class LocalTraceStore:
    """In-memory implementation for deterministic unit tests."""

    def __init__(self) -> None:
        self._runs: dict[str, RunManifest] = {}

    def save(self, manifest: RunManifest) -> None:
        self._runs[manifest.run_id] = manifest

    def get(self, run_id: str) -> RunManifest:
        return self._runs[run_id]

    def list(self) -> list[RunManifest]:
        return list(reversed(list(self._runs.values())))


class JsonTraceStore:
    """Local-first durable trace store; atomic replacement prevents partial manifests."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, manifest: RunManifest) -> None:
        target = self.directory / f"{manifest.run_id}.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(manifest.model_dump_json())
        temporary.replace(target)

    def get(self, run_id: str) -> RunManifest:
        target = self.directory / f"{run_id}.json"
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
                "INSERT INTO run_manifests (run_id, manifest) VALUES (%s, %s::jsonb) ON CONFLICT (run_id) DO UPDATE SET manifest = EXCLUDED.manifest, updated_at = now()",
                (manifest.run_id, manifest.model_dump_json()),
            )

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
