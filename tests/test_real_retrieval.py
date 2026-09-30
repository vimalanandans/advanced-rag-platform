import math
import sqlite3

import pytest

from rag_workbench.contracts import Evidence
from rag_workbench.embeddings import EmbeddingIdentity, OllamaEmbeddingProvider
from rag_workbench.lexical import ExactRetriever, PersistentBM25Retriever
from rag_workbench.retrieval import IndexedDenseRetriever
from rag_workbench.providers import QdrantVectorIndex


def doc(identifier, content):
    return Evidence(id=identifier, document_id=identifier, source_uri="file:///fixture", revision="1",
                    content=content, title=identifier, locator="section:1")


def test_bm25_uses_saturation_length_and_persists_counts(tmp_path):
    path = tmp_path / "lexical.sqlite"
    docs = [doc("short", "needle"), doc("long", "needle filler filler filler")]
    retriever = PersistentBM25Retriever(path)
    first = retriever.retrieve("needle", docs)
    assert [item.evidence.id for item in first] == ["short", "long"]
    expected = math.log1p(0.5 / 2.5) * 2.2 / (1 + 1.2 * (0.25 + 0.75 * 1 / 2.5))
    assert first[0].score == pytest.approx(expected)
    restored = PersistentBM25Retriever(path).retrieve("needle", docs)
    assert [item.score for item in restored] == [item.score for item in first]
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM terms").fetchone()[0] == 2


def test_bm25_scope_excludes_unauthorized_document_statistics(tmp_path):
    retriever = PersistentBM25Retriever(tmp_path / "index.sqlite")
    permitted = doc("permitted", "needle")
    before = retriever.retrieve("needle", [permitted])[0].score
    retriever.retrieve("needle", [doc("other", "needle " * 100)])
    after = retriever.retrieve("needle", [permitted])[0].score
    assert before == after
    assert retriever.retrieve("needle", []) == []


def test_exact_identifiers_do_not_match_prefixes_and_preserve_punctuation():
    docs = [doc("exact", "Use AB-123 only"), doc("prefix", "Use AB-1234 only")]
    assert [item.evidence.id for item in ExactRetriever().retrieve("Explain AB-123", docs)] == ["exact"]
    assert not ExactRetriever().retrieve("semantic question", docs)


def embedding_adapter():
    return OllamaEmbeddingProvider(EmbeddingIdentity(provider="ollama", model_id="test:latest", revision="digest", dimensions=2), batch_size=1)


def test_ollama_embedding_batch_normalization_and_no_truncation():
    adapter = embedding_adapter()
    calls = []
    def request(path, payload=None):
        calls.append((path, payload))
        if path == "/api/tags":
            return {"models": [{"name": "test:latest", "digest": "digest"}]}
        return {"embeddings": [[3.0, 4.0]]}
    adapter._request = request
    assert adapter.encode(["first", "second"], purpose="document") == [[0.6, 0.8], [0.6, 0.8]]
    batches = [payload for path, payload in calls if path == "/api/embed"]
    assert len(batches) == 2
    assert all(payload["truncate"] is False for payload in batches)


@pytest.mark.parametrize("vectors", [[[1.0]], [[float('nan'), 1]], [[0, 0]], []])
def test_ollama_rejects_invalid_embedding_batches(vectors):
    adapter = embedding_adapter()
    adapter._request = lambda path, payload=None: ({"models": [{"name": "test:latest", "digest": "digest"}]} if path == "/api/tags" else {"embeddings": vectors})
    with pytest.raises(ValueError):
        adapter.encode(["query"], purpose="query")


def test_ollama_rejects_model_drift_before_embedding():
    adapter = embedding_adapter()
    paths = []
    adapter._request = lambda path, payload=None: paths.append(path) or {"models": [{"name": "test:latest", "digest": "changed"}]}
    with pytest.raises(ValueError, match="digest changed"):
        adapter.encode(["query"], purpose="query")
    assert paths == ["/api/tags"]


def test_indexed_retrieval_uses_provider_vectors_without_lexical_anchor():
    class Embeddings:
        identity = EmbeddingIdentity(provider="fixture", model_id="semantic-double", revision="1", dimensions=2)
        def encode(self, texts, *, purpose):
            return [[1.0, 0.0] for _ in texts]
    class Index:
        def create_index(self, dimensions):
            assert dimensions == 2
        def upsert(self, point_id, vector, payload):
            self.point = {"id": point_id, "score": 1.0}
            assert vector == [1.0, 0.0]
        def search(self, vector, limit=5, *, allowed_point_ids):
            assert self.point["id"] in allowed_point_ids
            return [self.point]
    result = IndexedDenseRetriever(Index(), embeddings=Embeddings()).retrieve("automobile", [doc("car", "vehicle")])
    assert result[0].evidence.id == "car"


