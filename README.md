# RAG Engineering Workbench

**Build RAG systems as evidence-selection systems, not chat models attached to a vector database.**

The RAG Engineering Workbench is a local-first reference platform for engineering, running, inspecting, and
evaluating versioned RAG pipelines. It makes the questions that matter operational: Which evidence was allowed
in? Which retrieval lane found it? What fit the context budget? Why did the system answer—or abstain?

Every run produces inspectable citations or an explicit abstention, plus a graph fingerprint, component and
provider versions, budget usage, and safe node-level trace metadata.

## What you can do today

- Run a validated baseline graph with simplified lexical scoring, deterministic hashed-vector retrieval, and heading-based structural retrieval. These are fixtures, not a real semantic dense baseline.
- Fuse, verify, and pack approved evidence before local generation.
- Ingest Markdown and PDF evidence with source, revision, section/page locator, and policy metadata.
- Inspect response, citations, context usage, node activity, errors, and persisted run manifests in Studio.
- Compare behavior with deterministic golden fixtures and the baseline evaluation endpoint.
- Choose deterministic local execution by default, or explicitly select local Qdrant and Ollama adapters.

## Who it is for

RAG product owners use it to compare strategies; data engineers use it to preserve trustworthy evidence;
developers use it to add composable components; operators use it to reproduce and diagnose runs. Read
[Product Goals](Goals.md) for the intended outcomes and deliberate non-goals.

## Start in the right mode

### Deterministic local development

Use this mode for the first run, regression fixtures, and fast iteration. It needs Python and Node.js but no
Docker, Qdrant, or model download.

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
npm --prefix apps/studio ci
```

Continue with the [first local run guide](docs/user-guide/first-local-run.md).

### Full local Compose stack

Use this mode when you need PostgreSQL trace storage or want to exercise local Qdrant/Ollama adapters.

```bash
docker compose up --build
```

The control API is available at `http://localhost:8000/docs`; Studio is at `http://localhost:5173`. The
deterministic profile remains the default. Pull an Ollama model only before selecting the Ollama provider
profile; see the [operations guide](docs/operations/README.md).

## How the baseline works

```text
question
  → authorize evidence
  → lexical + hashed-vector + heading-based retrieval
  → reciprocal-rank fusion
  → evidence verification
  → bounded context assembly
  → cited answer or explicit abstention
```

The `PipelineGraph`, not individual components, owns sequencing, branching, retries, and bounded loops.
Components publish typed, versioned manifests; providers stay behind provider-neutral interfaces. This is what
makes an execution reproducible and a provider replaceable.

## V2 evolution

The [V2 requirements and coverage map](docs/v2/requirements.md) defines the planned evolution, including the
[current-system assessment](docs/v2/current-system-assessment.md), target architecture and measured migration.
Real embeddings, persistent BM25, claim verification and the local-real profile are planned, not shipped.

## Documentation

Start from the [documentation index](docs/README.md):

- [Product goals](Goals.md) — users, outcomes, and non-goals.
- [Product roadmap and platform specification](docs/product/roadmap-and-specification.md) — current capability status, detailed feature inventory, phase gates, contracts, and development practices.
- [System architecture](docs/architecture/system.md) — dependency boundaries and execution flow.
- [API reference](docs/api/README.md) — local control endpoints and request scope.
- [Configuration reference](docs/reference/configuration.md) — profile, storage, and Studio settings.
- [Definition of Done](docs/definition-of-done/README.md) — what must be true before a change is accepted.
- [Advanced RAG Strategies](ADVANCED_RAG_STRATEGIES.md) — when to add a technique after measurement.

## Repository map

| Path | Purpose |
| --- | --- |
| `rag_workbench/` | Contracts, graph compiler/runtime, retrieval, ingestion, APIs, and evaluation. |
| `configs/pipelines/` | Versioned declarative pipeline definitions. |
| `data/fixtures/`, `data/golden/` | Licensed deterministic evidence and expected behavior. |
| `apps/studio/` | Inspector-oriented React/TypeScript workbench. |
| `docs/` | Product, architecture, API, operating, security, and quality guidance. |

Read [AGENTS.md](AGENTS.md) before changing behavior. It contains the engineering rules that preserve the
workbench’s local-first, evidence-first architecture.
