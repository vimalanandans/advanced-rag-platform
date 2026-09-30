# Local reranker adapter research

Reviewed 2026-09-30. Primary source: [Sentence Transformers CrossEncoder API](https://www.sbert.net/docs/package_reference/cross_encoder/model.html).

The adapter uses local-files-only loading with remote code disabled and safetensors required. It scores query/passage pairs, preserves evidence identity and ranks only the authorized candidates supplied by the graph. A content fingerprint pins the complete local model directory at load time. Token-length checks reject inputs that would be silently truncated; candidate and batch limits are explicit.

No model is selected, downloaded or redistributed. License, M3 memory use, CPU/MPS feasibility and ranking gain require a separately supplied local model and benchmark. Unit doubles test sorting, evidence identity, input bounds and model drift. They do not prove ranking improvement. The optional `local-real` dependency group installs Sentence Transformers when requested by an operator.

Compare D and E on the same frozen data before promotion. F applies an explicit experimental lexical-only routing rule for identifier/phrase queries; the default graph retains all lanes. Neither optimization is accepted on source claims or synthetic tests alone.
