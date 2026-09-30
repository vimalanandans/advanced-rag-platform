"""A–F graph variants keep every stage and dependency explicit."""

from __future__ import annotations

from pathlib import Path

from rag_workbench.contracts import Edge, Node, Pipeline
from rag_workbench.graph import pipeline_from_yaml

ARMS = {
    "A": ["bm25"],
    "B": ["dense"],
    "C": ["bm25", "dense"],
    "D": ["bm25", "dense", "structural"],
    "E": ["bm25", "dense", "structural"],
    "F": ["bm25", "dense", "structural"],
}


def experiment_pipeline(arm: str) -> Pipeline:
    if arm not in ARMS:
        raise ValueError("experiment arm must be A through F")
    path = Path(__file__).parent.parent / "configs/pipelines/local-real.yaml"
    pipeline = pipeline_from_yaml(path.read_text())
    pipeline.id = f"local-real-arm-{arm.lower()}"
    pipeline.description = f"Controlled A-F experiment arm {arm}; not promoted"
    retrieval_nodes = {"bm25", "dense", "structural", "exact"}
    retained = {node.id for node in pipeline.graph.nodes} - (retrieval_nodes - set(ARMS[arm]))
    nodes = [node for node in pipeline.graph.nodes if node.id in retained]
    edges = [edge for edge in pipeline.graph.edges if edge.source in retained and edge.target in retained]
    for node in nodes:
        if node.id == "fuse":
            node.inputs["candidate_lists"] = [f"{lane}.candidates" for lane in ARMS[arm]]
    if arm in {"E", "F"}:
        nodes.append(Node(id="rerank", component="ranking.local@1.0.0",
                          inputs={"query": "$query", "candidates": "fuse.candidates"}, outputs={"candidates": "candidates"}))
        for node in nodes:
            if node.id not in {"rerank", "fuse"}:
                node.inputs = {key: "rerank.candidates" if value == "fuse.candidates" else value for key, value in node.inputs.items()}
        edges = [Edge(source="rerank", target=edge.target, kind=edge.kind, condition=edge.condition)
                 if edge.source == "fuse" else edge for edge in edges]
        edges.append(Edge(source="fuse", target="rerank"))
    if arm == "F":
        # Routing is explicit graph data consumed by each retrieval capability.
        for node in nodes:
            if node.id == "classify":
                node.config["routing_policy"] = "lexical-identifiers@1.0.0"
            if node.id in ARMS[arm]:
                node.component = "routed." + node.component
                node.inputs["decision"] = "classify.decision"
    pipeline = pipeline.model_copy(update={"graph": pipeline.graph.model_copy(update={"nodes": nodes, "edges": edges})})
    return pipeline
