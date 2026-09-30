# Experimental local-real profile

Implemented as a composition path, not yet operationally accepted. It uses persistent SQLite BM25, an exact lane, digest-pinned Ollama embeddings, filtered Qdrant search and local generation. The structural lane, classifier, context gate and generation/claim behavior are still being upgraded; this is not the complete first V2 milestone.

Set explicit model identities from the installed Ollama service; no downloads or model defaults are selected:

```bash
export RAG_WORKBENCH_PROFILE=local-real
export RAG_WORKBENCH_STORAGE="$PWD/.local"
export RAG_WORKBENCH_EMBEDDING_MODEL='<installed-model:tag>'
export RAG_WORKBENCH_EMBEDDING_REVISION='<installed-model-digest>'
export RAG_WORKBENCH_EMBEDDING_DIMENSIONS='<model-dimension>'
export RAG_WORKBENCH_OLLAMA_MODEL='<installed-generator:tag>'
export RAG_WORKBENCH_GENERATION_REVISION='<installed-generator-digest>'
export RAG_WORKBENCH_OLLAMA_URL=http://localhost:11434
export RAG_WORKBENCH_QDRANT_URL=http://localhost:6333
export RAG_WORKBENCH_QDRANT_COLLECTION=rag_evidence_v2
python3 -m uvicorn rag_workbench.api:app --host 127.0.0.1 --port 8000
```

The API selects `configs/pipelines/local-real.yaml` when this profile is set. Missing model identity fails startup; missing/drifted models and incompatible dimensions fail execution. This path still uses the checked-in fixture corpus. Corpus management/publication and held-out evaluation are separate upcoming slices.

The embedding adapter bounds batch count/input bytes and checks response cardinality, dimensions and finite/nonzero values. Both embedding and generation digest checks reject mutable-tag drift. Generation uses the remaining runtime deadline as its network timeout and sets an output-token limit; this is not preemptive cancellation and multiple HTTP calls can still exceed a single wall-clock deadline before runtime rejects the result.

Manifests now retain embedding identity, content/policy corpus fingerprint and candidate IDs/ranks/scores without raw evidence. BM25 token statistics persist at `<storage>/indexes/bm25-v2.sqlite`. Versioned component schemas are validated at compile time. The old deterministic profile and fingerprint remain available.

Verification covers deterministic scoring, database reopen, exact boundaries, scope isolation and provider response contracts. No local model or Qdrant listener was available during implementation, so live and M3 resource acceptance remain outstanding.
