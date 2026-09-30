"""Record the deterministic fixture as a V2 experiment; no external services required."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rag_workbench.contracts import RequestContext
from rag_workbench.evaluation import load_cases
from rag_workbench.experimentation import DatasetManifest, ExperimentCase, StrategyManifest, corpus_fingerprint, run_experiment
from rag_workbench.graph import pipeline_from_yaml
from rag_workbench.observability import JsonTraceStore
from rag_workbench.providers import LocalProviderProfile
from rag_workbench.runtime import demo_runtime


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".local" / "experiments")
    args = parser.parse_args()
    runtime = demo_runtime(provider_profile=LocalProviderProfile(), trace_store=JsonTraceStore(args.output / "traces"))
    plan = runtime.compile(pipeline_from_yaml((ROOT / "configs/pipelines/baseline.yaml").read_text()))
    revision = corpus_fingerprint(runtime.evidence)
    dataset = DatasetManifest(
        dataset_id="baseline-fixture", version="1.0.0", corpus_revision=revision,
        provenance="Checked-in data/fixtures/rag_basics.md and data/golden/baseline.json",
        license="Repository LICENSE; fixture only",
        cases=[ExperimentCase(
            case_id=case.id, query=case.question, query_class="semantic", corpus_revision=revision,
            source_group="rag-basics", split="regression", expected_evidence_ids=case.expected_evidence_ids,
            expected_abstention=case.expect_abstention,
        ) for case in load_cases(ROOT / "data/golden/baseline.json")],
    )
    strategy = StrategyManifest(
        strategy_id="deterministic_fixture", version="1.0.0", graph_fingerprint=plan.fingerprint,
        supported_query_classes=["semantic"], supported_content_classes=["markdown"],
        required_components=[node.component for node in plan.pipeline.graph.nodes],
        required_models=[runtime.model_version], latency_expectations={"budget_ms": plan.pipeline.budgets.max_latency_ms},
        resource_requirements={"profile": "deterministic", "model_download": False},
        known_limitations=["Hashed vectors, simplified lexical scoring, two regression cases; not held-out research."],
        evaluation_dataset="baseline-fixture@1.0.0",
    )
    request = RequestContext(tenant_id="local", user_id="local-admin", requested_at=datetime(2026, 9, 29, tzinfo=UTC))
    output = run_experiment(
        runtime, plan, dataset, strategy, request, experiment_id="v2-fixture-baseline",
        run_id=str(uuid.uuid4()), hypothesis="The preserved fixture can produce a versioned, persisted ranking baseline.",
        baseline="local-evidence-baseline@1.0.0", split="regression", output_directory=args.output,
    )
    print(output)


if __name__ == "__main__":
    main()
