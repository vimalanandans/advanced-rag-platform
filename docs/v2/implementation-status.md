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

## Current limits and next steps

- Ollama and Qdrant readiness probes return connection refused; Docker and Ruff are unavailable. Compose startup, PostgreSQL durability/concurrency and M3 memory/latency acceptance remain unverified.
- The local-real profile is experimental, using the checked-in corpus. Managed ingestion/publication, immutable source storage and corpus/index releases remain pending.
- Claim verification checks complete quoted sentences only; general semantic entailment, inferred contradictions and calibrated evidence sufficiency remain pending.
- Query classification retains every lane by default. Reranking and measured routing still need the A–F dataset/experiment milestone.
- Representative held-out/adversarial data, per-class metrics, token telemetry, full experiment promotion/rollback and Studio inspection remain pending.
- Provider cancellation, advanced error-edge behavior, tools/corrective retrieval, experience memory and learning are not enabled. They remain gated by reproducible A–F evidence.

See [runtime contracts](runtime-contract.md), [local-real profile](local-real-profile.md), [verification contract](verification-contract.md), and [migration plan](migration-plan.md). Each milestone's evidence is in `experiments/`; none of the adapter tests establish real-model quality or production readiness.
