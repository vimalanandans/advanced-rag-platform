from collections.abc import Callable
from typing import Any

from rag_workbench.contracts import CapabilityManifest, ComponentManifest

ComponentExecutor = Callable[[dict[str, Any], Any, dict[str, Any]], dict[str, Any]]


class ComponentRegistry:
    """Explicit component catalog; manifests are the UI and compiler source of truth."""

    def __init__(self) -> None:
        self._components: dict[str, ComponentManifest] = {}
        self._executors: dict[str, ComponentExecutor] = {}

    def register(self, manifest: ComponentManifest, executor: ComponentExecutor) -> None:
        key = f"{manifest.id}@{manifest.version}"
        if key in self._components:
            raise ValueError(f"component already registered: {key}")
        self._components[key] = manifest
        self._executors[key] = executor

    def get(self, reference: str) -> ComponentManifest:
        try:
            return self._components[reference]
        except KeyError as error:
            raise KeyError(f"unknown component {reference}") from error

    def list(self) -> list[ComponentManifest]:
        return sorted(self._components.values(), key=lambda item: (item.category, item.id))

    def execute(self, reference: str, inputs: dict[str, Any], context: Any, config: dict[str, Any]) -> dict[str, Any]:
        return self._executors[reference](inputs, context, config)


def baseline_registry(*, dense_retriever: Any = None, generation_provider: Any = None) -> ComponentRegistry:
    from rag_workbench.components import baseline_executors

    executors = baseline_executors(dense_retriever=dense_retriever, generation_provider=generation_provider)

    registry = ComponentRegistry()
    definitions = [
        ("query.classifier", "1.0.0", "transformation", "Routes a query to retrieval lanes", {"query": "string"}, {"route": "string"}),
        ("retrieval.bm25", "1.0.0", "retrieval.lexical", "Transparent lexical retrieval", {"query": "string", "evidence": "evidence_list"}, {"candidates": "candidates"}),
        ("retrieval.dense", "1.0.0", "retrieval.dense", "Provider-neutral semantic retrieval", {"query": "string", "evidence": "evidence_list"}, {"candidates": "candidates"}),
        ("retrieval.vectorless", "1.0.0", "retrieval.vectorless", "Hierarchical tree traversal without a vector store", {"query": "string", "evidence": "evidence_list"}, {"candidates": "candidates"}),
        ("fusion.rrf", "1.0.0", "fusion", "Reciprocal rank fusion", {"candidate_lists": "candidate_lists"}, {"candidates": "candidates"}),
        ("verification.evidence", "1.0.0", "verification", "Evidence sufficiency gate", {"candidates": "candidates"}, {"sufficient": "bool"}),
        ("context.evidence_packer", "1.0.0", "context", "Token-bounded evidence packing", {"candidates": "candidates"}, {"context": "context"}),
        ("generation.local", "1.0.0", "generation", "Local evidence-constrained generation", {"question": "string", "context": "context", "sufficient": "bool", "candidates": "candidates"}, {"answer": "answer", "citations": "evidence_list", "abstained": "bool"}),
    ]
    for identifier, version, category, description, inputs, outputs in definitions:
        registry.register(ComponentManifest(
            id=identifier, version=version, category=category, description=description,
            capabilities=CapabilityManifest(category=category, suitable_query_classes=["factual"],
                suitable_content_types=["markdown", "pdf"], metrics=["latency_ms", "token_usage"]),
            input_types=inputs, output_types=outputs,
            telemetry_events=["component.started", "component.completed"],
        ), executors[f"{identifier}@{version}"])
    return registry
