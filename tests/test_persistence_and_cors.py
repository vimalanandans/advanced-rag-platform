from pathlib import Path

from fastapi.testclient import TestClient

from rag_workbench.api import app
from rag_workbench.graph import pipeline_from_yaml
from rag_workbench.ingestion import ingest_path
from rag_workbench.observability import JsonTraceStore
from rag_workbench.runtime import WorkbenchRuntime


def test_json_trace_store_survives_runtime_recreation(tmp_path):
    root = Path(__file__).parent.parent
    store = JsonTraceStore(tmp_path / "traces")
    runtime = WorkbenchRuntime(trace_store=store)
    runtime.set_evidence(ingest_path(root / "data/fixtures/rag_basics.md"))
    plan = runtime.compile(pipeline_from_yaml((root / "configs/pipelines/baseline.yaml").read_text()))
    result = runtime.run(plan, "When should a RAG system abstain?")
    restored = JsonTraceStore(tmp_path / "traces").get(result.manifest.run_id)
    assert restored.graph_fingerprint == result.manifest.graph_fingerprint
    assert restored.status == "completed"


def test_local_studio_origins_receive_cors_preflight_headers():
    client = TestClient(app)
    response = client.options("/runs", headers={
        "Origin": "http://127.0.0.1:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "x-tenant-id,x-user-id,x-local-admin-token,content-type",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
