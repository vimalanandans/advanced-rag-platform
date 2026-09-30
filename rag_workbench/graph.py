"""Pipeline parsing, validation, compilation, and immutable graph fingerprints."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

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
    graph["schema_version"] = payload.pop("graph_schema_version", "1.0.0")
    graph["outputs"] = payload.pop("outputs", {})
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
        try:
            Draft202012Validator.check_schema(manifest.config_schema)
        except SchemaError as error:
            raise GraphValidationError(f"component {node.component} has an invalid configuration schema") from error
        if any(Draft202012Validator(manifest.config_schema).iter_errors(node.config)):
            raise GraphValidationError(f"node {node.id} configuration violates its component schema")
        if set(node.inputs) != set(manifest.input_types):
            raise GraphValidationError(f"node {node.id} inputs must match component contract")
        if set(node.outputs) != set(manifest.output_types):
            raise GraphValidationError(f"node {node.id} outputs must match component contract")
        if node.outputs != manifest.output_types:
            raise GraphValidationError(f"node {node.id} output types must match component contract")

    loop_nodes = {node_id for loop in pipeline.graph.loops for node_id in loop.nodes}
    if sum(len(loop.nodes) for loop in pipeline.graph.loops) != len(loop_nodes):
        raise GraphValidationError("loop nodes must be unique and cannot overlap loops")
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
        if edge.kind == EdgeKind.FEEDBACK and not any(
            {edge.source, edge.target} <= set(loop.nodes) for loop in pipeline.graph.loops
        ):
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
    _validate_terminal_outputs(pipeline, manifests)
    for loop in pipeline.graph.loops:
        if loop.nodes != [node_id for node_id in order if node_id in loop.nodes]:
            raise GraphValidationError(f"loop {loop.id} nodes must follow graph execution order")
        for edge in pipeline.graph.edges:
            if edge.source in loop.nodes and edge.target not in loop.nodes and order.index(edge.target) < order.index(loop.nodes[-1]):
                raise GraphValidationError(f"loop {loop.id} must finish before downstream nodes execute")
    serialized = json.dumps(pipeline_snapshot(pipeline), sort_keys=True, separators=(",", ":"))
    return ExecutionPlan(pipeline=pipeline, fingerprint=hashlib.sha256(serialized.encode()).hexdigest(), order=tuple(order))


def pipeline_snapshot(pipeline: Pipeline) -> dict:
    """Retain the historical v1 canonical representation and fingerprints."""
    snapshot = pipeline.model_dump(mode="json")
    if pipeline.graph.schema_version == "1.0.0":
        snapshot["graph"].pop("schema_version")
        snapshot["graph"].pop("outputs")
    return snapshot


def _validate_terminal_outputs(pipeline: Pipeline, manifests: dict) -> None:
    bindings = pipeline.graph.outputs
    if pipeline.graph.schema_version == "1.0.0":
        if bindings:
            raise GraphValidationError("explicit terminal outputs require graph schema 2.0.0")
        return
    required = {"answer": "answer", "citations": "evidence_list", "abstained": "bool"}
    allowed = {**required, "context": "context", "claims": "claim_support"}
    if not set(required) <= set(bindings) or not set(bindings) <= set(allowed):
        raise GraphValidationError("v2 terminal outputs require answer, citations and abstained; context is optional")
    for name, binding in bindings.items():
        try:
            node, port = binding.split(".", 1)
            actual = manifests[node].output_types[port]
        except (ValueError, KeyError) as error:
            raise GraphValidationError(f"invalid terminal binding {name}") from error
        if actual != allowed[name]:
            raise GraphValidationError(f"terminal binding {name} must produce {allowed[name]}")


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
