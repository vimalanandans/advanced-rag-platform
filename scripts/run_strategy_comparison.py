"""Run one local-real A-F arm, or all arms in isolated processes."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rag_workbench.contracts import Evidence, RequestContext
from rag_workbench.experimentation import (
    DatasetManifest,
    ExperimentRecord,
    StrategyManifest,
    run_experiment,
)
from rag_workbench.local_real import local_real_runtime
from rag_workbench.observability import JsonTraceStore
from rag_workbench.strategy_graphs import ARMS, experiment_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True, help="Approved evaluation Evidence JSON array")
    parser.add_argument("--output", type=Path, default=ROOT / ".local/strategy-comparison")
    parser.add_argument("--split", choices=["development", "tuning", "held_out", "adversarial", "regression"], default="held_out")
    parser.add_argument("--requested-at", required=True, help="Pinned ISO-8601 timestamp with timezone")
    parser.add_argument("--max-latency-ms", type=int, help="Explicit experiment deadline override, recorded in graph fingerprint")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--arm", choices=list(ARMS))
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if args.max_latency_ms is not None and args.max_latency_ms <= 0:
        parser.error("--max-latency-ms must be positive")
    if args.all:
        outcomes = {}
        for arm in ARMS:
            command = [sys.executable, str(Path(__file__).resolve()), "--dataset", str(args.dataset), "--corpus", str(args.corpus),
                       "--output", str(args.output), "--split", args.split, "--requested-at", args.requested_at, "--arm", arm]
            if args.max_latency_ms is not None:
                command += ["--max-latency-ms", str(args.max_latency_ms)]
            outcomes[arm] = subprocess.run(command, check=False).returncode
        args.output.mkdir(parents=True, exist_ok=True)
        target = args.output / f"comparison-{uuid.uuid4()}.json"
        with target.open("x") as output:
            json.dump({"arm_exit_codes": outcomes, "decision": "iterate", "note": "Independent processes; inspect all case-level results. No automatic promotion."}, output, indent=2)
        print(target)
        return int(any(outcomes.values()))
    run_id = str(uuid.uuid4())
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        timestamp = datetime.fromisoformat(args.requested_at)
        if timestamp.tzinfo is None:
            raise ValueError("evaluation time requires timezone")
        dataset = DatasetManifest.model_validate_json(args.dataset.read_text())
        corpus = [Evidence.model_validate(item) for item in json.loads(args.corpus.read_text())]
        runtime = local_real_runtime(trace_store=JsonTraceStore(args.output / "traces"))
        runtime.set_evidence(corpus)
        pipeline = experiment_pipeline(args.arm)
        if args.max_latency_ms is not None:
            pipeline.budgets.max_latency_ms = args.max_latency_ms
        plan = runtime.compile(pipeline)
        models = [runtime.model_version]
        indexes = []
        if "dense" in ARMS[args.arm]:
            models.append(runtime.asset_versions["embedding"])
            indexes.append(runtime.index_revisions["vector_collection"])
        if "bm25" in ARMS[args.arm]:
            indexes.append(runtime.index_revisions["lexical"])
        if args.arm in {"E", "F"}:
            if "reranker" not in runtime.asset_versions:
                raise ValueError("E/F require a configured local reranker")
            models.append(runtime.asset_versions["reranker"])
        strategy = StrategyManifest(
            strategy_id=f"experiment-arm-{args.arm.lower()}", version="1.0.0", graph_fingerprint=plan.fingerprint,
            supported_query_classes=sorted({case.query_class for case in dataset.cases}), supported_content_classes=["markdown", "pdf"],
            required_components=[node.component for node in plan.pipeline.graph.nodes], required_models=models, required_indexes=indexes,
            latency_expectations={"max_latency_ms": plan.pipeline.budgets.max_latency_ms}, resource_requirements={"profile": "local-real"},
            known_limitations=["Experimental; no automatic acceptance", "Quoted-sentence verifier, heuristic classification and limited evidence sufficiency"],
            evaluation_dataset=f"{dataset.dataset_id}@{dataset.version}",
        )
        artifact = run_experiment(runtime, plan, dataset, strategy, RequestContext(tenant_id="local", user_id="local-admin", requested_at=timestamp),
                                  experiment_id=f"local-real-{args.arm.lower()}", run_id=run_id, hypothesis=f"Evaluate controlled strategy arm {args.arm}",
                                  baseline="experiment-arm-a@1.0.0", split=args.split, output_directory=args.output,
                                  ranking_component="ranking.local@1.0.0" if args.arm in {"E", "F"} else "fusion.rrf@1.0.0", allow_local_real=True)
        record = ExperimentRecord.model_validate_json(artifact.read_text())
        print(artifact)
        return int(bool(record.failures))
    except Exception as error:  # noqa: BLE001 - persist a redacted preflight failure
        target = args.output / f"preflight-{args.arm.lower()}-{run_id}.json"
        with target.open("x") as output:
            json.dump({"arm": args.arm, "status": "failed", "phase": "preflight", "error_type": type(error).__name__, "decision": "iterate"}, output, indent=2)
        print(target)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
