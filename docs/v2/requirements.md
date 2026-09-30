# Advanced RAG Engineering Workbench V2 requirements

Status: specified. This document translates the V2 brief into implementation requirements. It does not mark unbuilt capabilities complete. Preserve and improve the existing system; no architectural blocker justifies a rebuild. The platform determines which retrieval strategy should be trusted for a corpus/query class, explains the selection, proves answer support, exposes insufficient/conflicting evidence, and improves through measured experiments.

## Source of truth and deliverables

- [Current-system assessment](current-system-assessment.md): observed implementation, KEEP/HARDEN/REFACTOR/REPLACE/REMOVE/DEFER decisions, risks, tests and blocked checks.
- [Target architecture](target-architecture.md): eight layers, contracts, invariants, local profiles, security and observability.
- [Migration plan](migration-plan.md): vertical slices, concise KEEP/HARDEN/REFACTOR/NEW/LATER backlog and rollback.
- [Evaluation plan](evaluation-plan.md): datasets, stage metrics, A–F experiment and promotion.
- [Research plan](research-plan.md): primary-source research protocol and Apple Silicon feasibility.
- [AGENT.md](../../AGENT.md): permanent operating contract and loop engineering.

The existing product roadmap remains useful background; the V2 migration plan controls V2 sequencing. Runtime behavior is established by versioned contracts and executable evidence. A document, adapter class or Compose service is not operational acceptance.

## Requirement coverage and acceptance map

