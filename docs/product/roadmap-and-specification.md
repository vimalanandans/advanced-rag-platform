# Product Roadmap and Planned Platform Specification

This document is the working product specification for the Local-First Graph-Native RAG Workbench. It joins
the product concept, engineering practices, target architecture, feature inventory, and an ordered roadmap.

It is intentionally explicit about delivery state. **Available** means present in the current repository;
**partial** means a contract or demo exists but the end-to-end product behavior is incomplete; **planned** means
it is a target, not a shipped feature. Roadmap phases are ordered by dependency and acceptance gate, not by
calendar date or delivery commitment.

## V2 scope and precedence

The [V2 requirements](../v2/requirements.md) and [migration plan](../v2/migration-plan.md) refine this roadmap for the attached V2 scope. They preserve the product vision while making the first V2 milestone explicit: real local embeddings, persistent BM25, Qdrant, structural hierarchy, RRF, reranking, query classification, evidence/context/claim verification, constrained generation and experiment comparison. Implementation status remains separate from this specification.

## 1. Product concept

The workbench helps a team answer this question with evidence: **which retrieval and answer pipeline should we
trust for this corpus and query class, and why?** It is an engineering and evaluation environment for RAG
systems, not a general-purpose chat client.

RAG is treated as an evidence-selection system. The platform must make source authorization, revision,
retrieval, verification, context allocation, generation, citations, abstention, and run history inspectable.
Advanced techniques are added only when evaluation shows a gap that the measured baseline cannot meet.

### Product promise

For a configured local corpus and a versioned pipeline, a user can run a question and inspect:

- which evidence was eligible before retrieval;
- which retrieval lanes returned each candidate, with rank and score;
- how fusion and evidence verification affected selection;
- what evidence fit the context budget and what was omitted;
- whether the response cited evidence or abstained;
- which graph, component, model, index revision, budgets, and trace produced the result.

The workbench must not imply that a citation proves a claim is correct. It exposes the source and decision path
so users can evaluate support and system behavior.

### Primary users and outcomes

| User | Primary question | Product outcome |
| --- | --- | --- |
| RAG product owner | Is this strategy an improvement worth accepting? | Compare baseline and experiment on versioned cases, inspect trade-offs, record an acceptance decision. |
| Data engineer | Is this source current, permitted, and represented faithfully? | Inspect ingestion, revision, provenance, approval, policy filters, and evidence locators. |
| RAG developer | Can I add this behavior without hiding dependencies or binding to one provider? | Implement a versioned component contract and compose it in a validated graph. |
| Operator | What ran, what failed, and can I reproduce it locally? | Start supported local profiles, inspect persisted manifests, diagnose dependencies and budgets. |
| Reviewer / trust owner | Is the evidence or answer safe to publish? | See source-level review state, authorization decisions, citations, abstentions, and audit metadata. |

## 2. Goals, boundaries, and success measures

### Product goals

1. **Evidence integrity:** only authorized, approved, current, applicable evidence can enter generation.
2. **Inspectable answers:** every completed answer has resolvable citations; insufficient evidence yields a clear abstention.
3. **Reproducible execution:** pipeline, component, prompt/model, index, corpus revision, and budget inputs are recorded.
4. **Composable orchestration:** a versioned `PipelineGraph` owns data/control flow; components own one declared capability.
5. **Provider portability:** storage, embeddings, vector search, and generation are replaceable adapters behind stable contracts.
6. **Local operation:** core development and deterministic evaluation run without network services; integrations are explicit local options.
7. **Measured progress:** retrieval strategies and product releases pass deterministic regression plus appropriate quality, policy, and operations gates.
8. **Understandable Studio:** users can inspect and debug before the platform adds visual graph authoring or autonomous behavior.

### Non-goals for the reference workbench

- A hosted multi-tenant SaaS or production security/compliance certification.
- A general consumer assistant, document editor, or enterprise content-management system.
- Automatic approval of extracted evidence or automatic promotion of a pipeline.
- A visual workflow authoring product in the first stable release.
- An unrestricted agent runtime or implicit access to shell, network, or customer tools.
- Adding every technique in `ADVANCED_RAG_STRATEGIES.md`; each technique needs a demonstrated use case and evaluation plan.

### Product success measures

Establish a measured baseline before setting numeric release thresholds. Do not invent thresholds before the
evaluation set and query classes are representative. Report results by query/content class, corpus, and pipeline
fingerprint.

