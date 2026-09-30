"""Provider-neutral, versioned contracts used by the control and execution planes."""

from __future__ import annotations

from enum import Enum
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EdgeKind(str, Enum):
    DATA = "data"
    CONTROL = "control"
    CONDITIONAL = "conditional"
    ERROR = "error"
    FEEDBACK = "feedback"


class Budget(BaseModel):
    max_total_tokens: int = Field(default=30_000, gt=0)
    max_context_tokens: int = Field(default=12_000, gt=0)
    max_output_tokens: int = Field(default=3_000, gt=0)
    max_latency_ms: int = Field(default=15_000, gt=0)
    max_tool_calls: int = Field(default=0, ge=0)
    max_iterations: int = Field(default=1, gt=0)


class Node(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    component: str
    config: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, str | list[str]] = Field(default_factory=dict)
    outputs: dict[str, str] = Field(default_factory=dict)


class Edge(BaseModel):
    source: str
    target: str
    kind: EdgeKind = EdgeKind.DATA
    condition: str | None = None


class Loop(BaseModel):
    id: str
    nodes: list[str]
    exit_when: str
    budget: Budget = Field(default_factory=lambda: Budget(max_iterations=2, max_total_tokens=6_000))
    fallback: Literal["abstain", "fail"] = "abstain"


class PipelineGraph(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: Literal["1.0.0", "2.0.0"] = "1.0.0"
    nodes: list[Node]
    edges: list[Edge]
    loops: list[Loop] = Field(default_factory=list)
    outputs: dict[str, str] = Field(default_factory=dict)


class Pipeline(BaseModel):
    id: str
    version: str
    tenant_id: str = "local"
    description: str = ""
    budgets: Budget = Field(default_factory=Budget)
    graph: PipelineGraph

    @model_validator(mode="after")
    def version_is_semantic(self) -> "Pipeline":
        if len(self.version.split(".")) != 3 or not all(part.isdigit() for part in self.version.split(".")):
            raise ValueError("pipeline version must be semantic major.minor.patch")
        return self


class CapabilityManifest(BaseModel):
    category: str
    suitable_query_classes: list[str] = Field(default_factory=list)
    suitable_content_types: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    local_supported: bool = True
    cloud_supported: bool = True


class ComponentManifest(BaseModel):
    id: str
    version: str
    category: str
    description: str
    capabilities: CapabilityManifest
    config_schema: dict[str, Any] = Field(default_factory=dict)
    input_types: dict[str, str] = Field(default_factory=dict)
    output_types: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    concurrency: Literal["serial", "parallel-safe"] = "serial"
    telemetry_events: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    id: str
    document_id: str
    source_uri: str
    revision: str
    content: str
    title: str
    locator: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    approval_state: Literal["approved", "review_required", "rejected"] = "approved"
    tenant_id: str = "local"
    allowed_users: list[str] = Field(default_factory=lambda: ["local-admin"])
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    applicability_tags: list[str] = Field(default_factory=list)


class RequestContext(BaseModel):
    """Authenticated request scope; authorization is evaluated before retrieval."""

    tenant_id: str
    user_id: str
    allowed_corpora: list[str] = Field(default_factory=list)
    allowed_revisions: dict[str, str] = Field(default_factory=dict)
    applicability_tags: list[str] = Field(default_factory=list)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RetrievalCandidate(BaseModel):
    evidence: Evidence
    lane: str
    score: float
    rank: int = 0


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    context_tokens: int = 0
    retrieval_reasoning_tokens: int = 0


class ContextPlan(BaseModel):
    included: list[str] = Field(default_factory=list)
    omitted: list[str] = Field(default_factory=list)
    truncated: list[str] = Field(default_factory=list)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)


class NodeExecution(BaseModel):
    node_id: str
    component: str
    status: Literal["completed", "failed", "skipped", "retrying"]
    duration_ms: int
    input_metadata: dict[str, Any] = Field(default_factory=dict)
    output_metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    iteration: int = 0


class RunManifest(BaseModel):
    schema_version: str = "1.1.0"
    run_id: str
    trace_id: str
    tenant_id: str
    user_id: str = "local-admin"
    pipeline_id: str
    pipeline_version: str
    graph_fingerprint: str
    component_versions: dict[str, str]
    model_version: str
    index_revisions: dict[str, str] = Field(default_factory=dict)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    node_executions: list[NodeExecution] = Field(default_factory=list)
    status: Literal["completed", "failed"] = "completed"
    error: str | None = None
    loop_outcomes: list[dict[str, Any]] = Field(default_factory=list)
    embedding_identity: dict[str, Any] = Field(default_factory=dict)
    retrieval_candidates: list[dict[str, Any]] = Field(default_factory=list)


class RunResult(BaseModel):
    manifest: RunManifest
    answer: str
    citations: list[Evidence] = Field(default_factory=list)
    abstained: bool = False
    context: ContextPlan = Field(default_factory=ContextPlan)


class EvaluationCase(BaseModel):
    id: str
    question: str
    expected_evidence_ids: list[str]
    expect_abstention: bool = False


class EvaluationResult(BaseModel):
    pipeline_fingerprint: str
    passed: int
    failed: int
    cases: list[dict[str, Any]]
