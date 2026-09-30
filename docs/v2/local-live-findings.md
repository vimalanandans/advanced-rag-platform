# Local live verification — 2026-09-30

This is development evidence, not representative quality acceptance. Native Ollama 0.20.0 and Docker Desktop engine 29.8.1 were installed outside the initially probed PATH or stopped. Starting them resolved the earlier connection-refused prerequisite. The host reports 18 GiB RAM. Compose configuration passed; Qdrant 1.11.3 and PostgreSQL 16 containers started. Full application Compose startup, Studio and database restart durability remain separate checks.

## Observations and changes

Qdrant `/healthz` returns plain text. The JSON adapter now probes `/` and checks the service title. Local-real composition now exposes embedding query/document prefixes; they already participate in immutable vector-point identity. The installed Nomic model returns 768 dimensions. Its [model card](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) requires distinct search prefixes and lists Apache-2.0 licensing. This experiment uses its native dimensions without dimensional reduction.

Generation exposes explicit thinking, temperature and context-window settings, retained in asset metadata. Unspecified settings preserve prior behavior. The adapter rejects a prompt whose UTF-8 byte upper bound plus output reservation exceeds an explicitly selected context window, preventing silent prompt truncation. [Ollama's generation API](https://docs.ollama.com/api/generate) documents thinking and runtime options. No reasoning text is logged.

Installed Qwen 0.8B was selected only for a local development probe. The server initially allocated 131,072 context tokens on GPU. No model download was required. Model digests, graph snapshots and embedding settings are in each experiment record.

| Experiment | Completed | Expected cases passed | Observation |
| --- | --- | --- | --- |
| Arm A, defaults, 15 s deadline | 0/3 | 0/3 | All generation calls timed out |
| Arm D, thinking disabled, temperature 0, 60 s | 2/3 | 0/3 | One timeout; generated claims rejected |
| Arm D, same settings plus explicit 8192 context | 3/3 | 1/3 | 1.095–3.314 s; expected evidence ranked first for all three; two answers abstained after failed verification |

Records are retained under `experiments/v2-06-live/`. These are not controlled A-versus-D quality comparisons: configuration and warm state changed. The last two runs diagnose runtime behavior; the small development set cannot establish strategy improvement. Peak RSS describes the Python process only, excluding Ollama and Docker. No strategy promotion is justified. Next: inspect generation failures, complete equal-configuration A–F comparisons, measure the full service resource envelope and run held-out/adversarial cases.

## Six-arm follow-up

A pinned, offline CPU MiniLM reranker enabled real E/F runs. The installed Qwen 2B generator passed 2/3 initial development cases in arms B–F. A versioned prompt clarification regressed results; it remains experimental. Citation verifier 1.0.1 accepts an immediately adjacent citation line while retaining full source-sentence matching. The default prompt remains 2.0.0.

With the retained default prompt and revised parser, all six arms completed the 11 synthetic held-out cases; each passed only 5/11 expectations. Recall@5 was 1.0 for the six cases with relevant evidence labels, while generated claims failed verification. The five expected abstentions passed. The experiment does not justify reranking, routing or advanced-retrieval promotion. Preserve the held-out set; do not optimize against its answers. A real domain corpus is required for representative acceptance.

The native PostgreSQL integration check could not import the declared `psycopg` dependency. A project-local installation attempt encountered a malformed proxy; a direct retry failed DNS. PostgreSQL container startup alone is not persistence acceptance. These failures are recorded in the loop rather than waived.