| Measure | Definition | Release use |
| --- | --- | --- |
| Evidence recall@k | Fraction of expected evidence IDs present in the top-k candidate set. | Determines whether candidate retrieval can find support. |
| Citation precision | Fraction of cited evidence that supports the associated answer claims and is authorized. | Detects irrelevant or invalid citations. |
| Citation coverage | Fraction of material answer claims with at least one inspectable supporting citation. | Detects unsupported claims even when some citations exist. |
| Abstention correctness | Correct abstentions / expected abstentions, reported with false-abstention and unsupported-answer rates. | Balances safe refusal with answer usefulness. |
| Policy violation rate | Unauthorized, stale, rejected, or inapplicable evidence included in generation. | Hard release gate: must be zero in deterministic policy fixtures. |
| Context integrity | Budget compliance plus retention of required qualifiers, units, warnings, and provenance. | Guards against truncation and semantically incomplete context. |
| Reproducibility | Ability to identify all run inputs and repeat behavior under the same versions/data. | Required for regression analysis and incident review. |
| Operational behavior | API availability, persistence after restart, provider error visibility, latency, and resource usage. | Used for local-stack and adapter acceptance. |

## 3. Current product state

The repository is an early reference slice, not a complete platform. This inventory prevents roadmap language
from presenting a demo or contract as finished operational behavior.

| Capability | State | Current boundary / gap |
| --- | --- | --- |
| Typed pipeline contracts and YAML parser | Available | Supports semantic pipeline version and declared nodes, edges, budgets, and loops. |
| Graph compile, validation, and fingerprint | Available | Validates the baseline graph before the runtime executes it. |
| Component catalog and registry execution | Available | Baseline components are registered with typed manifests; manifest metadata should continue to mature as limits/errors become operational. |
| Evidence authorization filters | Available in runtime | Handles tenant, user, corpus, revision, validity, approval, and applicability before retrieval. Product corpus administration is not yet available. |
| Markdown ingestion | Available as a library function | Produces evidence blocks with revision and section locator; no ingestion API or Studio workflow. |
| PDF ingestion | Available as a library function | Extracts page text and page locator; scanned-page OCR, layout/table extraction, quality review, and visual verification are not provided. |
| BM25 lane | Available baseline | Current implementation scores evidence in process; it is not a persistent, scalable lexical index. |
| Dense lane, deterministic mode | Available as deterministic harness | Uses stable hashed term vectors as a stand-in. It demonstrates deterministic ranking and is not semantic embedding quality. |
| Dense lane, Qdrant mode | Partial | Persists/searches hashed term vectors in local Qdrant. A real embedding model/provider, dimension/version migration, and corpus index lifecycle are still needed. |
| Vectorless structural lane | Available baseline | Uses headings and text overlap; no learned page index or document-level tree construction. |
| RRF, evidence gate, context packing | Available baseline | Ranking and token estimates are simple baseline behavior; calibrate and evaluate before treating as production quality. |
| Deterministic generation | Available baseline | Produces extractive evidence snippets for repeatability; it is not a general synthesis model. |
| Ollama generation | Partial | Local adapter can generate from selected evidence; needs real provider smoke tests, prompt/version discipline, claim verification, and model-specific evaluation. |
| Run manifests | Available | Memory, JSON, and PostgreSQL adapters exist. Operational acceptance requires verifying restart persistence in Compose. |
| FastAPI control API | Available baseline | Health, catalog, validation, run, run list/detail, and baseline evaluation endpoints. Product CRUD and async job APIs are not present. |
| Studio inspector | Partial | Inspector-first React shell and local run integration exist. It is not yet a full corpus/pipeline/experiment management UI. |
| Docker Compose stack | Partial | Services are declared. Docker config/up smoke test has not been completed in the available environment; MinIO/worker integration is not yet a complete product path. |
| Evaluation | Available baseline | Golden tests and baseline endpoint exist. Dataset management, experiment comparison UI, stage-level metrics, and calibrated thresholds remain planned. |
| Authentication / tenancy | Planned beyond local admin | Current local administrator is not production authentication or enforced multi-tenant isolation. |

### Current release acceptance condition

The current code slice is useful for local deterministic graph and evidence-flow experimentation. Call the
**local reference slice accepted** only after the Compose stack is smoke-tested and demonstrates persisted
runs, a cited response and abstention, PDF/Markdown fixtures, visible failure behavior, and a trace after API
restart. Call **Qdrant/Ollama provider operation accepted** only after a separate live-provider run and
regression evaluation. See [Definition of Done](../definition-of-done/README.md).

## 4. Target platform specification

### 4.1 Product boundaries and configuration ownership

The target is a local-first workbench with three separately versioned configuration layers:

