"""Versioned experiment contracts and deterministic ranking measurements.

These contracts do not grant evidence access or orchestrate pipeline components.
The runner receives a compiled graph and uses the existing runtime boundary.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from rag_workbench.contracts import ComponentManifest, Evidence, RequestContext
from rag_workbench.graph import ExecutionPlan
from rag_workbench.runtime import WorkbenchRuntime

VERSION = r"^\d+\.\d+\.\d+$"
SAFE_ID = r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$"
QueryClass = Literal[
    "exact_identifier", "exact_phrase", "semantic", "comparison", "procedure",
    "table", "visual", "temporal", "multi_hop", "relationship", "conversational",
    "no_rag_required",
]
Split = Literal["development", "tuning", "held_out", "adversarial", "regression"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = Field(default="1.0.0", pattern=VERSION)


class ExperimentCase(Contract):
    case_id: str = Field(pattern=SAFE_ID)
    query: str = Field(min_length=1)
    query_class: QueryClass
    corpus_revision: str = Field(min_length=1)
    source_group: str = Field(min_length=1)
    split: Split
    expected_evidence_ids: list[str] = Field(default_factory=list)
    hard_negative_ids: list[str] = Field(default_factory=list)
    expected_claims: list[str] = Field(default_factory=list)
    expected_abstention: bool = False
    relevance: dict[str, int] = Field(default_factory=dict)
    policy_constraints: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""

    @model_validator(mode="after")
    def validate_labels(self) -> ExperimentCase:
        expected, negatives = set(self.expected_evidence_ids), set(self.hard_negative_ids)
        if len(expected) != len(self.expected_evidence_ids) or len(negatives) != len(self.hard_negative_ids):
            raise ValueError("evidence labels must be unique")
        if expected & negatives:
            raise ValueError("expected evidence cannot also be a hard negative")
        if self.expected_abstention and (expected or self.expected_claims):
            raise ValueError("abstention case cannot require evidence or answer claims")
        if any(grade < 0 for grade in self.relevance.values()):
            raise ValueError("relevance grades must be nonnegative")
        if self.relevance and {key for key, grade in self.relevance.items() if grade > 0} != expected:
            raise ValueError("positive relevance labels must match expected evidence")
        return self


class DatasetManifest(Contract):
    dataset_id: str = Field(pattern=SAFE_ID)
    version: str = Field(pattern=VERSION)
    corpus_revision: str = Field(min_length=1)
    provenance: str = Field(min_length=1)
    license: str = Field(min_length=1)
    cases: list[ExperimentCase] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_splits(self) -> DatasetManifest:
        ids: set[str] = set()
        groups: dict[str, str] = {}
        queries: dict[str, str] = {}
        for case in self.cases:
            if case.case_id in ids:
                raise ValueError("duplicate case ID")
            ids.add(case.case_id)
            if case.corpus_revision != self.corpus_revision:
                raise ValueError("case corpus revision differs from dataset")
            normalized = " ".join(case.query.casefold().split())
            for key, seen in ((case.source_group, groups), (normalized, queries)):
                if key in seen and seen[key] != case.split:
                    raise ValueError("source group or query leaks across dataset splits")
                seen[key] = case.split
        return self

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.model_dump(mode="json"))


class StrategyManifest(Contract):
    strategy_id: str = Field(pattern=SAFE_ID)
    version: str = Field(pattern=VERSION)
    graph_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    supported_query_classes: list[QueryClass] = Field(min_length=1)
    supported_content_classes: list[str] = Field(min_length=1)
    required_components: list[str] = Field(min_length=1)
    required_models: list[str] = Field(default_factory=list)
    required_indexes: list[str] = Field(default_factory=list)
    latency_expectations: dict[str, Any]
    resource_requirements: dict[str, Any]
    known_limitations: list[str]
    evaluation_dataset: str = Field(min_length=1)
    promotion_status: Literal["experimental", "evaluated", "accepted", "rejected", "superseded"] = "experimental"


class RankingMetrics(Contract):
    k: int = Field(gt=0)
    recall_at_k: float | None
    precision_at_k: float
    mrr: float | None
    ndcg_at_k: float | None
    hard_negative_hits: int
    relevant_count: int
    retrieved_count: int
    unavailable_reason: str | None = None


def ranking_metrics(ranked_ids: list[str], case: ExperimentCase, k: int = 5) -> RankingMetrics:
    """Measure unique ranked evidence; undefined relevance metrics stay null."""
    if k <= 0:
        raise ValueError("k must be positive")
    ranked = list(dict.fromkeys(ranked_ids))[:k]
    expected = set(case.expected_evidence_ids)
    hits = [index for index, item in enumerate(ranked, 1) if item in expected]
    grades = case.relevance or {item: 1 for item in expected}
    dcg = sum((2 ** grades.get(item, 0) - 1) / math.log2(index + 1) for index, item in enumerate(ranked, 1))
    ideal = sum((2 ** grade - 1) / math.log2(index + 1) for index, grade in enumerate(sorted(grades.values(), reverse=True)[:k], 1))
    return RankingMetrics(
        k=k, recall_at_k=len(hits) / len(expected) if expected else None,
        precision_at_k=len(hits) / k, mrr=1 / hits[0] if hits else (0.0 if expected else None),
        ndcg_at_k=dcg / ideal if ideal else None,
        hard_negative_hits=len(set(ranked) & set(case.hard_negative_ids)),
        relevant_count=len(expected), retrieved_count=len(ranked),
        unavailable_reason=None if expected else "no expected relevant evidence",
    )


class ExperimentRecord(Contract):
    experiment_id: str = Field(pattern=SAFE_ID)
    run_id: str = Field(pattern=SAFE_ID)
    hypothesis: str = Field(min_length=1)
    baseline: str = Field(min_length=1)
    candidate_strategy: StrategyManifest
    dataset_snapshot: dict[str, Any] = Field(default_factory=dict)
    configuration_snapshot: dict[str, Any] = Field(default_factory=dict)
    pipeline_snapshot: dict[str, Any] = Field(default_factory=dict)
    dataset_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    config_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    split: Split
    status: Literal["completed", "failed"]
    case_results: list[dict[str, Any]]
    metrics: dict[str, Any]
    failures: list[str]
    decision: Literal["accept", "reject", "iterate"]
    notes: str

    @model_validator(mode="after")
    def validate_decision(self) -> ExperimentRecord:
        if self.dataset_snapshot and fingerprint(self.dataset_snapshot) != self.dataset_fingerprint:
            raise ValueError("dataset snapshot fingerprint mismatch")
        if self.configuration_snapshot and fingerprint(self.configuration_snapshot) != self.config_fingerprint:
            raise ValueError("configuration snapshot fingerprint mismatch")
        if self.pipeline_snapshot and fingerprint(self.pipeline_snapshot) != self.candidate_strategy.graph_fingerprint:
            raise ValueError("pipeline snapshot fingerprint mismatch")
        if self.decision == "accept" and (self.status != "completed" or self.failures):
            raise ValueError("failed experiments cannot be accepted")
        return self


def fingerprint(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def write_record(directory: Path, record: ExperimentRecord) -> Path:
    """Publish a complete record without replacing any earlier run.

    A same-directory temporary file is linked atomically to a new immutable name.
    Only safe IDs are accepted by the contract; file permissions are owner-only.
    """
    import os
    import tempfile

    # Revalidate mutable nested objects at the publication boundary.
    record = ExperimentRecord.model_validate(record.model_dump(mode="json"))
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{record.experiment_id}--{record.run_id}.json"
    fd, temporary = tempfile.mkstemp(prefix=".experiment-", dir=directory)
    try:
        with os.fdopen(fd, "w") as output:
            output.write(record.model_dump_json(indent=2) + "\n")
            output.flush()
            os.fsync(output.fileno())
        os.link(temporary, target)  # FileExistsError preserves the prior record.
    finally:
        os.unlink(temporary)
    return target


def corpus_fingerprint(evidence: list[Evidence]) -> str:
    """Pin content and policy metadata without machine-specific source paths."""
    return fingerprint(sorted(
        [item.model_dump(mode="json", exclude={"source_uri"}) for item in evidence],
        key=lambda item: item["id"],
    ))


def run_experiment(
    runtime: WorkbenchRuntime, plan: ExecutionPlan, dataset: DatasetManifest, strategy: StrategyManifest,
    request: RequestContext, *, experiment_id: str, run_id: str, hypothesis: str,
    baseline: str, split: Split, output_directory: Path, k: int = 5,
    ranking_component: str = "fusion.rrf@1.0.0",
) -> Path:
    """Run a pinned dataset through the existing graph, recording a safe artifact.

    No provider or component is invoked outside WorkbenchRuntime. Ranking metrics
    describe the nominated candidate stage, not answer entailment or promotion.
    """
    import time

    dataset = DatasetManifest.model_validate(dataset.model_dump(mode="json"))
    strategy = StrategyManifest.model_validate(strategy.model_dump(mode="json"))
    if not re.fullmatch(SAFE_ID, experiment_id) or not re.fullmatch(SAFE_ID, run_id):
        raise ValueError("experiment and run IDs must be safe artifact names")
    if k <= 0:
        raise ValueError("k must be positive")
    if strategy.graph_fingerprint != plan.fingerprint:
        raise ValueError("strategy graph fingerprint mismatch")
    if dataset.corpus_revision != corpus_fingerprint(runtime.evidence):
        raise ValueError("dataset corpus fingerprint mismatch")
    if strategy.evaluation_dataset != f"{dataset.dataset_id}@{dataset.version}":
        raise ValueError("strategy evaluation dataset mismatch")
    component_ids = [node.component for node in plan.pipeline.graph.nodes]
    if set(strategy.required_components) != set(component_ids):
        raise ValueError("strategy component requirements differ from graph")
    if component_ids.count(ranking_component) != 1:
        raise ValueError("ranking component must identify exactly one graph node")
    if strategy.required_models != [runtime.model_version]:
        raise ValueError("strategy model identity differs from runtime")
    # This initial runner supports the fixture only. Do not imply that index/model
    # version checks exist for local-real until those contracts are implemented.
    if strategy.required_indexes or runtime.model_version != "deterministic-local-generator@1.0.0":
        raise ValueError("initial experiment runner supports the deterministic fixture only")
    cases = [case for case in dataset.cases if case.split == split]
    if not cases:
        raise ValueError("selected dataset split is empty")
    if any(case.query_class not in strategy.supported_query_classes for case in cases):
        raise ValueError("dataset query class is unsupported by strategy")
    if any(case.policy_constraints for case in cases):
        raise ValueError("case policy constraints require a future explicit policy-case runner")
    evidence_ids = [item.id for item in runtime.evidence]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("corpus evidence IDs must be unique")
    if any(not set(case.expected_evidence_ids + case.hard_negative_ids) <= set(evidence_ids) for case in cases):
        raise ValueError("case references evidence absent from pinned corpus")

    class RecordingRegistry:
        def __init__(self) -> None:
            self.ranked_ids: list[str] | None = None

        def get(self, reference: str) -> ComponentManifest:
            return runtime.registry.get(reference)

        def execute(self, reference: str, inputs: Any, context: Any, config: Any) -> Any:
            outputs = runtime.registry.execute(reference, inputs, context, config)
            if reference == ranking_component:
                self.ranked_ids = [candidate.evidence.id for candidate in outputs["candidates"]]
            return outputs

    results: list[dict[str, Any]] = []
    failures: list[str] = []
    for case in cases:
        registry = RecordingRegistry()
        measured = WorkbenchRuntime(registry=registry, trace_store=runtime.trace_store, model_version=runtime.model_version)
        measured.set_evidence(runtime.evidence)
        started = time.monotonic()
        try:
            result = measured.run(plan, case.query, request)
            if registry.ranked_ids is None:
                raise ValueError("ranking stage did not execute")
            metrics = ranking_metrics(registry.ranked_ids, case, k)
            citation_ids = [item.id for item in result.citations]
            passed = result.abstained == case.expected_abstention and set(case.expected_evidence_ids) <= set(citation_ids)
            if metrics.hard_negative_hits:
                passed = False
            if not passed:
                failures.append(f"{case.case_id}: fixture expectations failed")
            results.append({
                "case_id": case.case_id, "query_class": case.query_class,
                "status": "completed", "passed": passed,
                "run_id": result.manifest.run_id, "ranked_evidence_ids": registry.ranked_ids,
                "citation_ids": citation_ids, "abstained": result.abstained,
                "ranking": metrics.model_dump(mode="json"),
                "latency_ms": (time.monotonic() - started) * 1000,
                "token_usage": result.manifest.token_usage.model_dump(mode="json"),
                "claim_support": None,
            })
        except Exception as error:
            # Error class only: provider exception text can contain private URLs/data.
            failures.append(f"{case.case_id}: {type(error).__name__}")
            results.append({"case_id": case.case_id, "query_class": case.query_class,
                            "status": "failed", "passed": False, "error_type": type(error).__name__})
    valid = [item["ranking"] for item in results if item["status"] == "completed"]
    aggregate: dict[str, Any] = {
        "cases": len(cases), "completed_cases": len(valid),
        "fixture_passes": sum(item["passed"] for item in results),
        "citation_precision": None, "citation_coverage": None, "unsupported_claim_rate": None,
        "peak_memory_bytes": None,
    }
    for name in ("recall_at_k", "precision_at_k", "mrr", "ndcg_at_k"):
        values = [item[name] for item in valid if item[name] is not None]
        aggregate[name] = {"mean": sum(values) / len(values) if values else None, "denominator": len(values)}
    configuration = {"strategy": strategy.model_dump(mode="json"),
                     "request": request.model_dump(mode="json"),
                     "k": k, "ranking_component": ranking_component, "split": split}
    record = ExperimentRecord(
        schema_version="1.1.0",
        dataset_snapshot=dataset.model_dump(mode="json"),
        configuration_snapshot=configuration,
        pipeline_snapshot=plan.pipeline.model_dump(mode="json"),
        experiment_id=experiment_id, run_id=run_id, hypothesis=hypothesis, baseline=baseline,
        candidate_strategy=strategy, dataset_fingerprint=dataset.fingerprint,
        config_fingerprint=fingerprint(configuration),
        split=split, status="failed" if any(item["status"] == "failed" for item in results) else "completed",
        case_results=results, metrics=aggregate, failures=failures, decision="iterate",
        notes="Deterministic fixture measurement only. No semantic retrieval, claim support, or promotion evidence. Missing metrics remain null.",
    )
    return write_record(output_directory, record)
