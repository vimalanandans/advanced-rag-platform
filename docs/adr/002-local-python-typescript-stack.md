# ADR-002: Python Runtime and TypeScript Studio

## Status

Accepted

## Decision

Use Python/FastAPI/Pydantic for RAG contracts/runtime and React/TypeScript for the inspector workbench.

## Consequences

This fits local RAG tooling while keeping the operator UX strongly typed. API contracts are the boundary.
