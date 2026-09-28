from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rag_workbench.api import app
from rag_workbench.contracts import Budget, CapabilityManifest, ComponentManifest, Edge, EdgeKind, Loop, Node, Pipeline, PipelineGraph
from rag_workbench.graph import GraphValidationError
from rag_workbench.ingestion import ingest_path
from rag_workbench.registry import baseline_registry
from rag_workbench.runtime import BudgetExceeded, WorkbenchRuntime


def _manifest(identifier: str) -> ComponentManifest:
    return ComponentManifest(
        id=identifier, version="1.0.0", category="test", description="test component",
        capabilities=CapabilityManifest(category="test"), input_types={"query": "string"},
        output_types={"answer": "answer", "citations": "evidence_list", "abstained": "bool"},
    )


def _pipeline(component: str, budget: Budget | None = None) -> Pipeline:
    return Pipeline(id="test", version="1.0.0", budgets=budget or Budget(), graph=PipelineGraph(nodes=[Node(
        id="generate", component=component, inputs={"query": "$query"},
        outputs={"answer": "answer", "citations": "evidence_list", "abstained": "bool"},
    )], edges=[]))


def test_runtime_executes_registered_component_and_typed_bindings():
    registry = baseline_registry()
    registry.register(_manifest("test.echo"), lambda inputs, _context, _config: {"answer": inputs["query"], "citations": [], "abstained": False})
    runtime = WorkbenchRuntime(registry=registry)
    assert runtime.run(runtime.compile(_pipeline("test.echo@1.0.0")), "contract execution").answer == "contract execution"


def test_compiler_rejects_binding_without_an_explicit_edge():
    root = Path(__file__).parent.parent
    pipeline = _pipeline("generation.local@1.0.0")
    with pytest.raises(GraphValidationError, match="inputs must match"):
        WorkbenchRuntime().compile(pipeline)


def test_evidence_policy_filters_tenant_and_user_before_retrieval():
    root = Path(__file__).parent.parent
    runtime = WorkbenchRuntime()
    evidence = ingest_path(root / "data/fixtures/rag_basics.md")
    runtime.set_evidence([item.model_copy(update={"tenant_id": "other"}) for item in evidence])
    plan = runtime.compile(__import__("rag_workbench.graph", fromlist=["pipeline_from_yaml"]).pipeline_from_yaml((root / "configs/pipelines/baseline.yaml").read_text()))
    assert runtime.run(plan, "When should RAG abstain?").abstained


def test_failed_component_persists_terminal_trace():
    registry = baseline_registry()
    registry.register(_manifest("test.fail"), lambda *_args: (_ for _ in ()).throw(RuntimeError("provider failed")))
    runtime = WorkbenchRuntime(registry=registry)
    with pytest.raises(RuntimeError, match="provider failed"):
        runtime.run(runtime.compile(_pipeline("test.fail@1.0.0")), "fail")
    saved = runtime.trace_store.list()[0]
    assert saved.status == "failed" and "provider failed" in (saved.error or "")
    assert saved.node_executions[-1].status == "failed"


def test_output_budget_is_enforced_and_failure_is_persisted():
    registry = baseline_registry()
    registry.register(_manifest("test.long"), lambda *_args: {"answer": "one two", "citations": [], "abstained": False})
    runtime = WorkbenchRuntime(registry=registry)
    with pytest.raises(BudgetExceeded, match="output token"):
        runtime.run(runtime.compile(_pipeline("test.long@1.0.0", Budget(max_output_tokens=1))), "budget")
    assert runtime.trace_store.list()[0].status == "failed"


def test_tool_budget_is_enforced_at_component_boundary():
    def tool_component(_inputs, context, _config):
        context.record_tool_call()
        return {"answer": "ok", "citations": [], "abstained": False}

    registry = baseline_registry()
    registry.register(_manifest("test.tool"), tool_component)
    runtime = WorkbenchRuntime(registry=registry)
    with pytest.raises(BudgetExceeded, match="tool-call"):
        runtime.run(runtime.compile(_pipeline("test.tool@1.0.0")), "tool")
    assert runtime.trace_store.list()[0].status == "failed"


def test_repeated_markdown_headings_have_unique_evidence_ids(tmp_path):
    document = tmp_path / "duplicate.md"
    document.write_text("# Same\nfirst\n# Same\nsecond")
    evidence = ingest_path(document)
    assert len({item.id for item in evidence}) == len(evidence)


def test_api_requires_local_admin_context_for_run_and_scopes_run_access():
    client = TestClient(app)
    headers = {"X-Tenant-Id": "local", "X-User-Id": "local-admin", "X-Local-Admin-Token": "local-development-token"}
    assert client.post("/runs", json={"question": "When should RAG abstain?"}).status_code == 422
    response = client.post("/runs", headers=headers, json={"question": "When should RAG abstain?"})
    assert response.status_code == 200
    run_id = response.json()["manifest"]["run_id"]
    assert client.get(f"/runs/{run_id}", headers={**headers, "X-Tenant-Id": "other"}).status_code == 404


def test_declared_feedback_loop_executes_with_a_bounded_fallback():
    registry = baseline_registry()
    registry.register(_manifest("test.loop"), lambda *_args: {"answer": "", "citations": [], "abstained": False})
    pipeline = _pipeline("test.loop@1.0.0", Budget(max_iterations=2))
    pipeline = pipeline.model_copy(update={"graph": PipelineGraph(
        nodes=pipeline.graph.nodes,
        edges=[Edge(source="generate", target="generate", kind=EdgeKind.FEEDBACK)],
        loops=[Loop(id="retry", nodes=["generate"], exit_when="generate.abstained == true", budget=Budget(max_iterations=2))],
    )})
    runtime = WorkbenchRuntime(registry=registry)
    result = runtime.run(runtime.compile(pipeline), "loop")
    assert len(result.manifest.node_executions) == 3


def test_revision_policy_excludes_non_current_evidence():
    root = Path(__file__).parent.parent
    runtime = WorkbenchRuntime()
    runtime.set_evidence(ingest_path(root / "data/fixtures/rag_basics.md"))
    plan = runtime.compile(__import__("rag_workbench.graph", fromlist=["pipeline_from_yaml"]).pipeline_from_yaml((root / "configs/pipelines/baseline.yaml").read_text()))
    request = __import__("rag_workbench.contracts", fromlist=["RequestContext"]).RequestContext(tenant_id="local", user_id="local-admin", allowed_revisions={"local-demo:rag_basics": "not-current"})
    assert runtime.run(plan, "When should RAG abstain?", request).abstained
