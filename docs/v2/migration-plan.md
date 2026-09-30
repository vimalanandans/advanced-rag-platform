# V2 migration and implementation plan

Status: implementation sequence; V2-00 and an initial fixture-only V2-02 slice are delivered. See [implementation status](implementation-status.md). Preserve the existing repository and deterministic profile. The first milestone is a measured local-real retrieval system, not an autonomous agent. [Assessment](current-system-assessment.md) records current evidence; [requirements](requirements.md) tracks coverage.

## Delivery rules

Use small vertical slices. Each slice states the problem/current behavior, baseline, hypothesis, minimal change, contracts, tests, evaluation, failure analysis, comparison, decision, docs and rollback. Store the loop record under `experiments/`; commit only the slice's files after reviewable validation. Never include unrelated edits. A blocked hardware/provider check remains blocked, not waived.

Maintain readable v1 traces and the checked-in baseline graph. Introduce new component/schema versions for changed ranking or result semantics. Create new indexes for embedding/parser/chunker changes, validate them, atomically switch a versioned release pointer, and retain the prior index until retention permits removal. Rollback restores the previous strategy plus its compatible graph, model, corpus and index identities.

## Ordered slices and gates

| Slice | Scope | Dependency | Exit evidence / rollback |
| --- | --- | --- | --- |
| V2-00 | Assessment, target, migration, evaluation, research, operating contract and requirement map | Repository audit | Documents agree; observed failures retained; no runtime acceptance implied |
| V2-01 | Local operational baseline and safety hardening | V2-00 | Compose config/up on M3; API/Studio flow, Markdown/PDF, cited/abstaining/error runs, PostgreSQL restart persistence and readiness; retain deterministic deployment |
| V2-02 | Experiment/dataset/strategy contracts and immutable records | V2-00; operational release gated by V2-01 | Dataset validation, disjoint splits, deterministic metrics, failed experiment persistence, reproducible fingerprints; keep old evaluation endpoint |
| V2-03 | Evidence publication, scope-aware indexes, embedding contract, persistent BM25 and real dense lane | V2-01/02 | Same authorized snapshot across lanes, migration/error tests, exact/semantic fixtures, measured local resources; switch back to fixture profile |
| V2-04 | Explicit hierarchy, RRF, sufficiency/context instrumentation and claim verification | V2-03 | Stable parent/child locators, required evidence/qualifier retention, conflicts and unsupported answers visible; version graph and verifier |
| V2-05 | Reranker and query classification/routing | V2-04 and measurable candidate recall | A–F comparison, held-out decisions and resource envelope; disable rejected candidate through prior strategy release |
| V2-06 | Studio experiment/evidence/claim inspection | Reliable V2-02–05 traces | UI reconciles with run records; browser, keyboard, responsive and privacy checks |
| V2-07 | Independent advanced retrieval experiments | Reproducible accepted A–F baseline | Each technique has primary-source research, targeted dataset, measured gain and failure bounds |
| V2-08 | Bounded corrective retrieval | V2-07 plus graph loop safety | Each iteration preserves scope; exhaustion/cancel/error tests; baseline comparison |
| V2-09 | Retrieval planner and separate experience memory | V2-08 | Permissioned graph actions; traceable stop decisions; experience cannot enter source citations |
| V2-10 | Offline policy learning, tuning and justified bandit/RL studies | High-quality held-out trajectories | Leakage checks, offline baseline, safety gates, human promotion and rollback; no automatic model deployment |

V2-03–05 together deliver the first V2 retrieval milestone: real embeddings + persistent BM25 + Qdrant + structural hierarchy + RRF + reranking + query classification + evidence/context/claim verification + constrained local generation + experiment comparison. Claim verification is not deferred to agentic research.

## Concise implementation backlog

| Category | Work |
| --- | --- |
| KEEP | Platform-owned IR; registry execution; provider-neutral boundaries; source documents; deterministic baseline; Studio shell; local trace-store interface |
| HARDEN | Pre-retrieval authorization in every index/cache; manifests/config validation; terminal bindings; deadlines/loops/failure traces; immutable records; local bindings/readiness; source approval and token accounting |
| REFACTOR | Simplified BM25 and hash-vector deployment assumptions; heading-only structural retrieval; placeholder classifier; context/generation truncation; evaluation pass-count model; fixed Studio graph |
| NEW | V2 contracts; versioned datasets/strategies/experiments; real embedding adapter; persistent lexical/index lifecycle; reranker; claim/conflict verification; A–F runner; comparison inspector |
| LATER | Typed/visual/graph and late-interaction retrieval, corrective/planner loops, experience memory, policy/model learning, multi-user and production deployment |

## Operational acceptance procedure

On M3 with Docker Desktop: record hardware/RAM, OS, Docker, image/model digests and resource allocation. Validate Compose; start services; verify readiness rather than process existence. Exercise authenticated API and Studio through `/api`; ingest Markdown and generated PDF; prove cited answer, abstention and failed-provider trace. Restart API and confirm PostgreSQL trace retrieval. Stop/restart services without deleting volumes and confirm pinned corpus/index identity. Document backup/restore and clean shutdown. Repeat local-real checks with provisioned models; an absent model must fail explicitly.

No Redis or cloud dependency is introduced merely to satisfy a diagram. Worker and MinIO cannot be called operational until durable job/source workflows use them. Native versus container model serving is chosen from measured M3 behavior and licensing, recorded in an ADR.

## Compatibility and promotion

Keep artifact readers backward compatible or supply explicit migrations with fixtures. Candidate strategy starts `experimental`, becomes `evaluated` after a valid run, and `accepted` only after policy/citation/resource gates and a recorded decision; otherwise `rejected`. A superseded release remains interpretable. Never use an aggregate score to override a security failure.
