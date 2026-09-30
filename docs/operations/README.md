# Operations Guide

Operate the workbench in one of two local modes. The deterministic mode is the reproducible default for
development and regression checks. The Compose mode starts the complete local service topology for durable
PostgreSQL traces and optional Qdrant/Ollama adapter checks.

## Choose a local operating mode

| Mode | Use it when | Dependencies | Trace storage |
| --- | --- | --- | --- |
| Deterministic process | Developing, testing, or reproducing fixtures | Python + Node.js | JSON when `RAG_WORKBENCH_STORAGE` is set; otherwise memory |
| Docker Compose | Exercising local services and provider adapters | Docker Compose | PostgreSQL JSONB |

The Studio uses `/api` through Vite in local development. Compose sets the proxy target to `control-api`; the
API permits only configured local Studio origins through CORS.

## Start and verify Compose

```bash
docker compose up --build
```

Verify the API at `http://localhost:8000/health`, inspect its interactive API reference at
`http://localhost:8000/docs`, and open Studio at `http://localhost:5173`. Use the deterministic profile first:
it does not require a model download.

## Provider profiles

To exercise real local adapters after the Compose services are healthy, select them explicitly:

```bash
RAG_WORKBENCH_DENSE_MODE=qdrant \
RAG_WORKBENCH_GENERATION_MODE=ollama \
RAG_WORKBENCH_OLLAMA_MODEL='<installed-local-model>' \
docker compose up --build
```

Ensure the selected model has already been pulled into the local Ollama container. Adapter selection is
platform configuration, not pipeline YAML; graph fingerprints remain comparable across providers while run
manifests record the generation model. An unavailable or invalid selected provider fails the run and its
trace—there is no silent deterministic fallback.

## Diagnose a local issue

| Symptom | First check |
| --- | --- |
| Studio cannot run a question | API `/health`, proxy target, and local-admin request headers |
| Run failed | Persisted run manifest: node status, error, budget use, selected provider/model |
| No prior traces after restart | `RAG_WORKBENCH_DATABASE_URL` or `RAG_WORKBENCH_STORAGE` configuration |
| Qdrant/Ollama profile failed | Service readiness, local endpoint, selected model availability, and provider profile |
| Citations/abstention look wrong | Evidence authorization, retrieval lanes, verification, context plan, then fixture expectations |

For supported settings, storage precedence, and security boundaries, see [Configuration](../reference/configuration.md)
and [Security](../security/README.md).
