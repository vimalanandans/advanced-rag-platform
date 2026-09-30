"""Bounded, contract-driven local execution of compiled PipelineGraph plans."""

from __future__ import annotations

import time
import uuid
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rag_workbench.contracts import Budget, ContextPlan, Evidence, NodeExecution, Pipeline, RequestContext, RetrievalCandidate, RunManifest, RunResult, TokenUsage
from rag_workbench.graph import ExecutionPlan, compile_pipeline
from rag_workbench.observability import LocalTraceStore, TraceStore
from rag_workbench.providers import LocalProviderProfile, OllamaModelProvider, QdrantVectorIndex, provider_profile_from_environment
from rag_workbench.retrieval import IndexedDenseRetriever
from rag_workbench.registry import ComponentRegistry, baseline_registry


class BudgetExceeded(RuntimeError):
    pass


class AuthorizationError(PermissionError):
    pass


@dataclass
class ExecutionContext:
    request: RequestContext
    budget: Budget
    started_at: float = field(default_factory=time.monotonic)
    usage: TokenUsage = field(default_factory=TokenUsage)
    tool_calls: int = 0
    iterations: int = 0
    loop_outcomes: list[dict[str, Any]] = field(default_factory=list)
    forced_abstention: bool = False
    retrieval_candidates: list[dict[str, Any]] = field(default_factory=list)

    def assert_within_deadline(self) -> None:
        if (time.monotonic() - self.started_at) * 1000 > self.budget.max_latency_ms:
            raise BudgetExceeded("pipeline latency budget exceeded")

    def consume_context(self, amount: int) -> None:
        self.usage.context_tokens += amount
        self.usage.input_tokens += amount
        if self.usage.context_tokens > self.budget.max_context_tokens:
            raise BudgetExceeded("context token budget exceeded")
        self._assert_total()

    def consume_output(self, amount: int) -> None:
        self.usage.output_tokens += amount
        if self.usage.output_tokens > self.budget.max_output_tokens:
            raise BudgetExceeded("output token budget exceeded")
        self._assert_total()

    def consume_retrieval_reasoning(self, amount: int) -> None:
        self.usage.retrieval_reasoning_tokens += amount
        self._assert_total()

    def record_tool_call(self) -> None:
        self.tool_calls += 1
        if self.tool_calls > self.budget.max_tool_calls:
            raise BudgetExceeded("tool-call budget exceeded")

    def record_iteration(self) -> None:
        self.iterations += 1
        if self.iterations > self.budget.max_iterations:
            raise BudgetExceeded("iteration budget exceeded")

    def _assert_total(self) -> None:
        if self.usage.input_tokens + self.usage.output_tokens + self.usage.retrieval_reasoning_tokens > self.budget.max_total_tokens:
            raise BudgetExceeded("total token budget exceeded")


