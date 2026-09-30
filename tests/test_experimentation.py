from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from rag_workbench.contracts import RequestContext
from rag_workbench.experimentation import (
    DatasetManifest, ExperimentCase, ExperimentRecord, StrategyManifest,
    corpus_fingerprint, ranking_metrics, run_experiment, write_record,
)
from rag_workbench.graph import pipeline_from_yaml
from rag_workbench.providers import LocalProviderProfile
from rag_workbench.runtime import demo_runtime


def case(**updates):
    values = dict(case_id="one", query="query", query_class="semantic", corpus_revision="revision",
                  source_group="source", split="regression", expected_evidence_ids=["a", "b"],
                  hard_negative_ids=["negative"])
    return ExperimentCase(**(values | updates))


def dataset(cases):
    return DatasetManifest(dataset_id="test", version="1.0.0", corpus_revision="revision",
                           provenance="synthetic", license="test", cases=cases)


def test_ranking_metrics_deduplicate_and_use_explicit_denominators():
    result = ranking_metrics(["negative", "a", "a", "b"], case(), k=3)
    assert result.recall_at_k == 1
    assert result.precision_at_k == pytest.approx(2 / 3)
    assert result.mrr == 0.5
    assert 0 < result.ndcg_at_k < 1
    assert result.hard_negative_hits == 1
    assert result.retrieved_count == 3
    assert ranking_metrics(["a"], case(), k=5).precision_at_k == 0.2


def test_empty_relevance_is_not_reported_as_perfect_recall():
    result = ranking_metrics([], case(expected_evidence_ids=[], expected_abstention=True), k=5)
    assert result.recall_at_k is None
    assert result.mrr is None
    assert result.ndcg_at_k is None
    assert result.unavailable_reason == "no expected relevant evidence"
    with pytest.raises(ValueError, match="positive"):
        ranking_metrics([], case(), k=0)


def test_graded_ranking_respects_order():
    labels = case(relevance={"a": 3, "b": 1})
    assert ranking_metrics(["a", "b"], labels, 2).ndcg_at_k == 1
    assert ranking_metrics(["b", "a"], labels, 2).ndcg_at_k < 1


@pytest.mark.parametrize("second", [
    {"case_id": "one"},
    {"case_id": "two", "split": "held_out", "query": "other"},
    {"case_id": "two", "split": "tuning", "source_group": "other", "query": " QUERY "},
    {"case_id": "two", "corpus_revision": "other"},
])
def test_dataset_rejects_duplicate_ids_leakage_and_revision_mismatch(second):
    with pytest.raises(ValidationError):
        dataset([case(), case(**second)])


def test_case_rejects_contradictory_labels():
    with pytest.raises(ValidationError):
        case(hard_negative_ids=["a"])
    with pytest.raises(ValidationError):
        case(relevance={"a": -1})
    with pytest.raises(ValidationError):
        case(expected_abstention=True)


def fixture():
    root = Path(__file__).parent.parent
    runtime = demo_runtime(provider_profile=LocalProviderProfile())
    plan = runtime.compile(pipeline_from_yaml((root / "configs/pipelines/baseline.yaml").read_text()))
    revision = corpus_fingerprint(runtime.evidence)
    data = DatasetManifest(dataset_id="fixture", version="1.0.0", corpus_revision=revision,
                           provenance="repository", license="repository", cases=[case(
                               corpus_revision=revision, query="When should RAG abstain?",
                               expected_evidence_ids=[], hard_negative_ids=[])])
    strategy = StrategyManifest(
        strategy_id="fixture", version="1.0.0", graph_fingerprint=plan.fingerprint,
        supported_query_classes=["semantic"], supported_content_classes=["markdown"],
        required_components=[node.component for node in plan.pipeline.graph.nodes],
        required_models=[runtime.model_version], latency_expectations={}, resource_requirements={},
        known_limitations=["fixture"], evaluation_dataset="fixture@1.0.0",
    )
    return runtime, plan, data, strategy


def execute(tmp_path, *args):
    return run_experiment(*args, RequestContext(tenant_id="local", user_id="local-admin",
                          requested_at=datetime(2026, 9, 29, tzinfo=UTC)),
                          experiment_id="baseline", run_id="run-one", hypothesis="fixture",
                          baseline="v1", split="regression", output_directory=tmp_path)


