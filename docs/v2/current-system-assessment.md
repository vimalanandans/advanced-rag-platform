# V2 current-system assessment

Assessment date: 2026-09-29. This assessment describes the inspected checkout, including existing uncommitted product documentation. It is not a production acceptance certificate.

## Decision

Evolve the current platform. Retain the graph IR, registry boundary, local-first adapters, evidence policies, deterministic fixtures, and Studio shell. No inspected subsystem justifies restarting the repository. Replace weak retrieval implementations behind new versioned contracts; do not silently change the deterministic baseline.

## Verified baseline

| Check | Result | What it proves / does not prove |
| --- | --- | --- |
| `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q` | 26 passed | Existing deterministic tests pass; only two golden evaluation cases exist. |
| `npm --prefix apps/studio run build` | Passed | TypeScript and production bundling; no browser interaction acceptance. |
| `python3 -m compileall -q rag_workbench` | Passed | Python syntax; not type safety or behavioral correctness. |
| `python3 scripts/check_docs.py` | Passed, seven API routes | Reference coverage and local links; not semantic correctness. |
| `docker compose config --quiet` | Blocked: Docker command unavailable | Compose syntax, startup, PostgreSQL restart persistence, and live providers remain unverified. |
| Local Markdown/PDF, citations, abstention, failure traces | Covered by passing tests | In-process runtime and JSON persistence; not a live Compose workflow. |

`rtk` is unavailable in this environment; standard commands were used. Do not report blocked checks as passing. The complete local-real profile has not been accepted.

## Subsystem decisions

| Subsystem | Current state | Strength | Weakness | Decision | Reason | Migration risk | Test coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Product and architecture | Documented | Evidence-first, local-first, provider-neutral | V2 requirements previously absent | KEEP + HARDEN | Preserve direction; add traceable specifications | Competing roadmaps | Documentation checker |
| PipelineGraph/compiler | Operational deterministic subset | Typed bindings, fingerprints, cycle/loop checks | Component configuration schemas not enforced; terminal result depends on node names | KEEP + HARDEN | Strengthen IR rather than adopt framework-owned orchestration | Existing YAML compatibility | Graph and remediation tests |
| Runtime | Operational deterministic subset | Registry execution; budgets; failed-node traces | Deadline checked around blocking calls; loop exhaustion does not force abstention; authorization errors occur before trace lifecycle | REFACTOR | Correct explicit safety and terminal semantics | Result and trace compatibility | Runtime/remediation tests; gaps need new cases |
| Component manifests | Partial | IDs, versions, ports, telemetry fields | Limits/config/errors incomplete; runtime list checks do not validate element types | KEEP + HARDEN | Make manifests enforceable | New strict validation may reject old graphs | Contract checks in graph tests |
| Authorization | Partial | Filters tenant/user/corpus/revision/time/applicability before passing evidence to lanes | Unrestricted corpus default needs explicit policy; indexed search has no provider-side eligibility filter | KEEP + HARDEN | Apply scope before candidate selection, including shared indexes | Filter/selectivity and scope migration | Tenant/revision fixtures; cross-scope indexed recall missing |
| Ingestion | Operational library slice | Markdown sections, PDF pages, hashes, locators | Auto-approves nonempty text; no managed source revisions, limits, OCR or structural hierarchy | REFACTOR | Preserve parser seam; add publication and provenance lifecycle | Evidence IDs and historical locators | PDF and duplicate-heading fixtures |
| Lexical retrieval | Partial | Transparent deterministic scoring | BM25-named component uses normalized term frequency, not full BM25; no persistent index | REPLACE | Add real BM25 under a new version; retain fixture behavior | Ranking changes | Single-lane smoke fixture |
| Dense retrieval | Deterministic fixture | Stable hash vectors and collision guard | Not semantic; Qdrant also receives hash vectors | REPLACE | Add explicit embedding provider and index identity | Dimension/model migration | Fake-index tests; no live semantics |
| Structural retrieval | Partial | Heading-weighted overlap | No tree or parent-child traversal despite descriptive naming | REFACTOR | Add explicit hierarchy and bounded expansion | Chunk/provenance changes | One baseline fixture |
| RRF/context/evidence gate | Partial | Explicit graph nodes; bounded packing | Sufficiency is any positive score; word counts approximate tokens; no omission reasons or qualifier checks | KEEP + HARDEN | Add measured verification/context contracts | More abstentions are possible | Baseline budget/abstention tests |
| Query classifier | Placeholder | Declared graph component | Always returns `all`; no classification or routing | REPLACE | Add versioned query decision, preserve safe default | Routing recall regression | No classification evaluation |
| Generation | Fixture plus partial Ollama adapter | Adapter binding outside graph | Two excerpts truncated to 220 characters; citations attached without claim validation | KEEP + HARDEN | Preserve fixture; verify claims and source completeness | Answer/result schema | Fake-model test only |
| Trace stores | Partial | Memory, JSON, PostgreSQL seam | Stores allow overwrite; index revision hardcoded; counts omit reconstructable retrieval decisions | KEEP + HARDEN | Immutable versioned runs with authorized inspection | Storage/schema migration | JSON recreation; no live PostgreSQL restart |
| Evaluation | Minimal operational fixture | Pipeline fingerprint, two golden cases | Citation inclusion/abstention only; no ranking, stage metrics, split or promotion system | REFACTOR | Preserve regression endpoint; add experiment runner | Avoid false metric equivalence | Two golden cases |
| Studio | Partial | Existing shell, run requests, activity | Hardcoded graph; several placeholder controls; lacks full evidence/experiment inspection | KEEP + HARDEN | Extend after instrumentation | API/type alignment | Build only; browser acceptance outstanding |
| Compose | Declared, unverified | Local services and PostgreSQL health check | Worker exits; MinIO unused; broad port bindings; mutable image tags | KEEP + HARDEN | Operationalize before calling it supported | Local networking/data migration | Docker unavailable |
| Agentic retrieval/learning | Planned | Strategy guide states guardrails | No executable planner, experience store or policy learning | DEFER | Baseline A–F must be reproducible first | Premature complexity | None |

REMOVE applies to unsupported claims and obsolete placeholders only after replacements are verified. Do not delete historical source documentation or remove deterministic fixtures.

## Highest-priority gaps

1. Make the authorization contract hold inside indexed candidate selection, not only after provider results return.
2. Fix graph terminal binding, loop-exhaustion fallback, strict configuration validation, and complete failure tracing before enabling corrective loops.
3. Capture candidates, versions and context decisions before claiming experiments are reproducible.
4. Replace fixture retrieval in a separate local-real profile; establish held-out evaluation before tuning.
5. Validate the M3 Docker path, dependency readiness and restart persistence on a machine with Docker Desktop.

See [migration plan](migration-plan.md) for sequencing and [requirements](requirements.md) for coverage. These are implementation requirements, not claims that the target exists.
