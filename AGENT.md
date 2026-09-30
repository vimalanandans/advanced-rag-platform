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
- Apply authorization, freshness, revision, and applicability filters before retrieval, including provider-side candidate selection and every corrective iteration.
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


## V2 operating contract

This is the permanent operating contract for coding agents working on the Advanced RAG Engineering Workbench V2. Read the [V2 requirements](docs/v2/requirements.md), [assessment](docs/v2/current-system-assessment.md), and [migration plan](docs/v2/migration-plan.md) before changing architecture. Preserve the existing system and deterministic profile. The target development machine is an Apple Silicon M3 Mac with Docker Desktop; cloud services remain optional adapters.

## Loop engineering

Every meaningful change follows:

UNDERSTAND → RESEARCH → IDENTIFY GAP → FORM HYPOTHESIS → CREATE BASELINE → DESIGN EXPERIMENT → IMPLEMENT MINIMUM CHANGE → EXECUTE → OBSERVE → MEASURE → DIAGNOSE → IMPROVE → REGRESSION TEST → COMPARE AGAINST BASELINE → ACCEPT / REJECT → DOCUMENT → COMMIT → REPEAT.

Store an engineering-loop record under `experiments/` using the [template](experiments/templates/engineering-loop.json). Include problem, query/content class, hypothesis, baseline/experiment, changed files, commands/tests, before/after metrics, failures, root causes, regressions, decision and notes. Use accept/reject/iterate explicitly. Preserve unrelated work and commit only the intended slice. A blocked external check is a recorded limitation, never a success.

## Evidence and experimentation rules

- Code generation, compilation and one successful example do not establish completion or retrieval improvement.
- Every new strategy needs a problem definition, baseline, representative cases, metric, experiment, result, failure analysis and acceptance decision.
- Measure retrieval, evidence, context, answer and runtime stages separately. Never hide retrieval failures with prompt changes or let aggregate scores conceal policy violations.
- Never disable abstention to increase answer rate or treat model-generated confidence as authority.
- Summaries, hypothetical documents, compressed text and graph edges must retain original evidence references. They cannot replace original authority or become sole citations when original sources exist.
- Keep experience memory separate from authoritative evidence. Learning may select a strategy; it may not grant access or manufacture support.
- Prefer the simplest strategy that solves the measured problem. Research current primary sources before advanced techniques and store records under `docs/research/`.
- Preserve original queries, version transformations, bound every query/action/loop, and log why the system continued, stopped, clarified or abstained.
- Pin model/embedding/index/parser/chunker/corpus/dataset/policy identities. Reject incompatible indexes; migrate rather than silently overwrite.
- Do not enable corrective or agentic retrieval until A–F baseline experiments are reproducible. Do not begin with language-model RL.

## Acceptance and reporting

Follow [Definition of Done](docs/definition-of-done/README.md). A slice needs documented requirements/contracts, success and failure tests, relevant evaluation and baseline comparison, inspectable traces, verified local operation, updated docs, regression evidence and an acceptance decision. Report specified, implemented, tested and operationally accepted as distinct states. Preserve failed run/experiment records and rollback identities.
