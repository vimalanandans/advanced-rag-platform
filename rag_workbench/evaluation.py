import json
from pathlib import Path

from rag_workbench.contracts import EvaluationCase, EvaluationResult
from rag_workbench.graph import ExecutionPlan
from rag_workbench.runtime import WorkbenchRuntime


def evaluate(runtime: WorkbenchRuntime, plan: ExecutionPlan, cases: list[EvaluationCase]) -> EvaluationResult:
    outcomes = []
    for case in cases:
        result = runtime.run(plan, case.question)
        citation_ids = {item.id for item in result.citations}
        passed = result.abstained == case.expect_abstention and set(case.expected_evidence_ids).issubset(citation_ids)
        outcomes.append({"id": case.id, "passed": passed, "citations": sorted(citation_ids), "abstained": result.abstained})
    return EvaluationResult(pipeline_fingerprint=plan.fingerprint, passed=sum(item["passed"] for item in outcomes), failed=sum(not item["passed"] for item in outcomes), cases=outcomes)


def load_cases(path: Path) -> list[EvaluationCase]:
    return [EvaluationCase(**item) for item in json.loads(path.read_text())]
