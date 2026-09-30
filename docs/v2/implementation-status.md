# V2 implementation status

Updated 2026-09-30. Specifications cover the full scope; runtime delivery is incremental and the full V2 platform is not yet accepted.

## Delivered milestones

| Milestone | Implemented scope | Verification |
| --- | --- | --- |
| V2-00 | Assessment, architecture, migration/backlog, evaluation/research, 27-group requirements, AGENT.md | Documentation checks |
| Initial V2-02 | Versioned fixture datasets/strategies/experiments, ranking metrics, split checks, snapshots and immutable experiment publication | 39 tests at milestone; two fixture cases pass |
| Runtime safety | Explicit V2 terminal bindings, loop fallback/order, denial traces and typed evidence/candidate outputs | 49 tests; v1 fingerprint unchanged |
| Scope/persistence | Mandatory Qdrant authorized-ID filter, content/scope-sensitive identities, no-overwrite traces and safe errors | 57 tests; provider request doubles, no live database |
| Retrieval adapters | Persistent BM25, exact lane, pinned Ollama embeddings/generation, Qdrant composition, config schemas and candidate trace metadata | 70 tests; no live semantic-quality claim |
| Structural/context/verification | Parent links/traversal, twelve query classes, whole-block context/quota decisions, explicit conflicts, complete quoted-sentence citation verification | 89 tests; full graph with provider doubles |
| Strategy experiment runtime | Local pinned reranker, explicit A–F graphs, experimental F routing, per-process comparison command, policy narrowing, stage metrics and 22 synthetic cases | 105 tests at implementation; subsequent real A–F results below |

## Current limits and next steps

- Native Ollama and Docker Desktop are now running on the 18 GiB host. Compose configuration and Qdrant/PostgreSQL startup passed. Real development runs expose generation timeouts and rejected claims; see [live findings](local-live-findings.md). Full Compose flow, PostgreSQL restart durability, representative quality and resource acceptance remain unverified. Ruff remains unavailable.
- The local-real profile is experimental. Immutable local originals, staged/approved corpus releases and pinned runtime loading are implemented; source/approval/PDF/scope tests cover them. Durable ingestion jobs, index-build promotion and representative corpus acceptance remain pending. See [corpus publication](corpus-publication.md).
- Claim verification checks complete quoted sentences only; general semantic entailment, inferred contradictions and calibrated evidence sufficiency remain pending.
- Query classification retains every lane by default. Real A–F experiments now execute with pinned Nomic, Qwen 2B and an offline CPU cross-encoder. All arms passed only 5/11 synthetic held-out expectations; no promotion is justified. Source-fidelity parsing now accepts adjacent-line citations, and failed runs retain completed retrieval metrics. See experiments/v2-07-generation.
- A pinned HotpotQA distractor validation subset now supplies sourced hard bridge/comparison questions and labeled supporting passages; the BM25 retrieval-only baseline and real A-F graph comparison are recorded. C reached recall@5 0.9583 on 48 question-scoped cases, but no arm passed more than 1/48 answer/citation expectations. It does not cover the full V2 domain. Independent domain held-out/adversarial data, calibrated per-class metrics, token telemetry, full experiment promotion/rollback and Studio inspection remain pending.
- Provider cancellation, advanced error-edge behavior, tools/corrective retrieval, experience memory and learning are not enabled. They remain gated by reproducible A–F evidence.

See [runtime contracts](runtime-contract.md), [local-real profile](local-real-profile.md), [verification contract](verification-contract.md), and [migration plan](migration-plan.md). Each milestone's evidence is in `experiments/`; none of the adapter tests establish real-model quality or production readiness.
