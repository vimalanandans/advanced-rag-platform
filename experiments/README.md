# Engineering experiments

Store each experiment in its own stable ID directory. Follow the [evaluation plan](../docs/v2/evaluation-plan.md) and copy the [loop template](templates/engineering-loop.json). Keep hypothesis, baseline/candidate configuration, dataset versions/splits, fingerprints, case-level outputs, metrics, failures and decision together.

Never overwrite an accepted result when rerunning: create a new run identity. Commit only approved fixtures and safe summaries; private evidence and credentials do not belong in the repository. A documentation/audit loop may record no retrieval metrics; it must not invent improvements.


## Implemented fixture runner

```bash
python3 scripts/run_fixture_experiment.py
```

This writes a unique result and JSON run traces under `.local/experiments/`. Use `--output <directory>` to choose a local artifact directory. It pins the existing graph, corpus fingerprint, strategy and two golden regression cases, measures ranking, and retains dataset/configuration/graph snapshots. It explicitly selects deterministic providers regardless of environment variables. It does not tune or promote a strategy.

The typed contracts are in `rag_workbench/experimentation.py`. Dataset validation rejects overlapping source groups/normalized queries across splits, duplicate IDs, contradictory labels and corpus mismatches. Near-duplicate/semantic leakage still needs corpus annotation/review. Metric outputs include denominators and null reasons. MRR is measured within the configured top-K window. Unsupported citation-quality metrics remain null. V2 attempted-claim outcomes and process peak RSS are recorded where available. The default fixture runner rejects local-real indexes. The separate [comparison command](../docs/v2/strategy-comparison.md) explicitly enables local-real evaluation and permits only validated scope-narrowing case policies.

Result files use atomic no-overwrite publication. Runtime trace stores also reject conflicting terminal writes; live PostgreSQL acceptance is still pending. Preflight validation errors raise before a run starts; per-case execution failures produce failed experiment records. Result snapshots may contain queries and labels: store private datasets only in an access-controlled local directory. The checked-in example contains public repository fixtures only.
