import pytest

from rag_workbench.contracts import Edge, Node, Pipeline, PipelineGraph
from rag_workbench.graph import GraphValidationError, compile_pipeline
from rag_workbench.registry import baseline_registry


def test_graph_fingerprint_is_stable_for_valid_pipeline():
    pipeline = Pipeline(id="demo", version="1.0.0", graph=PipelineGraph(
        nodes=[Node(id="classify", component="query.classifier@1.0.0", inputs={"query": "$query"}, outputs={"route": "string"})], edges=[]))
    first = compile_pipeline(pipeline, baseline_registry())
    second = compile_pipeline(pipeline, baseline_registry())
    assert first.fingerprint == second.fingerprint


def test_graph_rejects_unknown_component():
    pipeline = Pipeline(id="demo", version="1.0.0", graph=PipelineGraph(
        nodes=[Node(id="bad", component="missing@1.0.0")], edges=[]))
    with pytest.raises(GraphValidationError, match="unknown component"):
        compile_pipeline(pipeline, baseline_registry())


def test_graph_rejects_cycle_without_feedback_loop():
    pipeline = Pipeline(id="demo", version="1.0.0", graph=PipelineGraph(
        nodes=[Node(id="left", component="query.classifier@1.0.0", inputs={"query": "$query"}, outputs={"route": "string"}), Node(id="right", component="query.classifier@1.0.0", inputs={"query": "$query"}, outputs={"route": "string"})],
        edges=[Edge(source="left", target="right"), Edge(source="right", target="left")]))
    with pytest.raises(GraphValidationError, match="DAG"):
        compile_pipeline(pipeline, baseline_registry())
