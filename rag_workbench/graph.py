"""Pipeline parsing, validation, compilation, and immutable graph fingerprints."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass

import yaml

from rag_workbench.contracts import EdgeKind, Pipeline
from rag_workbench.registry import ComponentRegistry


class GraphValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ExecutionPlan:
    pipeline: Pipeline
    fingerprint: str
    order: tuple[str, ...]


def pipeline_from_yaml(raw: str) -> Pipeline:
    payload = yaml.safe_load(raw)
    if "pipeline" in payload:
        payload = payload["pipeline"]
    graph = {"nodes": payload.pop("nodes", []), "edges": _parse_edges(payload.pop("edges", [])), "loops": payload.pop("loops", [])}
    return Pipeline(**payload, graph=graph)


def _parse_edges(edges: list[object]) -> list[dict[str, str]]:
    parsed: list[dict[str, str]] = []
    for edge in edges:
        if isinstance(edge, str):
            source, target = [part.strip() for part in edge.split("->", 1)]
            parsed.append({"source": source, "target": target})
        elif isinstance(edge, dict):
            parsed.append(edge)
        else:
            raise GraphValidationError("edges must be strings or maps")
    return parsed


def compile_pipeline(pipeline: Pipeline, registry: ComponentRegistry) -> ExecutionPlan:
    nodes = {node.id: node for node in pipeline.graph.nodes}
    if len(nodes) != len(pipeline.graph.nodes):
        raise GraphValidationError("node IDs must be unique")
    manifests = {}
    for node in nodes.values():
        try:
            manifests[node.id] = registry.get(node.component)
        except KeyError as error:
            raise GraphValidationError(str(error)) from error
        manifest = manifests[node.id]
        if set(node.inputs) != set(manifest.input_types):
            raise GraphValidationError(f"node {node.id} inputs must match component contract")
        if set(node.outputs) != set(manifest.output_types):
            raise GraphValidationError(f"node {node.id} outputs must match component contract")
        if node.outputs != manifest.output_types:
            raise GraphValidationError(f"node {node.id} output types must match component contract")

    loop_nodes = {node_id for loop in pipeline.graph.loops for node_id in loop.nodes}
    loop_ids = [loop.id for loop in pipeline.graph.loops]
    if len(loop_ids) != len(set(loop_ids)):
        raise GraphValidationError("loop IDs must be unique")
    if sum(loop.budget.max_iterations for loop in pipeline.graph.loops) > pipeline.budgets.max_iterations:
        raise GraphValidationError("declared loop iterations exceed pipeline iteration budget")
    for loop in pipeline.graph.loops:
        if not loop.nodes or not set(loop.nodes).issubset(nodes):
            raise GraphValidationError(f"loop {loop.id} references an unknown node")
        if loop.budget.max_iterations > pipeline.budgets.max_iterations:
            raise GraphValidationError(f"loop {loop.id} exceeds pipeline iteration budget")
        if any(getattr(loop.budget, field) > getattr(pipeline.budgets, field) for field in ("max_total_tokens", "max_context_tokens", "max_output_tokens", "max_latency_ms", "max_tool_calls", "max_iterations")):
            raise GraphValidationError(f"loop {loop.id} exceeds pipeline budget")
        if not re.fullmatch(r"[a-z][a-z0-9_-]*\.[a-z][a-z0-9_-]*\s*==\s*(true|false)", loop.exit_when):
            raise GraphValidationError(f"loop {loop.id} exit_when must compare a boolean node output")
        exit_node, exit_output = loop.exit_when.split("==", 1)[0].strip().split(".", 1)
        if exit_node not in loop.nodes or manifests[exit_node].output_types.get(exit_output) != "bool":
            raise GraphValidationError(f"loop {loop.id} exit_when must reference a boolean output in the loop")
        if not any(edge.kind == EdgeKind.FEEDBACK and edge.source in loop.nodes and edge.target in loop.nodes for edge in pipeline.graph.edges):
            raise GraphValidationError(f"loop {loop.id} requires an internal feedback edge")

    adjacency: dict[str, list[str]] = defaultdict(list)
    indegree: dict[str, int] = {node_id: 0 for node_id in nodes}
    for edge in pipeline.graph.edges:
        if edge.source not in nodes or edge.target not in nodes:
            raise GraphValidationError(f"edge {edge.source}->{edge.target} references an unknown node")
        if edge.kind == EdgeKind.FEEDBACK and not ({edge.source, edge.target} <= loop_nodes):
            raise GraphValidationError("feedback edges are permitted only in declared loops")
        if edge.kind == EdgeKind.CONDITIONAL and not edge.condition:
            raise GraphValidationError("conditional edges require a condition")
        if edge.kind == EdgeKind.CONDITIONAL and not re.fullmatch(r"[a-z][a-z0-9_-]*\.[a-z][a-z0-9_-]*\s*==\s*(true|false|'[^']*')", edge.condition or ""):
            raise GraphValidationError("conditional edge condition must compare a node output")
        if edge.kind == EdgeKind.CONDITIONAL:
            condition_source, condition_output = (edge.condition or "").split("==", 1)[0].strip().split(".", 1)
            if condition_source != edge.source or condition_output not in manifests[edge.source].output_types:
                raise GraphValidationError("conditional edge must inspect an output from its source node")
        if edge.kind != EdgeKind.FEEDBACK:
            adjacency[edge.source].append(edge.target)
            indegree[edge.target] += 1

    ready = sorted(node_id for node_id, count in indegree.items() if count == 0)
    order: list[str] = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for target in adjacency[current]:
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
                ready.sort()
    if len(order) != len(nodes):
        raise GraphValidationError("graph must be a DAG outside declared feedback loops")
    _validate_bindings(pipeline, manifests)
    serialized = json.dumps(pipeline.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return ExecutionPlan(pipeline=pipeline, fingerprint=hashlib.sha256(serialized.encode()).hexdigest(), order=tuple(order))


def _validate_bindings(pipeline: Pipeline, manifests: dict) -> None:
    nodes = {node.id: node for node in pipeline.graph.nodes}
    edge_pairs = {(edge.source, edge.target) for edge in pipeline.graph.edges if edge.kind != EdgeKind.FEEDBACK}
    root_types = {"$query": "string", "$evidence": "evidence_list"}
    for node in nodes.values():
        for input_name, binding in node.inputs.items():
            values = binding if isinstance(binding, list) else [binding]
            expected = manifests[node.id].input_types[input_name]
            if expected == "candidate_lists" and not isinstance(binding, list):
                raise GraphValidationError(f"node {node.id} input {input_name} requires a list of candidate bindings")
            for value in values:
                if value in root_types:
                    actual = root_types[value]
                else:
                    try:
                        source, output = value.split(".", 1)
                        actual = manifests[source].output_types[output]
                    except (KeyError, ValueError) as error:
                        raise GraphValidationError(f"node {node.id} has invalid binding {value}") from error
                    if (source, node.id) not in edge_pairs:
                        raise GraphValidationError(f"node {node.id} binding {value} lacks an explicit graph edge")
                if expected != "candidate_lists" and actual != expected:
                    raise GraphValidationError(f"node {node.id} input {input_name} expects {expected}, got {actual}")
                if expected == "candidate_lists" and actual != "candidates":
                    raise GraphValidationError(f"node {node.id} candidate list binding must produce candidates")
