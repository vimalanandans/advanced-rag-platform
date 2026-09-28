# Operations Guide

Use Docker Compose for local services. The Compose API stores run manifests in PostgreSQL; without a database URL,
the local API uses durable JSON manifests under `RAG_WORKBENCH_STORAGE/traces`. The Studio uses `/api` through
its Vite proxy in local development, while the API also permits the local Studio origins through CORS.

## Provider profiles

`deterministic` is the default profile for reproducible development and all regression fixtures. It uses
in-process dense retrieval and evidence-constrained generation, so no model download is needed. To exercise
the real local adapters after Compose is healthy, start the stack with:

```bash
RAG_WORKBENCH_DENSE_MODE=qdrant RAG_WORKBENCH_GENERATION_MODE=ollama docker compose up --build
```

Ensure the selected `RAG_WORKBENCH_OLLAMA_MODEL` has been pulled into the local Ollama container first.
Adapter selection is platform configuration, not pipeline YAML; graph fingerprints remain comparable across
providers while run manifests record the generation model. An unavailable or invalid selected provider fails
the run and its trace—there is no silent deterministic fallback.
