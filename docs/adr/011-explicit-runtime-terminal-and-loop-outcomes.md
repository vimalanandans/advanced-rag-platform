# ADR-011: Explicit terminal outputs and enforced loop outcomes

## Status

Accepted; implemented as an additive runtime safety slice on 2026-09-30.

## Context

The v1 runtime selects results from fixed `generate`/`context` node IDs. Loop fallback `abstain` was declarative only, and loops ran after downstream generation. Tenant denial happened outside terminal trace persistence. These behaviors block safely adding corrective retrieval.

## Decision

Graph schema `2.0.0` requires typed terminal bindings for answer, citations and abstained, with optional context. The compiler validates their sources and types. V1 graphs retain their canonical representation and fingerprint. Execute bounded repetitions when the last loop node finishes, before downstream nodes. Reject overlapping/reordered loops, cross-loop feedback and graphs whose consumers execute before a loop finishes. Honor conditional edges during repetition, removing skipped stale outputs.

Exhaustion either raises a traced failure or forces abstention with no citations. Persist loop outcomes separately from node events. Allocate run identity before authorization so safe denial records survive. Validate evidence/candidate list element types at component boundaries.

## Consequences

Corrective retrieval still requires its own policy, planner, query/action budgets and evaluation; this slice alone does not enable it. Legacy graphs remain readable and deterministic ranking is unchanged. Provider interruption/cancellation, strict component configuration schemas, error-edge scheduling and append-only trace stores remain separate work. New graph formats use explicit outputs; rollback can select the existing v1 baseline, but must not restore the unsafe exhaustion behavior.