| Layer | Contains | Examples |
| --- | --- | --- |
| Platform | Deployment, installed adapters, secrets references, local limits, trace storage | Compose services, Qdrant URL, Ollama model, local-admin token source |
| Workspace/customer | Corpus membership, allowed identities, policy, evaluation collections, defaults | Allowed corpus IDs, revision rules, applicability tags |
| Pipeline | Typed nodes, edges, conditions, component config, prompt refs, budgets | Three retrieval lanes, fusion limits, verifier and context limits |

Configuration precedence must be documented and deterministic. Secrets must never appear in pipeline YAML,
graph fingerprints, browser storage, traces, or generated examples.

### 4.2 Core domain contracts

#### Source and evidence package

An immutable evidence package must carry:

- stable evidence and source/document IDs;
- source URI or local managed object key and source content hash;
- source revision, parser/chunker versions, and ingestion timestamp;
- content type and canonical representation;
- page, section, element, or structured-record locator;
- corpus and tenant/workspace scope;
- approval/review state and reviewer/audit metadata when applicable;
- allowed principals/policy reference, validity interval, and applicability tags;
- links between parent/child chunks, tables, figures, source pages, and derived summaries as needed.

Derived text, OCR, summaries, and vector representations must retain a resolvable edge to the source package.
Reprocessing with a changed parser, chunker, or extraction prompt creates a new derived revision; it must not
silently overwrite the evidence used by historical runs.

#### PipelineGraph IR

The graph format must be versioned independently of its human-readable name. It must represent:

- stable node IDs and component ID/version;
- typed config validated against a published schema;
- named typed input/output ports and explicit bindings;
- data, control, conditional, error, and feedback dependencies;
- declared entry points and terminal result contract;
- immutable prompt/template references and their versions;
- per-node and whole-run time, token, context, retry, concurrency, and tool budgets;
- bounded loops with exit predicate, limits, exhaustion outcome, and trace events;
- compiler validation errors with node/edge/path context;
- canonical graph serialization and deterministic fingerprinting.

Compilation must reject unknown components, unbound required ports, type mismatches, undeclared dependencies,
invalid conditions, unsafe cycles, incompatible capabilities, invalid budgets, and unversioned runtime assets.
No component may call another component by name.

#### Component manifest and capability model

Each component has a stable ID and semantic version plus category, description, config schema, typed input and
output schema, capability declarations, compatible query/content classes, limitations, resource limits,
concurrency contract, error contract, emitted telemetry, security/data handling notes, and tests/evaluation
requirements. Provider-specific objects remain inside adapters.

#### Provider contracts

Target provider families include document parsing, embeddings, lexical index, vector index, reranking,
generation, trace storage, object storage, and optional external exporters. Each adapter contract must specify
connection/health checks, timeout behavior, batching, idempotency, model/index identity, error mapping,
retryability, cancellation, data locality, and resource expectations.

Provider selection belongs to platform or workspace configuration. A graph references a provider-neutral
capability, not a URL or vendor SDK class. An explicitly selected adapter failure is a failed run. Fallback is
allowed only when declared in the graph/config, budgeted, visible in the manifest, and covered by evaluation.

#### Request and evidence authorization

Every run has a request scope. Before any evidence is returned to a retrieval lane, the platform enforces
tenant/workspace, corpus, principal/ACL, approval, revision, validity/freshness, and applicability constraints.
Authorization filters are mandatory and cannot be disabled by a node, prompt, or provider. Cache/index keys and
trace viewers must preserve the same scope.

#### Context and token budget

The context planner receives verified candidates and returns ordered included/omitted/truncated evidence IDs,
source locators, token estimates and actual counts where available, and reasons for exclusion. It preserves
qualifiers, units, warnings, table headers, and citation mapping. It enforces model input limits and pipeline
budgets before generation. Tokenizer/model estimation version is recorded.

#### Run manifest and trace

Every run, success or failure, records immutable identity and configuration: run/trace IDs, request scope,
pipeline and graph version/fingerprint, component versions, prompt version, embedding/model identity, corpus and
index revisions, policy version, budgets, actual resource use, retrieval candidate summaries, context plan,
citations, abstention, per-node timing/status, retry/loop/fallback events, and safe failure details.

Trace schemas are versioned. Raw content is omitted by default; evidence viewers re-check authorization at
read-time. Failed runs persist. Retention, deletion, export, and backup behavior must be documented before
operational adoption.

#### Evaluation and experiment model

Datasets are versioned and distinguish tuning from held-out regression data. Cases can include query class,
expected evidence, claim-level support, expected citations, abstention, policy restrictions, adversarial
conditions, and source revision. Experiments pin graph, prompts, models, embeddings, indexes, corpus snapshot,
and budgets. Results include stage-level retrieval metrics, citation precision/coverage, abstention errors,
policy violation count, latency, token/context use, and provider failures.

