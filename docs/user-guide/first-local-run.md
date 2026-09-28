# First Local Run

This walkthrough uses the deterministic profile. It is the safest first run because it is local, reproducible,
and does not need an Ollama model or Qdrant service.

## 1. Install local dependencies

Use Python 3.11+ and Node.js. From the repository root:

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
npm --prefix apps/studio ci
```

## 2. Start the API and Studio

In one terminal, choose a local admin token and start the API:

```bash
export RAG_WORKBENCH_LOCAL_ADMIN_TOKEN='<local-admin-token>'
export RAG_WORKBENCH_STORAGE="$PWD/.local"
uvicorn rag_workbench.api:app --host 127.0.0.1 --port 8000
```

In another terminal, start Studio:

```bash
npm --prefix apps/studio run dev
```

Open the local Studio address printed by Vite. The Studio talks to `/api`, which proxies to the local control API
in development. It should display **Saved locally** when the API is reachable.

## 3. Run and inspect the baseline

1. Keep the default question or ask an evidence-seeking question.
2. Select **Run**.
3. Confirm the result is either a grounded response with a citation or an explicit abstention.
4. Open the context drawer and inspect the eight node events: classify, BM25, dense, vectorless, fuse, verify,
   context, and generate.
5. Inspect the response token/context counts and the cited locator.

The default corpus is the checked-in Markdown fixture. The runtime also ingests local PDFs through
`ingest_path`; PDF import is currently a developer/data-engineer operation rather than a Studio upload feature.

## 4. Verify repeatability

Run the checks before accepting a change:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
npm --prefix apps/studio run build
python scripts/check_docs.py
```

For the complete local Compose stack and optional provider profile, follow the [operations guide](../operations/README.md)
and the [Definition of Done](../definition-of-done/README.md).

## Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Studio shows offline | API is not running or proxy target is wrong | Check `/health`, then verify `VITE_PROXY_TARGET` or `VITE_API_URL`. |
| `401` from a protected route | Token does not match the API process | Set the same `RAG_WORKBENCH_LOCAL_ADMIN_TOKEN` in the caller and API shell. |
| `403` from a protected route | Current release supports only `local-admin` | Use `X-User-Id: local-admin`; multi-user RBAC is later work. |
| Empty or abstained answer | No authorized evidence met verification | Inspect retrieval lanes and evidence policy; do not disable abstention. |
| Provider run fails | Qdrant/Ollama is unavailable or model is missing | Fix the local provider and rerun; selected providers do not silently fall back. |
