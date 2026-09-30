# V2 implementation status

Updated 2026-09-29. This is a delivery record, not a claim that the entire V2 platform exists.

## Delivered

- V2-00: assessment, eight-layer architecture, migration/backlog, evaluation, research protocol, 27-group requirements map, ADR-010 and permanent AGENT.md contract.
- Documentation alignment: authorization before retrieval, M3 target, first-milestone reranker/classifier/claim verification, truthful fixture retrieval wording and regenerated compendium.
- Initial V2-02: typed dataset/case/strategy/experiment contracts; split and label validation; corpus/graph/model checks; Recall@K, Precision@K, MRR within K and graded nDCG@K; fixture runner; dataset/configuration/graph snapshots; atomic no-overwrite experiment publication; safe per-case failure records and explicit unavailable metrics.

## Evidence

| Check | Result |
| --- | --- |
| Baseline test suite before changes | 26 passed |
| Suite after first experiment slice | 39 passed, including 13 new experiment tests |
| Studio production build | Passed during baseline audit; no Studio files changed |
| Python compilation | Passed during baseline audit; final verification recorded in the loop artifact |
| Documentation/reference checks | Passed; seven API routes |
| Fixture experiment | Two of two regression cases pass; no candidate strategy or semantic-quality improvement claimed |
| Docker Compose / live providers | Blocked: Docker command unavailable |
| Ruff | Blocked: module not installed |

See [experiment artifacts](../../experiments/v2-02-fixture-baseline/README.md). The first experimental artifact lacked full snapshots/durable trace files and is retained as an incomplete intermediate result; the later record includes them. Neither record promotes a retrieval strategy.

## Remaining implementation

All local-real retrieval, corpus publication/index lifecycle, shared-index authorization hardening, runtime terminal/loop/deadline changes, claim/conflict verification, real reranking/classification/routing, representative held-out datasets, A–F comparison, Studio inspection extensions and advanced research slices remain pending. Documentation is specified; this list is not implemented by the first experiment slice.

Next execute V2-01 local operations/safety hardening and extend V2-02 metrics/policy cases, then V2-03 real retrieval. Docker/M3-dependent gates require the target environment; independent deterministic work can proceed without pretending those gates passed.