Promotion is an explicit review action with linked run/evaluation records. A passing aggregate score cannot
override a security-policy violation or a critical unsupported answer.

### 4.3 Target execution flow

#### Offline ingestion and publication

```text
Source import
  → malware / type / size checks
  → source hash and immutable revision
  → parse and profile pages/sections
  → extract structural text and typed objects
  → quality checks and optional human review
  → provenance-bearing evidence package
  → build versioned lexical, vector, and structural indexes
  → verify index snapshot
  → approve/publish corpus revision
```

#### Online query execution

```text
Request validation and authorization
  → query classification / explicit default route
  → policy-filtered BM25 + dense + structural retrieval
  → lane telemetry and candidate merge
  → fusion / optional measured reranking
  → evidence sufficiency and contradiction checks
  → context plan under token and source-diversity constraints
  → evidence-constrained generation
  → claim/citation verification
  → cited answer or explicit abstention
  → immutable run manifest and trace
```

All decisions, retries, provider failures, budgets, and fallback paths are inspectable. Agentic iteration is not
part of the initial target; any later bounded loop uses declared graph controls and per-loop limits.

### 4.4 Target local deployment

The reference Compose profile is expected to provide:

| Service | Responsibility | State expectation |
| --- | --- | --- |
| Studio | React/TypeScript inspection and experiment UI | Local browser only; proxy to control API |
| Control API | Authenticated local control and query endpoints | Health/readiness and explicit request-scope validation |
| Worker | Bounded ingestion, indexing, and evaluation jobs | Idempotent jobs; visible status and restart behavior |
| PostgreSQL | Pipeline metadata, policies, run manifests, job metadata | Versioned schema migrations and persistent volume |
| MinIO | Local evidence packages and derived artifacts | Bucket lifecycle/security policy and content-addressed objects |
| Qdrant | Dense vector index | Versioned collection/index identity and tested restore/rebuild path |
| Ollama | Optional local embeddings/generation models | Model availability checked and model IDs recorded |
| Local telemetry | Logs/traces/metrics store or bounded local files | Redaction by default and useful run correlation |

`docker compose up` must work without cloud access or credentials. Optional model download is a separately
documented provisioning action. Compose health checks and service readiness must distinguish “process started”
from “dependency usable.” The deterministic mode remains available even when optional providers are disabled.

## 5. Detailed feature inventory

### A. Product foundation and governance

| Feature | Target behavior | Priority |
| --- | --- | --- |
| Product/workspace/project identity | Name a local workbench workspace and group corpora, pipelines, datasets, and runs. | P0 |
| Configuration layers | Edit platform, workspace policy, and pipeline configuration in separate validated surfaces. | P0 |
| Capability catalog | Search/filter components by capability, supported input, limitations, status, and provider needs. | P0 |
| Version history | Inspect immutable pipeline, prompt, dataset, policy, and provider-profile revisions. | P0 |
| ADR and change record | Link material architecture/product decisions to requirements, spec, implementation, and evaluation. | P0 |
| Import/export | Export portable, provider-neutral pipeline and evaluation definitions with schema versions. | P1 |
| Release/promotion record | Record who approved a configuration, which evaluation passed, and rollback target; execute the A–F comparison specified in the [V2 evaluation plan](../v2/evaluation-plan.md). | P1 |

### B. Corpus and evidence lifecycle

| Feature | Target behavior | Priority |
| --- | --- | --- |
| Markdown/PDF import | Validate file type/size, hash source, create immutable revision, preserve section/page citations. | P0 |
| Corpus management | Create corpus, attach sources, view revision and ingestion state, remove/deprecate versions safely. | P0 |
| Parsing and structural chunking | Preserve headings, page boundaries, tables/procedures where supported, stable locator and parent-child relation. | P0 |
| Approval workflow | Mark extracted evidence pending, approved, rejected, or superseded with reason/audit metadata. | P1 |
| Source review viewer | Compare extracted text with source page and locator, including uncertainty markers. | P1 |
| Re-index/re-process | Create new derived revision based on parser/chunker/model version, retain old run reproducibility. | P1 |
| MinIO evidence package | Store source, normalized representation, page assets, and derived artifacts by content hash. | P1 |
| Specialized extraction | Add OCR, tables, figures, forms, warnings, and typed records with content-specific checks. | P2 |
| Connectors | Add external source import adapters only after local file workflow and permissions are stable. | P2 |

### C. Pipeline design and runtime

