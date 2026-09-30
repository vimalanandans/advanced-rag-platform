# Persistent lexical and local embedding baseline

Reviewed 2026-09-30. Primary sources: [Stanford IR text, Okapi BM25](https://nlp.stanford.edu/IR-book/html/htmledition/okapi-bm25-a-non-binary-model-1.html), [Ollama API source](https://github.com/ollama/ollama/blob/main/docs/api.md), and [Ollama embedding capability](https://github.com/ollama/ollama/blob/main/docs/capabilities/embeddings.mdx).

The new lexical component uses term-frequency saturation and length normalization, with positive smoothed IDF and configurable k1/b. SQLite persists immutable token statistics. Scores derive from the authorized snapshot, so private documents do not affect document frequency or top-k. The old simplified lexical component remains version 1 for regression compatibility; the new component is `retrieval.bm25@2.0.0`.

Ollama supplies batched local embeddings through `/api/embed`. The adapter rejects truncation and checks a configured model digest before and after each batch. Dimension, normalization and query/document prefixes are explicit. No model is downloaded or chosen implicitly. Unit doubles verify contract behavior, not semantic quality.

Dataset: current repository fixtures and focused synthetic authorization/identifier/length cases. Metrics: known BM25 score calculation, deterministic ranking, exact-boundary matches, scope stability, persistent restart and malformed provider rejection. No held-out quality improvement is claimed. SQLite/query scope scanning and digest checks add costs that must be measured on M3; large corpora need an indexed scope/statistics design rather than assuming this reference path scales.

License: no new model or dataset is distributed. Model licensing and M3 memory/latency feasibility must be recorded before choosing a supported default. `jsonschema` is added for component configuration validation; it is separate from model selection. Query/document embedding differences stay behind the neutral identity contract. A dimension/model change creates a new versioned collection or compatible isolated point identities; an incompatible existing Qdrant collection is rejected.

Local readiness probes on 2026-09-30 found no listener at Ollama 11434 or Qdrant 6333. Docker is unavailable in this execution environment. Live generation, embedding quality and resource measurements remain blocked.
