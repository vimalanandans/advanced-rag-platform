# V2-02 deterministic fixture baseline

Purpose: establish persisted experiment measurements without changing retrieval behavior.

- `v2-fixture-baseline--2ffedd3f-7298-44c7-af6d-5c5da9674b61.json` is the initial intermediate result. It lacks full input snapshots and durable trace files. Retained for diagnosis; do not treat it as fully replayable.
- `v2-fixture-baseline--549d9645-0c6a-416f-a9e2-be59b4bb1028.json` includes graph, configuration and dataset snapshots. Its run manifests are under `traces/`.
- Both use the same preserved graph and two regression cases. They are not independent held-out datasets and do not compare retrieval strategies.

Both cases satisfy fixture citation/abstention expectations. One case has expected evidence: Recall@5, MRR within five and nDCG@5 are 1.0 on that single case. The no-evidence case is excluded from those means with a null reason. Citation support/coverage, unsupported claims and peak memory remain unmeasured. Timing is a single in-process observation, not an M3 performance benchmark.

Decision: **iterate**. The experiment infrastructure is tested, but semantic retrieval and strategy promotion remain unproven. See the [implementation status](../../docs/v2/implementation-status.md) for gates and limitations.