| Feature | Target behavior | Priority |
| --- | --- | --- |
| Versioned PipelineGraph | Stable, canonical graph IR with explicit typed nodes, ports, edges, conditions, budgets, and version. | P0 |
| Compiler and static validation | Show actionable schema/capability/type/dependency/cycle/budget errors before a run. | P0 |
| Baseline retrieval pipeline | Classification/default route, BM25, dense, vectorless, fusion, verification, context, generation. | P0 |
| Run lifecycle | Start, cancel where safe, list, inspect, and persist success/failure with idempotent run IDs. | P0 |
| Execution limits | Enforce latency, token/context, retries, loops, tools, and concurrency limits in runtime. | P0 |
| Checkpoint/replay | Resume only safe idempotent work and replay with pinned input/configuration. | P1 |
| Branching and error paths | Graph-declared route, conditional, error, and bounded feedback edges with visible outcomes. | P1 |
| Visual graph editing | Create/version graphs with validation feedback and inspectable diffs. | P2 |
| Subgraphs/templates | Reuse approved graph fragments while preserving explicit input/output contracts. | P2 |

### D. Retrieval and answer quality

| Feature | Target behavior | Priority |
| --- | --- | --- |
| Lexical retrieval | Persistent BM25 or equivalent index, analyzers/normalization, identifiers, ranked candidates. | P0 |
| True dense retrieval | Versioned local embedding provider with dimension/model identity and Qdrant indexing. | P0 |
| Structural/vectorless retrieval | Hierarchical page/section index, parent-child lookup, provenance-preserving traversal. | P0 |
| Hybrid fusion | RRF with configurable candidate limits and lane-level explainability. | P0 |
| Evidence verification | Sufficient-evidence gate, source policy checks, conflicting-source signals, explicit abstention. | P0 |
| Context planner | Budget-aware packing, qualifiers and structural context retention, omission reasons. | P0 |
| Citation resolution | Stable source/page/section links and evidence identity in API and Studio. | P0 |
| Claim support checks | Link answer claims to supporting evidence and mark unsupported or uncertain spans. | P1 |
| Reranking | Add a second-stage reranker only with measured candidate-recall and ranking improvement. | P1 |
| Query transformation | Versioned rewrite, expansion, decomposition, and multi-query components with bounded count and trace. | P1 |
| Conflict and freshness handling | Detect supersession/conflict; prefer policy-approved current versions or abstain. | P1 |
| Typed retrieval | Retrieve structured rows/procedures/FAQs with schema and unit checks. | P2 |
| Visual and multimodal retrieval | Retrieve figures/pages/crops with visual provenance and human-review path. | P2 |
| Graph retrieval | Traverse evidence-backed entities and relationships for multi-hop needs. | P2 |
| Agent subgraphs/tools | Permissioned sandboxed tools and bounded autonomous flow after baseline quality and safety. | P3 |

### E. Evaluation and experiment management

| Feature | Target behavior | Priority |
| --- | --- | --- |
| Versioned datasets | Store cases, expected evidence, answer claims, abstention, policy constraints, corpus snapshot. | P0 |
| Deterministic regression runner | Run pipeline graph/provider profile against fixtures and fail on critical regression. | P0 |
| Stage metrics | Separate ingestion, recall, fusion/rank, citation, abstention, latency, and budget outcomes. | P0 |
| Experiment comparison | Compare fingerprints side by side by case and query class. | P1 |
| Tuning/held-out split | Prevent promotion based on data used to tune the strategy. | P1 |
| Human review labels | Capture relevance, support, citation accuracy, and extraction-quality judgments. | P1 |
| Threshold calibration | Derive thresholds from representative data; version the calibration set and rationale. | P1 |
| Scheduled regression | Re-run accepted baselines when prompts, models, parsers, indexes, or dependencies change. | P2 |
| Cost/latency envelopes | Compare hardware/provider profile runtime and resource costs against product-defined limits. | P2 |

### F. Studio and operator experience

| Feature | Target behavior | Priority |
| --- | --- | --- |
| Pipeline/capability overview | Select active version and see graph identity, components, status, and validation. | P0 |
| Run inspector | Inspect question, cited response/abstention, retrieval lanes, evidence, context, tokens, and node events. | P0 |
| Error diagnosis | Show safe actionable errors, failed node, provider status, and remediation hints. | P0 |
| Corpus/evidence inspector | Search corpus revisions, approval state, policy metadata, and source locator. | P1 |
| Evaluation inspector | Browse dataset cases, metrics, failures, and compare experiments. | P1 |
| Settings and local privacy | Explain local storage, selected providers/models, token handling, and backup state. | P1 |
| Accessible responsive shell | Keyboard operation, labels, focus management, reduced motion, usable narrow view. | P0 |
| AI-assisted changes | Show scoped proposals as reviewable diffs; require explicit accept/reject and preserve undo. | P2 |
| Visual graph authoring | Edit graph with static validation, undo, versioned change sets, and export. | P2 |
| Collaborative review | Comments/approvals only after identity, permissions, and audit behavior are specified. | P3 |