class WorkbenchRuntime:
    def __init__(self, registry: ComponentRegistry | None = None, trace_store: TraceStore | None = None, model_version: str = "deterministic-local-generator@1.0.0", *, embedding_identity: dict[str, Any] | None = None, index_revisions: dict[str, str] | None = None) -> None:
        self.registry = registry or baseline_registry()
        self.trace_store = trace_store or LocalTraceStore()
        self.model_version = model_version
        self.evidence: list[Evidence] = []
        self.embedding_identity = embedding_identity or {}
        self.index_revisions = index_revisions or {}

    def set_evidence(self, evidence: list[Evidence]) -> None:
        self.evidence = evidence

    def compile(self, pipeline: Pipeline) -> ExecutionPlan:
        return compile_pipeline(pipeline, self.registry)

    def run(self, plan: ExecutionPlan, question: str, request: RequestContext | None = None) -> RunResult:
        request = request or RequestContext(tenant_id=plan.pipeline.tenant_id, user_id="local-admin")
        context = ExecutionContext(request=request, budget=plan.pipeline.budgets)
        state: dict[str, Any] = {"$query": question}
        run_id, trace_id = str(uuid.uuid4()), str(uuid.uuid4())
        executions: list[NodeExecution] = []
        failure: Exception | None = None

        try:
            if request.tenant_id != plan.pipeline.tenant_id:
                raise AuthorizationError("request tenant is not authorized for this pipeline")
            state["$evidence"] = self._authorized_evidence(request)
            loop_ends = {loop.nodes[-1]: loop for loop in plan.pipeline.graph.loops}
            for node_id in plan.order:
                if self._should_execute(plan, node_id, state):
                    self._execute_node(plan, node_id, state, context, executions)
                else:
                    node = next(item for item in plan.pipeline.graph.nodes if item.id == node_id)
                    executions.append(NodeExecution(node_id=node.id, component=node.component, status="skipped", duration_ms=0, output_metadata={"reason": "conditional edge not selected"}))
                if node_id in loop_ends:
                    self._execute_loop(plan, loop_ends[node_id], state, context, executions)
                if context.forced_abstention:
                    break
            if context.forced_abstention:
                generated = {"answer": "I cannot answer because the retrieval loop exhausted its bounds.", "citations": [], "abstained": True}
                context_plan = ContextPlan()
            elif plan.pipeline.graph.schema_version == "2.0.0":
                generated = {name: self._resolve_binding(binding, state) for name, binding in plan.pipeline.graph.outputs.items()}
                context_plan = generated.get("context", ContextPlan())
            else:
                generated = state.get("generate", {})
                context_plan = state.get("context", {}).get("context", ContextPlan())
            return RunResult(
                manifest=self._manifest(plan, run_id, trace_id, request, context, executions, "completed", None),
                answer=generated.get("answer", "I cannot answer from the approved evidence available."),
                citations=generated.get("citations", []), abstained=generated.get("abstained", True),
                context=context_plan,
            )
        except Exception as error:
            failure = error
            raise
        finally:
            self.trace_store.save(self._manifest(plan, run_id, trace_id, request, context, executions, "failed" if failure else "completed", _safe_error(failure) if failure else None))

    def _execute_node(self, plan: ExecutionPlan, node_id: str, state: dict[str, Any], context: ExecutionContext, executions: list[NodeExecution], iteration: int = 0) -> None:
        node = next(item for item in plan.pipeline.graph.nodes if item.id == node_id)
        started = time.monotonic()
        try:
            context.assert_within_deadline()
            inputs = {key: self._resolve_binding(value, state) for key, value in node.inputs.items()}
            outputs = self.registry.execute(node.component, inputs, context, node.config)
            if set(outputs) != set(node.outputs):
                raise ValueError(f"component {node.component} returned outputs outside its contract")
            self._validate_output_values(node.outputs, outputs)
            for port, kind in node.outputs.items():
                if kind == "candidates":
                    context.retrieval_candidates.append({"node_id": node.id, "iteration": iteration, "candidates": [{"evidence_id": item.evidence.id, "revision": item.evidence.revision, "lane": item.lane, "rank": item.rank, "score": item.score} for item in outputs[port]]})
            self._account_outputs(outputs, context)
            context.assert_within_deadline()
            state[node.id] = outputs
            executions.append(NodeExecution(node_id=node.id, component=node.component, status="completed", duration_ms=int((time.monotonic() - started) * 1000), input_metadata=_metadata(inputs), output_metadata=_metadata(outputs), iteration=iteration))
        except Exception as error:
            executions.append(NodeExecution(node_id=node.id, component=node.component, status="failed", duration_ms=int((time.monotonic() - started) * 1000), error=_safe_error(error), iteration=iteration))
            raise

    @staticmethod
    def _validate_output_values(contract: dict[str, str], outputs: dict[str, Any]) -> None:
        expected_python_types = {"string": str, "answer": str, "bool": bool, "candidates": list, "evidence_list": list, "context": ContextPlan}
        for name, type_name in contract.items():
            expected = expected_python_types.get(type_name)
            if expected and not isinstance(outputs[name], expected):
                raise TypeError(f"component output {name} must be {type_name}")
            element_type = {"candidates": RetrievalCandidate, "evidence_list": Evidence}.get(type_name)
            if element_type and any(not isinstance(item, element_type) for item in outputs[name]):
                raise TypeError(f"component output {name} contains invalid {type_name} elements")

    @staticmethod
    def _account_outputs(outputs: dict[str, Any], context: ExecutionContext) -> None:
        """Enforce budgets at the registry boundary so custom components cannot bypass them."""
        context_value = outputs.get("context")
        if isinstance(context_value, ContextPlan):
            context.consume_context(context_value.token_usage.context_tokens)
        answer = outputs.get("answer")
        if isinstance(answer, str):
            context.consume_output(len(answer.split()))

    def _execute_loop(self, plan: ExecutionPlan, loop: Any, state: dict[str, Any], context: ExecutionContext, executions: list[NodeExecution]) -> None:
        started, initial_usage, initial_tools = time.monotonic(), context.usage.model_copy(deep=True), context.tool_calls
        for iteration in range(1, loop.budget.max_iterations + 1):
            if self._exit_condition(loop.exit_when, state):
                context.loop_outcomes.append({"loop_id": loop.id, "status": "exited", "iterations": iteration - 1})
                return
            context.record_iteration()
            for node_id in loop.nodes:
                if self._should_execute(plan, node_id, state):
                    self._execute_node(plan, node_id, state, context, executions, iteration)
                else:
                    state.pop(node_id, None)
                    node = next(item for item in plan.pipeline.graph.nodes if item.id == node_id)
                    executions.append(NodeExecution(node_id=node.id, component=node.component, status="skipped", duration_ms=0, iteration=iteration, output_metadata={"reason": "conditional edge not selected"}))
                self._assert_loop_budget(loop, started, initial_usage, initial_tools, context)
            if self._exit_condition(loop.exit_when, state):
                context.loop_outcomes.append({"loop_id": loop.id, "status": "exited", "iterations": iteration})
                return
        context.loop_outcomes.append({"loop_id": loop.id, "status": "exhausted", "iterations": loop.budget.max_iterations, "fallback": loop.fallback})
        if loop.fallback == "fail":
            raise BudgetExceeded(f"loop {loop.id} exhausted without exit condition")
        context.forced_abstention = True

    @staticmethod
    def _assert_loop_budget(loop: Any, started: float, initial_usage: TokenUsage, initial_tools: int, context: ExecutionContext) -> None:
        if (time.monotonic() - started) * 1000 > loop.budget.max_latency_ms:
            raise BudgetExceeded(f"loop {loop.id} latency budget exceeded")
        consumed = context.usage.input_tokens + context.usage.output_tokens + context.usage.retrieval_reasoning_tokens - initial_usage.input_tokens - initial_usage.output_tokens - initial_usage.retrieval_reasoning_tokens
        if consumed > loop.budget.max_total_tokens or context.usage.context_tokens - initial_usage.context_tokens > loop.budget.max_context_tokens or context.usage.output_tokens - initial_usage.output_tokens > loop.budget.max_output_tokens or context.tool_calls - initial_tools > loop.budget.max_tool_calls:
            raise BudgetExceeded(f"loop {loop.id} budget exceeded")

    @staticmethod
    def _exit_condition(expression: str, state: dict[str, Any]) -> bool:
        reference, expected = [item.strip() for item in expression.split("==", 1)]
        node_id, output = reference.split(".", 1)
        return state.get(node_id, {}).get(output) is (expected == "true")

    @staticmethod
    def _should_execute(plan: ExecutionPlan, node_id: str, state: dict[str, Any]) -> bool:
        conditions = [edge.condition for edge in plan.pipeline.graph.edges if edge.target == node_id and edge.kind.value == "conditional"]
        return not conditions or any(WorkbenchRuntime._condition_matches(condition or "", state) for condition in conditions)

    @staticmethod
    def _condition_matches(expression: str, state: dict[str, Any]) -> bool:
        reference, expected = [item.strip() for item in expression.split("==", 1)]
        node_id, output = reference.split(".", 1)
        actual = state.get(node_id, {}).get(output)
        expected_value: Any = expected == "true" if expected in {"true", "false"} else expected.strip("'")
        return actual == expected_value

    @staticmethod
    def _resolve_binding(binding: str | list[str], state: dict[str, Any]) -> Any:
        if isinstance(binding, list):
            return [WorkbenchRuntime._resolve_binding(item, state) for item in binding]
        if binding.startswith("$"):
            return state[binding]
        node_id, output = binding.split(".", 1)
        return state[node_id][output]

    def _authorized_evidence(self, request: RequestContext) -> list[Evidence]:
        permitted = []
        for item in self.evidence:
            corpus_id = str(item.metadata.get("corpus_id", ""))
            if item.approval_state != "approved" or item.tenant_id != request.tenant_id or request.user_id not in item.allowed_users:
                continue
            if request.allowed_corpora and corpus_id not in request.allowed_corpora:
                continue
            if request.allowed_revisions.get(item.document_id) not in {None, item.revision}:
                continue
            if (item.valid_from and request.requested_at < item.valid_from) or (item.valid_until and request.requested_at > item.valid_until):
                continue
            if item.applicability_tags and not set(item.applicability_tags).intersection(request.applicability_tags):
                continue
            permitted.append(item)
        return permitted

    def _manifest(self, plan: ExecutionPlan, run_id: str, trace_id: str, request: RequestContext, context: ExecutionContext, executions: list[NodeExecution], status: str, error: str | None) -> RunManifest:
        return RunManifest(
            run_id=run_id, trace_id=trace_id, tenant_id=request.tenant_id, user_id=request.user_id,
            pipeline_id=plan.pipeline.id, pipeline_version=plan.pipeline.version, graph_fingerprint=plan.fingerprint,
            component_versions={node.component.split("@")[0]: node.component.split("@")[1] for node in plan.pipeline.graph.nodes},
            model_version=self.model_version, index_revisions={**self.index_revisions, "corpus": hashlib.sha256(json.dumps(sorted([item.model_dump(mode="json", exclude={"source_uri"}) for item in self.evidence], key=lambda item: item["id"]), sort_keys=True, separators=(",", ":")).encode()).hexdigest()},
            token_usage=context.usage, node_executions=executions, status=status, error=error,
            loop_outcomes=context.loop_outcomes,
            embedding_identity=self.embedding_identity,
            retrieval_candidates=context.retrieval_candidates,
        )


