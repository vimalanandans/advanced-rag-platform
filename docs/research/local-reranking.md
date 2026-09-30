# Local reranker adapter research

Reviewed 2026-09-30. Primary source: [Sentence Transformers CrossEncoder API](https://www.sbert.net/docs/package_reference/cross_encoder/model.html).

The adapter uses local-files-only loading with remote code disabled and safetensors required. It scores query/passage pairs, preserves evidence identity and ranks only the authorized candidates supplied by the graph. A content fingerprint pins the complete local model directory at load time. Token-length checks reject inputs that would be silently truncated; candidate and batch limits are explicit.

No model is selected, downloaded or redistributed. License, M3 memory use, CPU/MPS feasibility and ranking gain require a separately supplied local model and benchmark. Unit doubles test sorting, evidence identity, input bounds and model drift. They do not prove ranking improvement. The optional `local-real` dependency group installs Sentence Transformers when requested by an operator.

Compare D and E on the same frozen data before promotion. F applies an explicit experimental lexical-only routing rule for identifier/phrase queries; the default graph retains all lanes. Neither optimization is accepted on source claims or synthetic tests alone.


## Provisioned development candidate — 2026-09-30

The [Sentence Transformers model card](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2) describes an English MS MARCO passage reranker with 22.7M parameters and Apache-2.0 licensing. Upstream benchmark figures are not M3 measurements. We provisioned only safetensors, tokenizer/configuration and the model card from revision `233902d25c440f23af6f7d6e94d2946bac0bee0a`. Directory fingerprint: `626066419752140b03cbdce61a92f31405be0ff8c2592261cf7fbbab2697fe44`. Assets live under ignored `.local/models/ms-marco-MiniLM-L6-v2`; runtime loads offline on CPU with remote code disabled. This candidate supplies arms E/F; quality acceptance depends on repository experiments. No score threshold is interpreted as a probability of truth.
