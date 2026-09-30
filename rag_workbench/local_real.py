"""Explicit local-real composition; no implicit model choice or fixture fallback."""

from __future__ import annotations

import os
from pathlib import Path

from rag_workbench.contracts import CapabilityManifest, ComponentManifest
from rag_workbench.embeddings import EmbeddingIdentity, OllamaEmbeddingProvider
from rag_workbench.ingestion import ingest_structural_path
from rag_workbench.lexical import ExactRetriever, PersistentBM25Retriever
from rag_workbench.observability import TraceStore
from rag_workbench.providers import OllamaModelProvider, QdrantVectorIndex
from rag_workbench.registry import baseline_registry
from rag_workbench.retrieval import IndexedDenseRetriever
from rag_workbench.runtime import WorkbenchRuntime


def local_real_runtime(*, trace_store: TraceStore | None = None, environ: dict[str, str] | None = None) -> WorkbenchRuntime:
    values = os.environ if environ is None else environ
    required = ["RAG_WORKBENCH_EMBEDDING_MODEL", "RAG_WORKBENCH_EMBEDDING_REVISION", "RAG_WORKBENCH_EMBEDDING_DIMENSIONS", "RAG_WORKBENCH_OLLAMA_MODEL", "RAG_WORKBENCH_GENERATION_REVISION"]
    if any(not values.get(key) for key in required):
        raise ValueError("local-real requires explicit embedding model, revision, dimensions and generation model/revision")
    identity = EmbeddingIdentity(provider="ollama", model_id=values[required[0]], revision=values[required[1]], dimensions=int(values[required[2]]))
    endpoint = values.get("RAG_WORKBENCH_OLLAMA_URL", "http://localhost:11434")
    embedding = OllamaEmbeddingProvider(identity, url=endpoint)
    collection = values.get("RAG_WORKBENCH_QDRANT_COLLECTION", "rag_evidence_v2")
    dense = IndexedDenseRetriever(QdrantVectorIndex(values.get("RAG_WORKBENCH_QDRANT_URL", "http://localhost:6333"), collection), embeddings=embedding)
    lexical = PersistentBM25Retriever(Path(values.get("RAG_WORKBENCH_STORAGE", ".local")) / "indexes" / "bm25-v2.sqlite")
    registry = baseline_registry(dense_retriever=dense, generation_provider=OllamaModelProvider(endpoint, values["RAG_WORKBENCH_OLLAMA_MODEL"], revision=values["RAG_WORKBENCH_GENERATION_REVISION"]))
    for identifier, retriever in (("retrieval.bm25@2.0.0", lexical), ("retrieval.exact@1.0.0", ExactRetriever())):
        name, version = identifier.split("@")
        registry.register(ComponentManifest(
            id=name, version=version, category="retrieval.lexical", description="Persistent BM25" if name.endswith("bm25") else "Exact identifier and phrase retrieval",
            capabilities=CapabilityManifest(category="retrieval.lexical", suitable_query_classes=["exact_identifier", "exact_phrase", "semantic"], suitable_content_types=["markdown", "pdf"], cloud_supported=False),
            config_schema={"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}}, "additionalProperties": False},
            input_types={"query": "string", "evidence": "evidence_list"}, output_types={"candidates": "candidates"},
            errors=["index_unavailable", "invalid_snapshot"], concurrency="parallel-safe", telemetry_events=["component.completed", "component.failed"],
        ), lambda inputs, _context, config, selected=retriever: {"candidates": selected.retrieve(inputs["query"], inputs["evidence"], config.get("limit", 5))})
    from rag_workbench.v2_components import register_v2_components
    register_v2_components(registry, OllamaModelProvider(endpoint, values["RAG_WORKBENCH_OLLAMA_MODEL"], revision=values["RAG_WORKBENCH_GENERATION_REVISION"]))
    runtime = WorkbenchRuntime(registry=registry, trace_store=trace_store, model_version=f"ollama:{values['RAG_WORKBENCH_OLLAMA_MODEL']}@{values['RAG_WORKBENCH_GENERATION_REVISION']}",
                               embedding_identity=identity.model_dump(), index_revisions={"lexical": "bm25@2.0.0/ascii-stopwords-v1", "vector_collection": collection})
    runtime.set_evidence(ingest_structural_path(Path(__file__).parent.parent / "data/fixtures/rag_basics.md"))
    return runtime
