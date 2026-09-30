from pathlib import Path

from rag_workbench.evaluation import evaluate, load_cases
from rag_workbench.graph import pipeline_from_yaml
from rag_workbench.ingestion import ingest_path
from rag_workbench.runtime import WorkbenchRuntime


def test_versioned_golden_baseline_regression_suite_passes():
    root = Path(__file__).parent.parent
    runtime = WorkbenchRuntime()
    runtime.set_evidence(ingest_path(root / "data/fixtures/rag_basics.md"))
    plan = runtime.compile(pipeline_from_yaml((root / "configs/pipelines/baseline.yaml").read_text()))
    result = evaluate(runtime, plan, load_cases(root / "data/golden/baseline.json"))
    assert result.failed == 0
    assert result.passed == 2
