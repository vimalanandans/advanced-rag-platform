from pathlib import Path

from rag_workbench.graph import pipeline_from_yaml
from rag_workbench.ingestion import ingest_path
from rag_workbench.runtime import WorkbenchRuntime


def test_baseline_run_is_cited_and_traced():
    root = Path(__file__).parent.parent
    runtime = WorkbenchRuntime()
    runtime.set_evidence(ingest_path(root / "data/fixtures/rag_basics.md"))
    plan = runtime.compile(pipeline_from_yaml((root / "configs/pipelines/baseline.yaml").read_text()))
    result = runtime.run(plan, "When should the system abstain?")
    assert not result.abstained
    assert result.citations
    assert result.manifest.graph_fingerprint == plan.fingerprint
    assert len(result.manifest.node_executions) == 8


def test_unknown_question_abstains():
    root = Path(__file__).parent.parent
    runtime = WorkbenchRuntime()
    runtime.set_evidence(ingest_path(root / "data/fixtures/rag_basics.md"))
    plan = runtime.compile(pipeline_from_yaml((root / "configs/pipelines/baseline.yaml").read_text()))
    assert runtime.run(plan, "What is the capital of Mars?").abstained
