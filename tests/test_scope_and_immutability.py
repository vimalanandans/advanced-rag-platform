from pathlib import Path
from uuid import uuid4

import pytest

from rag_workbench.contracts import Evidence, RunManifest
from rag_workbench.observability import JsonTraceStore, LocalTraceStore, TraceConflictError
from rag_workbench.providers import QdrantVectorIndex
from rag_workbench.retrieval import IndexedDenseRetriever


class SharedIndex:
    def __init__(self):
        self.points = {}
        self.allowed = []

    def create_index(self, _dimensions):
        pass

    def upsert(self, point_id, vector, payload):
        self.points[point_id] = {"id": point_id, "payload": payload, "score": 1.0}

    def search(self, _vector, limit=5, *, allowed_point_ids):
        self.allowed.append(allowed_point_ids)
        return [item for key, item in self.points.items() if key in allowed_point_ids][:limit]


def evidence(**updates):
    return Evidence(**({"id": "same-id", "document_id": "doc", "source_uri": "file:///public", "revision": "v1",
                        "content": "evidence", "title": "source", "locator": "section:1"} | updates))


def test_shared_index_filters_before_top_k_and_separates_tenants_and_content():
    index = SharedIndex()
    retriever = IndexedDenseRetriever(index)
    old = evidence(tenant_id="other")
    retriever.retrieve("evidence", [old], limit=1)
    current = evidence(content="new evidence")
    result = retriever.retrieve("evidence", [current], limit=1)
    assert result[0].evidence.content == "new evidence"
    assert len(index.points) == 2
    assert index.allowed[0] != index.allowed[1]
    assert len(index.allowed[1]) == 1


def test_empty_authorized_snapshot_does_not_query_provider():
    index = SharedIndex()
    assert IndexedDenseRetriever(index).retrieve("query", []) == []
    assert not index.allowed
    assert not index.points


def test_provider_scope_violation_fails_closed():
    index = SharedIndex()
    index.search = lambda *_args, **_kwargs: [{"id": "unauthorized", "score": 1.0}]
    with pytest.raises(PermissionError, match="authorized snapshot"):
        IndexedDenseRetriever(index).retrieve("query", [evidence()])


def test_qdrant_request_contains_mandatory_id_filter():
    adapter = QdrantVectorIndex()
    calls = []
    adapter._request = lambda *args: calls.append(args) or {"result": []}
    adapter.search([1.0], allowed_point_ids=["point"])
    assert calls[0][2]["filter"] == {"must": [{"has_id": ["point"]}]}
    assert adapter.search([1.0], allowed_point_ids=[]) == []
    assert len(calls) == 1


def manifest():
    return RunManifest(run_id=str(uuid4()), trace_id=str(uuid4()), tenant_id="local", pipeline_id="test",
                       pipeline_version="1.0.0", graph_fingerprint="fingerprint", component_versions={}, model_version="fixture")


@pytest.mark.parametrize("kind", ["memory", "json"])
def test_terminal_records_are_idempotent_but_not_replaceable(tmp_path: Path, kind):
    store = LocalTraceStore() if kind == "memory" else JsonTraceStore(tmp_path)
    original = manifest()
    store.save(original)
    store.save(original.model_copy(deep=True))
    changed = original.model_copy(update={"status": "failed", "error": "changed"})
    with pytest.raises(TraceConflictError):
        store.save(changed)
    returned = store.get(original.run_id)
    returned.status = "failed"
    original.status = "failed"
    assert store.get(original.run_id).status == "completed"
    assert not list(tmp_path.glob(".trace-*"))


def test_json_store_rejects_path_traversal(tmp_path):
    store = JsonTraceStore(tmp_path)
    with pytest.raises(KeyError):
        store.get("../private")
    with pytest.raises(KeyError):
        store.save(manifest().model_copy(update={"run_id": "../private"}))
    assert not list(tmp_path.iterdir())


def test_runtime_trace_redacts_provider_exception_content():
    from rag_workbench.graph import pipeline_from_yaml
    from rag_workbench.providers import LocalProviderProfile
    from rag_workbench.runtime import demo_runtime
    runtime = demo_runtime(provider_profile=LocalProviderProfile())
    def fail(*_):
        raise RuntimeError("https://user:private-token@provider/private-evidence")
    runtime.registry._executors["retrieval.bm25@1.0.0"] = fail
    plan = runtime.compile(pipeline_from_yaml((Path(__file__).parent.parent / "configs/pipelines/baseline.yaml").read_text()))
    with pytest.raises(RuntimeError):
        runtime.run(plan, "question")
    saved = runtime.trace_store.list()[0]
    assert "private" not in saved.model_dump_json()
    assert saved.error == "RuntimeError: execution failed"
    assert saved.node_executions[-1].error == saved.error
