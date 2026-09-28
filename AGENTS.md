# Agent Engineering Rules

## Purpose

This repository is a local-first, graph-native RAG engineering workbench. RAG is an
evidence-selection system, not a chat model connected to a vector database.

## Architecture invariants

- `PipelineGraph` owns orchestration. Components never invoke arbitrary downstream components.
- Keep public contracts typed, semantically versioned, and provider-neutral.
- Customers differ through configuration, data, policies, and evaluation sets—not shared-code forks.
- Local execution is mandatory. Cloud services and external observability are optional adapters.
- Persist immutable run metadata and a graph fingerprint for every execution.
- Apply authorization, freshness, revision, and applicability filters before evidence enters generation.
- Return inspectable citations or an explicit abstention when evidence is insufficient.

## Graph and component rules

- Declare every data/control/error/feedback dependency in the graph.
- Validate schemas, capability compatibility, budgets, and loops before execution.
- Cycles require declared bounds for iterations, time, tokens, tool calls, exit condition, fallback, and tracing.
- Each component must publish ID, semantic version, configuration schema, I/O contract, capabilities,
  limits, errors, concurrency behavior, telemetry, and tests.
- Provider-specific objects must not cross platform contracts.

## Security and observability

- Use local-admin defaults while preserving corpus/document ACL and tenant-policy contracts.
- Never log secrets, raw credentials, or unauthorized evidence. Use trace IDs and safe metadata.
- Account for input/output/context tokens, retrieval candidates, model/tool calls, retries, loops, and fallbacks.
- Tools must be explicitly permissioned and workspace-sandboxed.

## Required engineering practice

- Add or update an ADR for material architecture decisions.
- Add deterministic unit/contract/graph/pipeline tests and regression fixtures for new retrieval behavior.
- Document public components and configuration examples. Record evaluation guidance for a retrieval strategy.
- Keep `docker compose up` working without a cloud dependency.

## Forbidden patterns

- Customer-specific branches in shared domain code; direct cloud SDK calls from domain modules.
- Hidden component dependencies; global mutable runtime state; silent fallbacks.
- Hardcoded vector-store/model assumptions; opaque confidence claims.
- Unbounded agent loops or concurrency; unversioned prompts or pipeline definitions; untraceable responses.

## Definition of done

A change is done only when it meets the applicable gates in
[`docs/definition-of-done/README.md`](docs/definition-of-done/README.md): contracts validate,
tests/evaluation cover the behavior, telemetry and failure modes are observable, security implications
are documented, and local execution remains reproducible. A green unit test alone is never sufficient.