def test_qdrant_rejects_incompatible_existing_dimensions():
    adapter = QdrantVectorIndex()
    adapter._request = lambda *args: {"result": {"config": {"params": {"vectors": {"size": 64, "distance": "Cosine"}}}}}
    with pytest.raises(ValueError, match="incompatible"):
        adapter.create_index(768)


def test_local_real_profile_requires_explicit_model_identity():
    from rag_workbench.local_real import local_real_runtime
    with pytest.raises(ValueError, match="requires explicit"):
        local_real_runtime(environ={})


def test_local_real_graph_compiles_and_rejects_invalid_component_config(tmp_path):
    from pathlib import Path
    from rag_workbench.local_real import local_real_runtime
    from rag_workbench.graph import pipeline_from_yaml, GraphValidationError
    runtime = local_real_runtime(environ={
        "RAG_WORKBENCH_EMBEDDING_MODEL": "test:latest", "RAG_WORKBENCH_EMBEDDING_REVISION": "digest",
        "RAG_WORKBENCH_EMBEDDING_DIMENSIONS": "2", "RAG_WORKBENCH_OLLAMA_MODEL": "generator:latest",
        "RAG_WORKBENCH_STORAGE": str(tmp_path), "RAG_WORKBENCH_GENERATION_REVISION": "generation-digest",
        "RAG_WORKBENCH_EMBEDDING_QUERY_PREFIX": "search_query: ",
        "RAG_WORKBENCH_EMBEDDING_DOCUMENT_PREFIX": "search_document: ",
    })
    pipeline = pipeline_from_yaml((Path(__file__).parent.parent / "configs/pipelines/local-real.yaml").read_text())
    assert runtime.embedding_identity["query_prefix"] == "search_query: "
    assert runtime.embedding_identity["document_prefix"] == "search_document: "
    assert runtime.compile(pipeline).pipeline.graph.schema_version == "2.0.0"
    next(node for node in pipeline.graph.nodes if node.id == "bm25").config["limit"] = -1
    with pytest.raises(GraphValidationError, match="configuration"):
        runtime.compile(pipeline)


def test_qdrant_health_uses_json_identity_endpoint():
    adapter = QdrantVectorIndex()
    calls = []
    adapter._request = lambda method, path: calls.append((method, path)) or {"title": "qdrant - vector search engine"}
    assert adapter.health()
    assert calls == [("GET", "/")]
    adapter._request = lambda *_: {"title": "other service"}
    assert not adapter.health()


def test_embedding_prefix_is_applied_by_purpose():
    identity = EmbeddingIdentity(provider="ollama", model_id="test:latest", revision="digest", dimensions=2,
                                 query_prefix="search_query: ", document_prefix="search_document: ")
    adapter = OllamaEmbeddingProvider(identity)
    calls = []
    def request(path, payload=None):
        if path == "/api/tags":
            return {"models": [{"name": "test:latest", "digest": "digest"}]}
        calls.append(payload["input"])
        return {"embeddings": [[1, 0]]}
    adapter._request = request
    adapter.encode(["automobile"], purpose="query")
    adapter.encode(["vehicle"], purpose="document")
    assert calls == [["search_query: automobile"], ["search_document: vehicle"]]


def test_generation_options_are_explicit_and_context_overflow_rejected(monkeypatch):
    import io
    import json
    from rag_workbench import providers
    calls = []
    def request(req, **kwargs):
        calls.append(json.loads(req.data))
        return io.BytesIO(b'{"response": "verified"}')
    monkeypatch.setattr(providers, "urlopen", request)
    adapter = providers.OllamaModelProvider(think=False, temperature=0, context_window=512)
    assert adapter.generate("small prompt", max_tokens=128) == "verified"
    assert calls[0]["think"] is False
    assert calls[0]["options"] == {"num_predict": 128, "temperature": 0, "num_ctx": 512}
    with pytest.raises(ValueError, match="reservation"):
        adapter.generate("x" * 500, max_tokens=128)
    assert len(calls) == 1
