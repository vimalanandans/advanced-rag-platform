from pathlib import Path

import pytest

from rag_workbench.contracts import Evidence, RetrievalCandidate
from rag_workbench.local_real import local_real_runtime
from rag_workbench.reranking import LocalCrossEncoderReranker, model_fingerprint
from rag_workbench.strategy_graphs import ARMS, experiment_pipeline


def runtime(tmp_path):
    return local_real_runtime(environ={"RAG_WORKBENCH_EMBEDDING_MODEL": "test:latest", "RAG_WORKBENCH_EMBEDDING_REVISION": "digest",
                                      "RAG_WORKBENCH_EMBEDDING_DIMENSIONS": "2", "RAG_WORKBENCH_OLLAMA_MODEL": "test:latest",
                                      "RAG_WORKBENCH_GENERATION_REVISION": "digest", "RAG_WORKBENCH_STORAGE": str(tmp_path)})


@pytest.mark.parametrize("arm", list(ARMS))
def test_all_six_experiment_graphs_compile_with_expected_lanes(tmp_path, arm):
    engine = runtime(tmp_path)
    plan = engine.compile(experiment_pipeline(arm))
    nodes = {node.id: node for node in plan.pipeline.graph.nodes}
    assert {lane for lane in ["bm25", "dense", "structural", "exact"] if lane in nodes} == set(ARMS[arm])
    assert ("rerank" in nodes) == (arm in {"E", "F"})
    assert nodes["generate"].inputs["candidates"] == ("rerank.candidates" if arm in {"E", "F"} else "fuse.candidates")
    assert plan.pipeline.graph.outputs["answer"] == "claims.verified_answer"


def test_experimental_routing_avoids_dense_provider_call_for_identifiers(tmp_path):
    engine = runtime(tmp_path)
    classifier = engine.registry.execute("query.classifier@2.0.0", {"query": "AB-123"}, None, {"routing_policy": "lexical-identifiers@1.0.0"})
    result = engine.registry.execute("routed.retrieval.dense@1.0.0", {"query": "AB-123", "evidence": [], **classifier}, None, {})
    assert result == {"candidates": []}
    assert "dense" not in classifier["decision"].recommended_lanes


def candidate(identifier):
    item = Evidence(id=identifier, document_id=identifier, source_uri="file:///fixture", revision="1", content="complete evidence", title=identifier, locator="section:1")
    return RetrievalCandidate(evidence=item, lane="rrf", score=0.1, rank=1)


def test_reranker_preserves_evidence_and_rejects_truncation(tmp_path):
    (tmp_path / "model.safetensors").write_bytes(b"fixture-only")
    adapter = LocalCrossEncoderReranker(tmp_path, model_fingerprint(tmp_path), max_length=4)
    class Model:
        tokenizer = staticmethod(lambda *args, **kwargs: {"input_ids": [1, 2, 3]})
        predict = staticmethod(lambda *args, **kwargs: [0.1, 0.9])
    adapter._model = Model()
    docs = [candidate("a"), candidate("b")]
    result = adapter.rerank("query", docs, limit=2)
    assert [item.evidence.id for item in result] == ["b", "a"]
    assert result[0].evidence is docs[1].evidence
    adapter._model.tokenizer = lambda *args, **kwargs: {"input_ids": list(range(10))}
    with pytest.raises(ValueError, match="token bound"):
        adapter.rerank("query", docs)


def test_reranker_model_change_rejected_before_loading(tmp_path):
    (tmp_path / "model.safetensors").write_bytes(b"original")
    adapter = LocalCrossEncoderReranker(tmp_path, model_fingerprint(tmp_path))
    (tmp_path / "model.safetensors").write_bytes(b"changed")
    with pytest.raises(ValueError, match="fingerprint changed"):
        adapter.rerank("query", [candidate("a")])


def test_checked_in_dataset_is_pinned_and_split_validated():
    import json

    from rag_workbench.experimentation import DatasetManifest, corpus_fingerprint
    root = Path(__file__).parent.parent
    dataset = DatasetManifest.model_validate_json((root / "data/v2/dataset.json").read_text())
    corpus = [Evidence.model_validate(item) for item in json.loads((root / "data/v2/corpus.json").read_text())]
    assert dataset.corpus_revision == corpus_fingerprint(corpus)
    assert {case.split for case in dataset.cases} == {"development", "tuning", "held_out", "adversarial", "regression"}
    assert len(dataset.cases) == 22


@pytest.mark.parametrize("arm", list(ARMS))
def test_each_arm_executes_through_verified_terminal_with_provider_doubles(tmp_path, monkeypatch, arm):
    from rag_workbench.embeddings import OllamaEmbeddingProvider
    from rag_workbench.providers import OllamaModelProvider, QdrantVectorIndex
    monkeypatch.setattr(OllamaEmbeddingProvider, "encode", lambda self, texts, **kwargs: [[1.0, 0.0] for _ in texts])
    monkeypatch.setattr(QdrantVectorIndex, "create_index", lambda *args: None)
    monkeypatch.setattr(QdrantVectorIndex, "upsert", lambda *args: None)
    monkeypatch.setattr(QdrantVectorIndex, "search", lambda self, vector, limit=5, *, allowed_point_ids: [{"id": point_id, "score": 1.0} for point_id in allowed_point_ids][:limit])
    monkeypatch.setattr(OllamaModelProvider, "generate", lambda *args, **kwargs: "AB-123 requires a key. [a]")
    engine = runtime(tmp_path)
    engine.set_evidence([Evidence(id="a", document_id="a", source_uri="file:///fixture", revision="1", content="AB-123 requires a key.", title="Key", locator="section:1")])
    engine.registry._executors["ranking.local@1.0.0"] = lambda inputs, *_: {"candidates": inputs["candidates"]}
    result = engine.run(engine.compile(experiment_pipeline(arm)), "What does AB-123 require?")
    assert not result.abstained
    assert result.claims[0].support == "supported"
    assert result.manifest.node_executions[-1].node_id == "claims"