### G. Security, tenancy, and operations

| Feature | Target behavior | Priority |
| --- | --- | --- |
| Local administrator | Clear development token and single-admin boundary; safe local bind defaults. | P0 |
| Authorization before retrieval | Enforced corpus/document policy applied before any provider query or context assembly. | P0 |
| Secrets handling | Local secret input outside browser storage and graph config; redact on traces and diagnostics. | P0 |
| Trace safety | No unauthorized evidence or credentials in ordinary trace payloads; read-time authorization. | P0 |
| Readiness/health checks | Dependency readiness, startup failures, version and adapter status visible. | P0 |
| Backup and restore | Document database/object/index backup and reproducible rebuild path. | P1 |
| Tenant namespace contract | Carry tenant scope through indexes, cache, traces, storage, API, and evaluation. | P1 |
| Authenticated multi-user RBAC | Principal/group roles, audit, corpus permissions, session/token lifecycle. | P2 |
| Security review and threat model | Abuse cases for upload, prompt injection, provider calls, trace exposure, and tools. | P1 |
| External telemetry/export | Explicit opt-in, redaction, destination allowlist, data contract, and security decision. | P2 |
| Production deployment | Separate deployment profile, secret manager, network/identity controls, SLOs, upgrades. | P3 |

## 6. Roadmap and phase gates

Phases are a dependency order. A phase can overlap only when its contracts and inputs are stable. Dates, staffing,
and performance targets are intentionally unset until product ownership and capacity are agreed.

### Phase 0 — Product baseline and decisions

**Purpose:** make the intended first user journey and quality bar decision-complete.

**Work:** approve the product concept and non-goals; define query/content classes; choose corpus fixture and
policy cases; agree evaluation metrics; record threat model and retention expectations; close ADR decisions for
graph IR, provider interfaces, trace persistence, and Compose topology.

**Exit gate:** each P0 capability has an owner, user outcome, contract, failure behavior, evaluation fixture,
and acceptance check. Numeric quality thresholds are set only after a measured baseline.

### Phase 1 — Local reference slice acceptance

**Purpose:** turn the current demo into a reproducible local engineering tool.

**Work:** run Compose config/up on a Docker-capable machine; correct service health/readiness and local secrets;
prove API-to-Studio `/api` flow; prove PostgreSQL trace persistence after API restart; prove Markdown and generated
PDF evidence return citations/abstention; verify failure traces; document start/stop/recovery.

**Exit gate:** documented deterministic Compose acceptance passes from a clean checkout without cloud
credentials. No Qdrant/Ollama feature is declared operational unless run with those services.

### Phase 2 — Corpus and evidence lifecycle

**Purpose:** move from a checked-in fixture to user-managed local corpora without losing provenance.

**Work:** corpus/source/version contracts; ingestion job status; file validation; immutable source hashes;
Markdown/PDF parsing; evidence package metadata and locators; approval/review state; object storage in MinIO;
lexical/structural index build and revision tracking; safe reprocess/deprecate behavior.

**Exit gate:** a user can import a local source, inspect source-to-evidence mapping and policy metadata, publish a
revision, run against it, and later reproduce the historical run against its pinned revision.

### Phase 3 — Measured retrieval baseline

**Purpose:** make all claimed retrieval families meaningful and measurable.

**Work:** replace hashed-term “dense” stand-in with a real, versioned local embedding adapter; define persistent
BM25 and vector index lifecycle; implement stable structural index; add exact identifier fixtures; track per-lane
recall and final citation behavior; calibrate evidence sufficiency and context estimates; add contradiction and
source freshness cases; implement instrumented query classification, measured reranking, structural hierarchy,
and claim-level verification as part of the initial V2 milestone.

**Exit gate:** three retrieval families run over the same authorized corpus snapshot; lane contributions can be
inspected; regression data demonstrates baseline behavior; provider/model/index versions are pinned; policy
violation fixtures remain zero.

### Phase 4 — Evaluation and experiment workbench

**Purpose:** make strategy selection a reproducible product workflow.

**Work:** dataset versions and tuning/held-out splits; stage metrics; run/experiment grouping; side-by-side
fingerprint comparison; quality/cost/latency and abstention reporting; review labels; promotion record and
rollback target.

