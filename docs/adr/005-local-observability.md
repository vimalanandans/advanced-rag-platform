# ADR-005: Local Observability Is Mandatory

## Status

Accepted

## Decision

Persist local traces and run manifests first; OTEL/Langfuse are optional exporters.

## Consequences

The workbench remains diagnosable offline. Export failures cannot fail a pipeline run.
