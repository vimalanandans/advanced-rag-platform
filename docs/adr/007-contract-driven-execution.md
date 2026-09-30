# ADR-007: Execute Pipeline Bindings Through the Registry

## Status

Accepted

## Context

Hard-coded component dispatch made the graph descriptive rather than authoritative and allowed components to bypass budgets.

## Decision

Compile node bindings against manifest port types, then resolve inputs and invoke registry-provided executors at runtime. Account for context and output tokens at this boundary; persist a terminal trace in all outcomes.

## Consequences

New components require a manifest, executor, typed ports, tests, and telemetry. This removes hidden runtime coupling and makes invalid bindings fail before execution.