**Exit gate:** a product owner can explain a go/no-go decision with case-level evidence and an immutable
evaluation record. Aggregate metrics cannot hide policy or critical citation failures.

### Phase 5 — Studio inspection and local operations completion

**Purpose:** make platform behavior understandable without reading raw API payloads.

**Work:** durable run browser; retrieval lane inspector; evidence/source viewer; context and token panel; useful
provider/readiness diagnostics; corpus revision browser; evaluation comparison; accessible keyboard and compact
viewport behavior; backup/restore and upgrade guides.

**Exit gate:** target users can complete their core task through Studio; API/runtime traces reconcile with visible
UI state; no raw secret or unauthorized evidence is exposed.

### Phase 6 — Advanced strategies and controlled extensibility

**Purpose:** add capabilities only where an evaluation gap and content class justify them.

**Candidate features:** query rewrite/expansion, decomposition, typed/table retrieval, OCR/visual retrieval,
evidence graph traversal and bounded corrective retrieval. Reranking, query classification, structural
parent-child behavior and claim verification belong to the initial V2 milestone in Phases 3–4; they are not
optional later research. Corrective and agentic work waits for reproducible A–F comparisons.

**Exit gate per strategy:** documented target problem; separate component and contract; representative fixtures;
baseline comparison; failure/latency/token bounds; source-level provenance; security review; measured acceptance
record. Research interest alone is not a roadmap commitment.

### Phase 7 — Multi-user and production-oriented deployment

**Purpose:** move beyond the local single-admin reference context when there is a real deployment owner.

**Work:** identity integration; RBAC and tenant isolation across all stores/caches/indexes; audit/retention;
secret management; secure deployment profiles; migrations/backups; SLO/alerting; threat modeling; data export and
deletion policy; load and recovery tests.

**Exit gate:** independent security and operational acceptance. This phase is outside the initial local
reference release and must not be implied by tenant fields in current data contracts.

## 7. Development and product practices

### Work starts with a problem brief

Each roadmap item begins with a short brief:

1. User and job to be done.
2. Observed problem and supporting evidence.
3. Query/content class and corpus assumptions.
4. Desired outcome and measurable signal.
5. Scope, explicit non-goals, risks, and dependencies.
6. Acceptance examples, including abstention/error cases.

### Decision sequence: goals → specification → architecture/design → implementation

Do not start implementation until the following artifacts agree:

| Sequence | Artifact | Must resolve |
| --- | --- | --- |
| 1. Goals | Product brief / outcome | User, problem, success measure, non-goals, priority |
| 2. Requirements | Functional + quality requirements | Inputs/outputs, policy, limits, failure behavior, acceptance scenarios |
| 3. Detailed specification | Contract/API/graph/data/evaluation spec | Fields, types, versions, validation, compatibility, errors, telemetry, migration |
| 4. Architecture | ADR and dependency/data-flow decision | Boundaries, ownership, provider choice, local operation, security implications |
| 5. Design | User flow, API examples, schema/sequence diagrams | Interaction, observability, accessibility, recovery, reviewability |
| 6. Implementation plan | Vertical slice, dependency order, rollout/rollback | Tasks, owner, risk, test/evaluation fixture, documentation updates |
| 7. Implementation | Code + docs + evaluation | Contract-compliant, bounded, observable behavior |
| 8. Acceptance | Definition of Done evidence | Automated checks, local smoke where relevant, product review, release record |

If new evidence invalidates a decision, return to the appropriate phase and update the requirement/spec/ADR;
do not bury a changed architecture inside code.

### Component development practice

- Keep components single-purpose and free of hidden component calls.
- Add a typed versioned manifest before enabling a component in a pipeline.
- Declare configuration, capabilities, input/output schemas, resource limits, error cases, concurrency, and telemetry.
- Keep vendor SDK types inside adapter modules; map provider errors into platform-neutral errors.
- Version prompts, parsers, chunkers, models, and embedding configuration that affect output.
- Make retries idempotent and bounded; record attempts and final behavior.
- Include configuration examples and limitations in the component reference.

### Retrieval development practice

- Define a query/content class and baseline failure before selecting an advanced technique.
- Ensure policy filtering precedes ranking and context assembly.
- Add expected evidence and hard-negative cases; include no-evidence, stale, unauthorized, conflicting, and malformed-source cases.
- Separate candidate recall, rank quality, context integrity, answer support, citation coverage, and abstention measures.
- Keep training/tuning cases distinct from held-out release cases.
- Preserve original evidence when adding summaries or compression; cite the original source.
- Reject a quality gain that introduces policy violations or loses a critical qualifier.

### UI and product design practice