def test_runner_persists_graph_measurements_and_missing_metrics(tmp_path):
    runtime, plan, data, strategy = fixture()
    path = execute(tmp_path, runtime, plan, data, strategy)
    record = ExperimentRecord.model_validate_json(path.read_text())
    assert record.status == "completed"
    assert record.dataset_fingerprint == data.fingerprint
    assert record.dataset_snapshot["dataset_id"] == data.dataset_id
    assert record.pipeline_snapshot["id"] == plan.pipeline.id
    assert record.case_results[0]["ranked_evidence_ids"]
    assert record.metrics["citation_precision"] is None
    assert record.decision == "iterate"
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        write_record(tmp_path, record)
    assert path.read_bytes() == original
    assert not list(tmp_path.glob(".experiment-*"))


def test_runner_records_failures_without_raw_error_text(tmp_path):
    runtime, plan, data, strategy = fixture()
    def fail(*_args):
        raise RuntimeError("private-secret-url")
    runtime.registry._executors["retrieval.bm25@1.0.0"] = fail
    path = execute(tmp_path, runtime, plan, data, strategy)
    record = ExperimentRecord.model_validate_json(path.read_text())
    assert record.status == "failed"
    assert record.case_results[0]["error_type"] == "RuntimeError"
    assert "private-secret-url" not in path.read_text()
    assert record.metrics["mrr"]["denominator"] == 0
    with pytest.raises(ValidationError):
        ExperimentRecord.model_validate(record.model_dump() | {"decision": "accept"})


def test_runner_rejects_wrong_graph_and_changed_corpus_before_execution(tmp_path):
    runtime, plan, data, strategy = fixture()
    strategy.graph_fingerprint = "0" * 64
    with pytest.raises(ValueError, match="graph fingerprint"):
        execute(tmp_path, runtime, plan, data, strategy)
    strategy.graph_fingerprint = plan.fingerprint
    runtime.evidence[0].content += " changed"
    with pytest.raises(ValueError, match="corpus fingerprint"):
        execute(tmp_path, runtime, plan, data, strategy)
    assert not runtime.trace_store.list()


def test_runner_does_not_silently_ignore_policy_constraints(tmp_path):
    runtime, plan, data, strategy = fixture()
    data.cases[0].policy_constraints = {"deny": "all"}
    with pytest.raises(ValueError, match="policy constraints"):
        execute(tmp_path, runtime, plan, data, strategy)
    assert not runtime.trace_store.list()


def test_artifact_snapshots_detect_tampering(tmp_path):
    path = execute(tmp_path, *fixture())
    payload = __import__("json").loads(path.read_text())
    payload["configuration_snapshot"]["k"] = 99
    with pytest.raises(ValidationError, match="configuration snapshot"):
        ExperimentRecord.model_validate(payload)


def test_generation_failure_preserves_retrieval_measurement_and_trace(tmp_path):
    runtime, plan, data, strategy = fixture()
    def fail(*_args):
        raise TimeoutError("private-provider-payload")
    generation = next(node.component for node in plan.pipeline.graph.nodes if node.id == "generate")
    runtime.registry._executors[generation] = fail
    record = ExperimentRecord.model_validate_json(execute(tmp_path, runtime, plan, data, strategy).read_text())
    result = record.case_results[0]
    assert result["status"] == "failed"
    assert result["ranked_evidence_ids"]
    assert result["stage_ranking"]
    assert result["stage_latency_ms"]["generate"] >= 0
    assert runtime.trace_store.get(result["run_id"]).status == "failed"
    assert record.metrics["completed_cases"] == 0
    assert record.metrics["ranked_cases"] == 1
    assert "private-provider-payload" not in record.model_dump_json()


def test_configuration_fingerprint_includes_provider_options(tmp_path):
    runtime, plan, data, strategy = fixture()
    first = ExperimentRecord.model_validate_json(execute(tmp_path / "first", runtime, plan, data, strategy).read_text())
    runtime.asset_versions["generation_options"] = '{"think": false}'
    second = ExperimentRecord.model_validate_json(execute(tmp_path / "second", runtime, plan, data, strategy).read_text())
    assert first.config_fingerprint != second.config_fingerprint
    assert second.configuration_snapshot["asset_versions"] == runtime.asset_versions
