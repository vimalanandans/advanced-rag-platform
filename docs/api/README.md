# Local Control API Reference

The control API is a FastAPI application. During a local run, interactive documentation is available at
`/docs` and its machine-readable OpenAPI description is available at `/openapi.json`. This guide captures the
stable operator contract and local-admin behavior.

## Base URL and request scope

The default local address is `http://127.0.0.1:8000`. All routes except health and component discovery require
the following headers:

| Header | Required value |
| --- | --- |
| `X-Tenant-Id` | The pipeline tenant, `local` for the reference baseline. |
| `X-User-Id` | `local-admin` in the current single-admin release. |
| `X-Local-Admin-Token` | The value configured as `RAG_WORKBENCH_LOCAL_ADMIN_TOKEN`. |

The API returns `401` for an invalid local-admin token, `403` for a non-admin user, and `404` when a run or
pipeline is outside the current request scope. Do not place the token in browser source, logs, or committed
examples.

## Endpoints

### `GET /health`

Reports that the control API is reachable. It does not require request headers.

```json
{"status":"ok","mode":"local-first"}
```

### `GET /components`

Lists component manifests used by the compiler and Studio catalog. It does not require request headers. Each
manifest identifies the component/version, typed inputs and outputs, capabilities, configuration schema,
limits, errors, concurrency behavior, and telemetry event names.

### `POST /pipelines/validate`

Compiles the checked-in baseline graph and returns its immutable fingerprint and execution order. It validates
declared dependencies, component contracts, ports, capabilities, budgets, and bounded loops before execution.

```json
{"valid":true,"fingerprint":"<sha256>","execution_order":["classify","bm25","dense","vectorless","fuse","verify","context","generate"]}
```

### `POST /runs`

Executes the baseline pipeline. The only request body field is `question`.

```json
{"question":"When should a RAG system abstain?"}
```

The response contains `answer`, authorized `citations`, `abstained`, a bounded `context` plan, and a nested
immutable `manifest`. The manifest includes the graph fingerprint, component/model versions, token usage,
node execution events, status, and an error when applicable. A run must return citations or an explicit
abstention; it never returns an untraceable answer.

### `GET /runs`

Lists persisted manifests scoped to the local tenant and administrator. Raw evidence content is not included in
trace metadata.

### `GET /runs/{run_id}`

Returns one persisted manifest if it belongs to the requesting tenant and administrator; otherwise returns
`404`.

### `POST /evaluations/baseline`

Runs the versioned golden evaluation data for the baseline pipeline and returns pass/fail totals, individual
case results, and the pipeline fingerprint. Use it to compare a measured change—not as a substitute for new
fixtures when a retrieval strategy changes.

## Local example

Set a token in your local shell, start the API, and keep the value out of shell history where appropriate.

```bash
export RAG_WORKBENCH_LOCAL_ADMIN_TOKEN='<local-admin-token>'
uvicorn rag_workbench.api:app --host 127.0.0.1 --port 8000
```

Then make a scoped request from a separate terminal:

```bash
curl -X POST http://127.0.0.1:8000/runs \
  -H 'Content-Type: application/json' \
  -H 'X-Tenant-Id: local' \
  -H 'X-User-Id: local-admin' \
  -H "X-Local-Admin-Token: $RAG_WORKBENCH_LOCAL_ADMIN_TOKEN" \
  -d '{"question":"When should a RAG system abstain?"}'
```

For browser development, the Studio sends these local headers only to its configured local API. The Vite
`/api` proxy and server CORS policy are intentionally limited to the local Studio origins.