- Make the active task and context visible. Keep advanced traces available without overwhelming the default view.
- Distinguish source evidence, system-generated summaries, model output, and user-approved changes.
- Make saves, provider mode, local data boundaries, failure, and recovery understandable.
- Require explicit review for AI-generated edits; show a diff and support undo.
- Design keyboard, focus, responsive, and reduced-motion behavior with each surface.
- Use the Product-UX guide as a requirement; do not introduce an interaction that contradicts its trust model.

### Security and data practice

- Threat-model source import, parser execution, prompt injection, tool access, cross-scope retrieval, trace viewing, and provider network calls.
- Enforce authorization at ingestion/publication, retrieval, cache lookup, trace read, and export boundaries.
- Treat source documents and retrieved content as untrusted input.
- Never put credentials in browser state, prompts, pipeline definitions, logs, or generated docs.
- Require explicit permissions and workspace sandboxing before a tool component exists.
- Make retention, deletion, backups, and data locality visible before external integration or multi-user release.

### Documentation and decision practice

- Keep this roadmap and `Goals.md` as product direction; keep contracts and pipeline YAML as current behavior source of truth.
- Label concepts **available**, **partial**, or **planned** in user-facing material.
- Each material architectural choice has an ADR with status and consequences.
- Update API/config references, examples, operating guides, and feature status in the same change as behavior.
- Avoid unsupported performance, accuracy, security, and production-readiness claims.

## 8. Release gates and ownership

### Required gates by change type

| Change | Minimum acceptance evidence |
| --- | --- |
| Component | Manifest validation, contract tests, telemetry/error path, resource bounds, usage docs |
| Retrieval strategy | Candidate/citation/abstention fixtures, policy cases, baseline comparison, per-lane metrics |
| Ingestion/parser | Source fidelity and locator fixtures, revision behavior, malformed/empty input handling, safe resource limits |
| Provider adapter | Local integration smoke, timeout/error mapping, identity recorded, no silent fallback, deterministic substitute tests |
| Pipeline/runtime | Compile/fingerprint, all node contracts, budget/loop failure tests, cited result or abstention, persisted terminal manifest |
| Studio | Type/build check, task flow, accessible labels/focus, local API integration, errors and privacy disclosure |
| Compose/operations | Compose config/up, health/readiness, persistence after restart, clean shutdown, recovery guidance |
| Security boundary | Threat model update, authorization matrix, abuse/failure tests, safe traces, reviewer approval |

### Product roles

Until the project assigns named people, use these role responsibilities in planning:

- **Product owner:** owns problem briefs, priority, non-goals, and quality trade-offs.
- **RAG/data owner:** owns corpus assumptions, evidence policies, evaluation coverage, and review labels.
- **Architecture owner:** owns contracts, ADRs, compatibility, and provider boundaries.
- **Implementer:** owns code, tests, telemetry, docs, and local reproducibility for the assigned change.
- **Reviewer:** checks evidence, security, correctness, clarity, and Definition of Done proof.
- **Operator:** validates install/upgrade, persistence, recovery, and provider readiness.

One person may fill multiple roles in the reference project, but each decision responsibility must be explicit.

## 9. Open product decisions

These require a product/architecture decision before their dependent phase begins:

1. Target hardware is decided: Apple Silicon M3 with Docker Desktop. Record installed RAM and measure the minimum resource envelope for local embedding, reranking and generation.
2. First supported languages, PDF characteristics, and whether scanned PDF OCR is in the P0 target.
3. Local identity model for workspaces, users, and corpus ACLs beyond the single-admin prototype.
4. Evidence package retention, deletion, backup, and source-object encryption expectations.
5. Which embedding and generation models are the initial supported local defaults, including their licenses and hardware needs.
6. Representative query/content evaluation set and numeric quality/latency thresholds after baseline measurement.
7. Whether asynchronous ingestion/evaluation jobs are required for the first supported release or only Compose demo.
8. Which product owner approves promotion from experiment to an accepted pipeline.

Resolve each decision with a short decision record that names the owner, options, evidence, selected outcome,
and affected spec/ADR. Until resolved, keep dependent functionality labelled planned or experimental.

## 10. Related references

- [Product Goals](../../Goals.md)
- [Advanced RAG Strategies](../../ADVANCED_RAG_STRATEGIES.md)
- [System Architecture](../architecture/system.md)
- [Pipeline/API Reference](../api/README.md)
- [Configuration Reference](../reference/configuration.md)
- [Evaluation Guide](../evaluation/README.md)
- [Product UX Guide](../product-ux/ai-native-workspace-guide.md)
- [Definition of Done](../definition-of-done/README.md)
- [ADRs](../adr/)
