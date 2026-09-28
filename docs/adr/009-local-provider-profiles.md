# ADR-009: Explicit Local Provider Profiles

## Status

Accepted

## Context

The platform ships deterministic local components for reproducible fixtures and local Qdrant/Ollama adapters
for measured provider runs. Selecting an adapter inside pipeline YAML would couple a public graph definition to
provider implementation details. Falling back from an unavailable provider would make a run misleading.

## Decision

Select deterministic or local Qdrant/Ollama adapters through platform environment configuration at runtime
composition. Keep the graph component references provider-neutral. The selected generation model is recorded
in the immutable run manifest. A selected adapter that fails causes a failed, inspectable run manifest.

## Consequences

The default remains deterministic and does not need Docker model provisioning. Provider-enabled Compose smoke
tests are opt-in and must prove the selected services are available before being called accepted.
