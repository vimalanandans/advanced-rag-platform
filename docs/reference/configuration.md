# Configuration Reference

Configuration is deliberately separated from public contracts. Set values in the process environment or Compose
environment; do not put local credentials, provider URLs, or customer-specific behavior in pipeline YAML.

## Control API and trace storage

| Variable | Default | Owner | Meaning |
| --- | --- | --- | --- |
| `RAG_WORKBENCH_LOCAL_ADMIN_TOKEN` | local development default | platform security | Local-admin request token. Set a non-default value outside test-only development. |
| `RAG_WORKBENCH_CORS_ORIGINS` | local Studio addresses | platform web boundary | Comma-separated permitted browser origins. |
| `RAG_WORKBENCH_DATABASE_URL` | unset | platform storage | Enables PostgreSQL JSONB run-manifest persistence. |
| `RAG_WORKBENCH_STORAGE` | unset | platform storage | Enables atomic JSON traces at `<storage>/traces` when PostgreSQL is not selected. |

Database storage takes precedence over JSON storage. With neither configured, traces are in memory and are
appropriate only for deterministic tests or short-lived local runs.

## Local provider profile

| Variable | Default | Allowed values / meaning |
| --- | --- | --- |
| `RAG_WORKBENCH_DENSE_MODE` | `deterministic` | `deterministic` or `qdrant`. Selects in-process or local indexed dense retrieval. |
| `RAG_WORKBENCH_GENERATION_MODE` | `deterministic` | `deterministic` or `ollama`. Selects deterministic evidence-constrained generation or a local Ollama adapter. |
| `RAG_WORKBENCH_QDRANT_URL` | `http://localhost:6333` | Local Qdrant endpoint used when dense mode is `qdrant`. |
| `RAG_WORKBENCH_QDRANT_COLLECTION` | `rag_evidence` | Local collection name for approved evidence vectors. |
| `RAG_WORKBENCH_OLLAMA_URL` | `http://localhost:11434` | Local Ollama endpoint used when generation mode is `ollama`. |
| `RAG_WORKBENCH_OLLAMA_MODEL` | `llama3.2` | Model already available to the local Ollama service. |

The implementation rejects unrecognized mode values and remote provider endpoints unless an adapter explicitly
opts in. A selected unavailable provider fails the run visibly; the runtime does not fall back.

## Studio development

| Variable | Default | Meaning |
| --- | --- | --- |
| `VITE_API_URL` | `/api` | Optional Studio API base URL override for a local development build. |
| `VITE_PROXY_TARGET` | `http://127.0.0.1:8000` | Vite development proxy target. Compose sets this to the `control-api` service. |

`VITE_*` values are frontend build configuration. Never use them for tokens or private connection information.

## Configuration examples

Deterministic local development:

```bash
export RAG_WORKBENCH_STORAGE="$PWD/.local"
export RAG_WORKBENCH_DENSE_MODE=deterministic
export RAG_WORKBENCH_GENERATION_MODE=deterministic
```

Provider-enabled local Compose run after the selected Ollama model is available:

```bash
RAG_WORKBENCH_DENSE_MODE=qdrant \
RAG_WORKBENCH_GENERATION_MODE=ollama \
RAG_WORKBENCH_OLLAMA_MODEL='<installed-local-model>' \
docker compose up --build
```


## Experimental V2 profile

`RAG_WORKBENCH_PROFILE` selects `deterministic` (default) or `local-real`. Local-real additionally requires
`RAG_WORKBENCH_EMBEDDING_MODEL`, `RAG_WORKBENCH_EMBEDDING_REVISION`, `RAG_WORKBENCH_EMBEDDING_DIMENSIONS`,
`RAG_WORKBENCH_OLLAMA_MODEL` and `RAG_WORKBENCH_GENERATION_REVISION`. Revisions are installed model digests.
The profile uses the existing local URLs/storage settings and defaults its Qdrant collection to `rag_evidence_v2`.
See [local-real instructions and limitations](../v2/local-real-profile.md). These settings do not prove provider readiness.