| ID | Requirement | Implementation acceptance | Specification |
| --- | --- | --- | --- |
| V2-R01 | Audit before major architecture changes | Inspect code/tests/docs/ADRs/adapters/Studio/Compose, classify states, run baseline and retain failures | Assessment |
| V2-R02 | Preserve product and graph ownership | No shared-code customer forks, hidden component calls, framework-owned IR or provider SDK leakage | Target architecture; AGENT.md |
| V2-R03 | Authorization before retrieval | Scope, approval, revision, freshness and applicability enforced before each lane/index/cache query; adversarial isolation fixtures | Target architecture; evaluation |
| V2-R04 | Local operational slice | M3 Docker Desktop startup, health/readiness, Studio/API, Markdown/PDF, cited/abstaining/failed runs, PostgreSQL restart persistence | Migration V2-01 |
| V2-R05 | Evidence lifecycle | Immutable original/revisions, parser/chunker identity, explicit publication, ACL, structural provenance and inspection | Target evidence contract |
| V2-R06 | Real retrieval baseline | Exact/identifier lane, persistent BM25, real local embedding provider, Qdrant, hierarchy and RRF over same authorized snapshot | Migration V2-03/04 |
| V2-R07 | Embedding/index compatibility | Identity, dimensions, normalization, batching, health/resources, migration and incompatible-index failure tests | Target provider contract |
| V2-R08 | Query intelligence | Twelve classes, original query, confidence/capabilities/lanes/reason/fallback; routing evaluation | Target query contract; arm F |
| V2-R09 | First-class strategies | Versioned identity, classes, required components/models/indexes, resource/latency limits, limitations, dataset and promotion state | Target strategy contract |
| V2-R10 | Reranking | Recall established before reranking; RRF-only versus reranker comparison with coverage and resource gates | Evaluation arms D/E |
| V2-R11 | Context engineering | Fixed/structural/parent-child/neighbor/contextual/source/hierarchical variants; MMR, quotas, compression, class-specific budgets and inspectable decisions | Target context contract; research |
| V2-R12 | Claim verification | Segment claims, map evidence, verify support/citations, qualify/remove/abstain; confidence is not truth | Target claim contract; evaluation |
| V2-R13 | Temporal/conflict handling | Supersession, effective dates, applicability, jurisdiction, product versions and authority handled explicitly; conflicts remain visible | Target verification; evaluation |
| V2-R14 | Independent advanced experiments | Rewrite, expansion, multi-query, HyDE, decomposition, iterative/parent-child/contextual, late-interaction, learned sparse, typed/graph/visual retrieval each has targeted evidence | Research; migration V2-07 |
| V2-R15 | Corrective retrieval | Diagnose insufficiency; bounded allowed corrective actions; iteration traces and explicit exhaustion/cancel/error outcomes | Target graph bounds; migration V2-08 |
| V2-R16 | Retrieval planner | Only evidence acquisition/stop/clarification/abstention actions; graph permissions and budgets; no general autonomous agent | Target architecture; migration V2-09 |
| V2-R17 | Experience memory | Query/strategy/failure/action/ranking/context/citation/resource outcomes stored separately; never cited as source authority | Target architecture; research |
| V2-R18 | Retrieval policy/model learning | State includes class/corpus/candidates/coverage/sufficiency/action/resource history; offline policy or bandits first; tuning/preferences/RL justified by data and held-out evidence | Research; migration V2-10 |
| V2-R19 | Dataset system | Development/tuning/held-out/adversarial/regression splits, immutable corpus/case identities, representative cases and leakage checks | Evaluation dataset governance |
| V2-R20 | Stage metrics | Retrieval/evidence/context/answer/runtime/reproducibility measured separately with denominators and explicit unavailable values | Evaluation metric table |
| V2-R21 | Experiments and promotion | Hypothesis/baseline/candidate/data/config/case outputs/metrics/failures/decision persisted, with rollback and hard policy gates | Evaluation; experiments directory |
| V2-R22 | Studio V2 | Class/strategy/lanes/ranks/verification/context/claims/citations/conflicts/iterations/resources/versions/comparisons visible after backend instrumentation | Target Studio; migration V2-06 |
| V2-R23 | Reconstructable runs | Immutable success/failure records, asset versions, scope, original query under retention policy, scores/decisions/actions/budgets/errors; authorized reads | Target persistence contract |
| V2-R24 | Three execution profiles | Preserve deterministic; add local-real; gate advanced-research; selected provider errors never silently fall back | Target profiles; migration |
| V2-R25 | First V2 milestone and A–F gate | Full local-real baseline including reranker/classifier/claim checks/comparison accepted before corrective/agentic work | Migration V2-03–05; evaluation |
| V2-R26 | Loop engineering and completion | Structured loop record, tests, evaluation, failure diagnosis, comparison, decision, docs and scoped commit | AGENT.md; Definition of Done |
| V2-R27 | Primary-source research | Problem/paper/architecture/data/metrics/claims/limits/runtime/M3/license/contract mapping recorded before each advanced technique | Research plan |

## Verification of contradictions and temporal evidence

Eligible evidence must first pass authorization, approval and applicability; revision/freshness and source authority then resolve policy-defined precedence before relevance. Do not discard a conflicting authorized source merely because its similarity score is lower. Keep original and superseded identities traceable, distinguish historical questions from current-state questions, and qualify or abstain when no governing policy resolves disagreement. Effective date, jurisdiction and product version must be explicit case labels.

## Learning boundaries

Experience may influence strategy selection, never evidence truth or access rights. Training data excludes held-out labels and unauthorized trajectories. Candidate actions include stop, lexical, dense, structural, typed, graph, visual, rewrite, multi-query, decompose, rerank, ask-user and abstain. Reward can value supported evidence/citations/answers, correct abstention and resolution while charging for work/resources; policy violations are disallowed, not a compensable cost. Do not train the language model with RL first. Every learned artifact receives its own identity, offline comparison, acceptance decision and rollback.

## Delivery status

The specification and audit documents are delivered for V2-00. The initial V2-02 fixture experiment contracts/runner are implemented and tested; see [implementation status](implementation-status.md). Features in the table remain planned unless a subsequent experiment record demonstrates implementation and the relevant acceptance gates. Consult the assessment for current behavior; do not infer implementation from this coverage map.
