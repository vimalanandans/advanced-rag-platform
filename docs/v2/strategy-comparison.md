# A–F strategy comparison runtime

The graph factory implements A (BM25), B (dense), C (BM25+dense), D (C+structural), E (D+reranker), F (E+declared identifier/phrase routing). Fusion, verification, context and generation remain explicit graph nodes. Every arm terminates at claim verification. Routing returns empty candidates for disabled lanes through declared decision inputs; it does not secretly invoke other components.

## Local execution

Configure the [local-real models](local-real-profile.md). E/F also require:

- `RAG_WORKBENCH_RERANKER_PATH`: an existing local CrossEncoder model directory with safetensors.
- `RAG_WORKBENCH_RERANKER_REVISION`: SHA-256 directory identity from `rag_workbench.reranking.model_fingerprint(Path(...))`.
- `RAG_WORKBENCH_RERANKER_DEVICE`: `cpu` (default) or `mps`, subject to measured support.

Install the optional `.[local-real]` dependency group in the project environment if Sentence Transformers is unavailable. No model download or remote-code execution is performed by the adapter.

```bash
python3 scripts/run_strategy_comparison.py \
  --dataset data/v2/dataset.json \
  --corpus data/v2/corpus.json \
  --requested-at 2026-09-30T00:00:00+00:00 \
  --split held_out --all
```

Use `--arm A` through `--arm F` for one arm. All-arm execution uses one fresh process per arm so process-lifetime peak RSS has a useful scope. It retains every failed/preflight record and a comparison exit-status manifest; it does not silently omit failed arms. Successful execution is not promotion.

The checked-in dataset has 22 original synthetic cases across development, tuning, held-out, adversarial and regression splits, covering all twelve query classes. It includes unauthorized, obsolete and rejected evidence. Its corpus fingerprint pins content and policy metadata. These cases exercise machinery and guardrails, not representative domain quality or held-out statistical significance. Do not tune on the held-out cases and then claim them as independent evidence.

## Measurements and limitations

Records include nominated-stage ranking, per-stage ranking/latency, expected-claim checks, query-class fixture pass counts, abstention outcomes, attempted unsupported claims, process peak RSS and pinned input snapshots. Citation precision/coverage remain null when a trustworthy link-level metric is unavailable. Runtime token counts are estimates. Failed cases retain their denominator and fail the command.

Case policy constraints may narrow corpus/revision/applicability scope, never widen the caller scope. Unknown constraints are rejected. Candidate traces use IDs and scores; artifacts retain dataset queries/labels and belong in an access-controlled directory for private corpora.

The checked-in invocation currently fails preflight because local model configuration and services are absent. No real A–F quality or resource comparison is claimed. Corrective/agentic/learning slices remain gated until the real comparison is reproducible and accepted.
