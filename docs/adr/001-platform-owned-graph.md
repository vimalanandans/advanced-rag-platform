# ADR-001: Platform-Owned PipelineGraph

## Status

Accepted

## Context

The workbench must outlive orchestration-framework choices and make dependencies inspectable.

## Decision

Compile declarative pipeline configuration to a platform-owned typed IR and execute it with a bounded local interpreter.

## Consequences

Framework adapters may be added later; the initial executor is deliberately small and deterministic.