def _metadata(values: dict[str, Any]) -> dict[str, Any]:
    """Safe trace metadata: counts/types, never raw document content or secrets."""
    return {key: (len(value) if isinstance(value, (list, dict, str)) else type(value).__name__) for key, value in values.items()}


def _safe_error(error: Exception) -> str:
    """Exception messages may contain URLs, credentials or source content."""
    descriptions = {BudgetExceeded: "execution budget exceeded", AuthorizationError: "request scope denied", PermissionError: "evidence scope denied", TypeError: "component contract invalid"}
    return f"{type(error).__name__}: {descriptions.get(type(error), 'execution failed')}"


def demo_runtime(trace_store: TraceStore | None = None, provider_profile: LocalProviderProfile | None = None) -> WorkbenchRuntime:
    from rag_workbench.ingestion import ingest_path

    if provider_profile is None:
        import os
        profile_name = os.environ.get("RAG_WORKBENCH_PROFILE", "deterministic")
        if profile_name == "local-real":
            from rag_workbench.local_real import local_real_runtime
            return local_real_runtime(trace_store=trace_store)
        if profile_name != "deterministic":
            raise ValueError("RAG_WORKBENCH_PROFILE must be deterministic or local-real")

    profile = provider_profile or provider_profile_from_environment()
    dense_retriever = (
        IndexedDenseRetriever(QdrantVectorIndex(profile.qdrant_url, profile.qdrant_collection))
        if profile.dense_mode == "qdrant"
        else None
    )
    generation_provider = (
        OllamaModelProvider(profile.ollama_url, profile.ollama_model)
        if profile.generation_mode == "ollama"
        else None
    )
    runtime = WorkbenchRuntime(
        registry=baseline_registry(dense_retriever=dense_retriever, generation_provider=generation_provider),
        trace_store=trace_store,
        model_version=profile.model_version,
    )
    fixture = Path(__file__).parent.parent / "data" / "fixtures" / "rag_basics.md"
    if fixture.exists():
        runtime.set_evidence(ingest_path(fixture))
    return runtime
