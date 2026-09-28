# ADR-003: Local Provider Baseline

## Status

Accepted

## Decision

Compose PostgreSQL, MinIO, Qdrant, and Ollama locally; use provider interfaces so they remain replaceable.

## Consequences

Tests use deterministic in-process implementations. A running external provider is never required for unit tests.
