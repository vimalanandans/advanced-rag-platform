# Definition of Done

This is the acceptance standard for a change to the Local-First Graph-Native RAG Workbench. It prevents a
feature from being labelled complete merely because code compiles or a demo appears to work.

## Universal gate

Every change must satisfy all of the following before it is **done**:

| Gate | Required evidence |
| --- | --- |
| Scope and decision | The requirement, affected contracts, and non-goals are documented. A material architectural choice has an ADR. |
| Contract and graph | Public interfaces are typed, semantically versioned where public, provider-neutral, and graph validation covers dependencies, schemas, capabilities, budgets, and loops. |
| Safety | Evidence authorization occurs before retrieval, including provider-side candidate selection, cache lookup, and every corrective iteration. Logs contain only safe metadata. No secret, cloud dependency, hidden downstream call, or silent fallback was added. |
| Observability | A trace records graph fingerprint, component versions, provider/model identity, budgets, node events, outcome, and failure reason. |
| Verification | Deterministic unit/contract/graph tests cover success and failure paths. Relevant golden evaluation data detects a regression. |
| Local operation | The documented local path works without cloud services. Configuration and examples are documented, including recovery or rollback behavior. |
| Review readiness | Documentation, configuration examples, and operator impact are updated. Existing unrelated workspace changes are untouched. |

## Change-specific gates

### Component

- Its manifest declares identity, semantic version, configuration schema, inputs, outputs, capabilities,
  limits, errors, concurrency behavior, telemetry, and tests.
- It has no hidden component chaining; every dependency is declared in `PipelineGraph`.
- It has bounded resource behavior and an observable failure result.

### Retrieval strategy

- It passes deterministic recall/citation/abstention fixtures alongside BM25, dense, or vectorless peers as
  applicable.
- It cannot expose unauthorized, stale, disallowed-revision, or inapplicable evidence to candidate selection or generation.
- It reports candidates, lane, rank, and score so fusion and verification can be inspected.
- Tuning changes are evaluated on separate versioned tuning and held-out sets; retain graph/strategy/data/model/index identities, stage metrics, baseline comparison, failure analysis, and an explicit acceptance decision.

### Pipeline or runtime behavior

- The pipeline validates and fingerprints before execution.
- A completed run returns inspectable citations or an explicit abstention; failures persist an immutable,
  inspectable manifest.
- Token, context, latency, iteration, and tool-call budgets are enforced at component boundaries.
- The baseline exercises lexical, dense, and vectorless retrieval before fusion and evidence verification.

### Provider or storage adapter

- The adapter is behind a provider-neutral platform interface and is selected by configuration, not a contract
  or customer code fork.
- Startup, connection, malformed response, and unavailable-provider paths have tests or an executable local
  smoke check.
- Selection is recorded in the run metadata. It never silently changes provider or falls back.
- It remains local by default; remote use requires an explicit adapter and documented security decision.

### Studio/API change

- The UI exposes the resulting state, citations/abstention, token/context use, trace events, and errors without
  exposing raw unauthorized evidence or secrets.
- API request authorization, error shape, CORS/proxy path when affected, and keyboard/accessibility behavior
  have appropriate automated or documented manual checks.
- The Studio production build succeeds and the local development proxy reaches the API.

## Release acceptance commands

Run the relevant commands and retain their output in review notes or CI:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
npm --prefix apps/studio run build
python -m compileall -q rag_workbench
docker compose config
docker compose up --build
```

For the deterministic profile, prove `GET /health`, pipeline validation, a cited run or abstention, trace
retrieval after API restart, and the Studio inspector path. For a Qdrant/Ollama provider profile, additionally
prove the selected local services are ready, the Ollama model exists, all three retrieval lanes execute, and
the persisted manifest names the selected model. Stop the stack after the smoke test unless it is intentionally
being used.

## What “done” means for the current vertical slice

The initial vertical slice is **accepted** only when the deterministic local profile meets every universal gate
and executes Markdown/PDF evidence through all three retrieval lanes to a cited answer or abstention with a
durable trace. The Qdrant/Ollama profile is **accepted** only after its separate provider smoke test and
regression fixture pass. Visual graph editing, multi-tenant authentication, skills/tools, cloud adapters, and
scaling are explicitly later work—not implied by this Definition of Done.


## V2-specific gates

Use the [V2 evaluation plan](../v2/evaluation-plan.md) for A–F comparisons and metric definitions. Record each meaningful loop in `experiments/`. The first V2 milestone includes reranking, query classification and claim verification; these cannot be postponed until agentic retrieval. A passing deterministic fixture is not evidence of semantic dense quality. The M3 local-real profile requires live operational acceptance and must retain the deterministic regression path.
