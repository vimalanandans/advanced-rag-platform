from pathlib import Path

import pytest

from rag_workbench.contracts import (
    Budget, CapabilityManifest, ComponentManifest, Edge, EdgeKind, Loop,
    Node, Pipeline, PipelineGraph, RequestContext,
)
from rag_workbench.graph import GraphValidationError, pipeline_from_yaml
from rag_workbench.registry import ComponentRegistry
from rag_workbench.runtime import AuthorizationError, BudgetExceeded, WorkbenchRuntime


def setup_runtime(executor, *, fallback="abstain", looping=False):
    registry = ComponentRegistry()
    ports = {"answer": "answer", "citations": "evidence_list", "abstained": "bool"}
    registry.register(ComponentManifest(
        id="test.answer", version="1.0.0", category="test", description="test",
        capabilities=CapabilityManifest(category="test"), input_types={"query": "string"}, output_types=ports,
    ), executor)
    node = Node(id="result", component="test.answer@1.0.0", inputs={"query": "$query"}, outputs=ports)
    graph = PipelineGraph(
        schema_version="2.0.0", nodes=[node],
        outputs={key: f"result.{key}" for key in ports},
        edges=[Edge(source="result", target="result", kind=EdgeKind.FEEDBACK)] if looping else [],
        loops=[Loop(id="retry", nodes=["result"], exit_when="result.abstained == true",
                    budget=Budget(max_iterations=2), fallback=fallback)] if looping else [],
    )
    return WorkbenchRuntime(registry=registry), Pipeline(id="v2", version="2.0.0", budgets=Budget(max_iterations=2), graph=graph)


def answer(*_):
    return {"answer": "must not survive exhaustion", "citations": [], "abstained": False}


def test_v2_terminal_binding_does_not_depend_on_node_names():
    runtime, pipeline = setup_runtime(answer)
    result = runtime.run(runtime.compile(pipeline), "query")
    assert result.answer == "must not survive exhaustion"
    assert not result.abstained


def test_exhausted_loop_forces_abstention_and_records_fallback():
    runtime, pipeline = setup_runtime(answer, looping=True)
    result = runtime.run(runtime.compile(pipeline), "query")
    assert result.abstained
    assert "must not survive" not in result.answer
    assert not result.citations
    assert len(result.manifest.node_executions) == 3
    assert result.manifest.loop_outcomes == [{"loop_id": "retry", "status": "exhausted", "iterations": 2, "fallback": "abstain"}]
    assert runtime.trace_store.get(result.manifest.run_id).loop_outcomes == result.manifest.loop_outcomes


def test_loop_fail_fallback_persists_failed_terminal_manifest():
    runtime, pipeline = setup_runtime(answer, looping=True, fallback="fail")
    with pytest.raises(BudgetExceeded, match="exhausted"):
        runtime.run(runtime.compile(pipeline), "query")
    manifest = runtime.trace_store.list()[0]
    assert manifest.status == "failed"
    assert manifest.loop_outcomes[0]["fallback"] == "fail"


def test_loop_convergence_precedes_downstream_execution():
    calls = []
    def changing(*_):
        calls.append(1)
        return {"answer": str(len(calls)), "citations": [], "abstained": len(calls) == 2}
    runtime, pipeline = setup_runtime(changing, looping=True)
    runtime.registry.register(ComponentManifest(
        id="test.echo", version="1.0.0", category="test", description="echo",
        capabilities=CapabilityManifest(category="test"), input_types={"value": "answer"},
        output_types={"answer": "answer"},
    ), lambda inputs, *_: {"answer": inputs["value"]})
    graph = pipeline.graph.model_copy(update={
        "nodes": pipeline.graph.nodes + [Node(id="terminal", component="test.echo@1.0.0", inputs={"value": "result.answer"}, outputs={"answer": "answer"})],
        "edges": pipeline.graph.edges + [Edge(source="result", target="terminal")],
        "outputs": pipeline.graph.outputs | {"answer": "terminal.answer"},
    })
    pipeline = pipeline.model_copy(update={"graph": graph})
    result = runtime.run(runtime.compile(pipeline), "query")
    assert result.answer == "2"
    assert result.manifest.loop_outcomes[0]["status"] == "exited"


def test_authorization_denial_is_traced_before_components_run():
    runtime, pipeline = setup_runtime(answer)
    with pytest.raises(AuthorizationError):
        runtime.run(runtime.compile(pipeline), "private query", RequestContext(tenant_id="other", user_id="local-admin"))
    manifest = runtime.trace_store.list()[0]
    assert manifest.status == "failed"
    assert manifest.tenant_id == "other"
    assert not manifest.node_executions
    assert "private query" not in manifest.model_dump_json()


@pytest.mark.parametrize("bindings", [
    {"answer": "result.answer"},
    {"answer": "missing.answer", "citations": "result.citations", "abstained": "result.abstained"},
    {"answer": "result.abstained", "citations": "result.citations", "abstained": "result.abstained"},
])
def test_v2_rejects_missing_invalid_or_mistyped_terminals(bindings):
    runtime, pipeline = setup_runtime(answer)
    pipeline = pipeline.model_copy(update={"graph": pipeline.graph.model_copy(update={"outputs": bindings})})
    with pytest.raises(GraphValidationError):
        runtime.compile(pipeline)


def test_invalid_citation_elements_fail_at_component_boundary():
    runtime, pipeline = setup_runtime(lambda *_: {"answer": "bad", "citations": ["untyped"], "abstained": False})
    with pytest.raises(TypeError, match="elements"):
        runtime.run(runtime.compile(pipeline), "query")
    assert runtime.trace_store.list()[0].node_executions[-1].status == "failed"


def test_v1_fixture_fingerprint_remains_compatible():
    path = Path(__file__).parent.parent / "configs/pipelines/baseline.yaml"
    plan = WorkbenchRuntime().compile(pipeline_from_yaml(path.read_text()))
    assert plan.fingerprint == "bd09657a714267231398fb586187c369ee2b3c5a2ec805f5e37be63d008e619c"
