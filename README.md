# RAG Engineering Workbench

A local-first reference platform for engineering, running, inspecting, and evaluating
versioned RAG pipelines. It treats RAG as an evidence-selection system: every answer
is grounded in permitted evidence with inspectable provenance, or explicitly abstains.

## Who it is for

RAG Product Owners compare strategies and releases; Data Engineers configure corpora and
retrieval lanes; Developers add independently composable components; Operators inspect
traces, budgets, errors, and evaluation regressions.

## Quick start

```bash
docker compose up --build
```

The control API is available at `http://localhost:8000/docs`; the Studio is at
`http://localhost:5173`. The stack is local: PostgreSQL, MinIO, Qdrant, Ollama, an API,
a worker, and the Studio. Pull an Ollama model before using live generation; tests use a
deterministic local generator and do not require a model download.

## Core model

Pipeline YAML compiles into a versioned `PipelineGraph` IR. The graph, not a component,
owns sequencing, branching, retries, and bounded loops. Components publish typed,
versioned capability manifests. Provider adapters isolate models, storage, vector stores,
and exporters. Every run records a graph fingerprint, versions, evidence, budget usage,
and trace events.

The baseline pipeline runs lexical/BM25, dense, and vectorless hierarchical retrieval,
then verifies evidence, packs bounded context, and returns cited output or abstention.

## Repository map

- `rag_workbench/` — contracts, graph compiler/runtime, retrieval, ingestion, APIs, and evaluation.
- `configs/pipelines/` — versioned declarative pipelines.
- `data/fixtures/` and `data/golden/` — small licensed deterministic examples and expected behavior.
- `apps/studio/` — inspector-oriented React/TypeScript workbench.
- `docs/` — architecture, ADRs, security, test/evaluation, and operating guidance.

Read [ARCHITECTURE.md](ARCHITECTURE.md) and [AGENTS.md](AGENTS.md) before changing behavior.
The acceptance standard is defined in [Definition of Done](docs/definition-of-done/README.md).
