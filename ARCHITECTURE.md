# Architecture Principles

The workbench is designed to make evidence-grounded RAG behavior inspectable and portable. The detailed
diagrams and runtime flow are in [System Architecture](docs/architecture/system.md); this page records the
decisions every change must preserve.

## Dependency direction

`Studio/API → control and runtime services → contracts, graph engine, registries → components → providers`.

Dependencies point inward. A provider adapter can implement a local model, vector index, or trace store, but it
cannot define a domain contract, change graph behavior, or leak provider-specific objects to a caller.

## Four planes

| Plane | Responsibility | Primary output |
| --- | --- | --- |
| Control | Pipeline versions, component catalog, configuration, datasets, and releases | Validated graph and chosen run configuration |
| Execution | Compiler, bounded scheduler, context/budget management, checkpointing | Reproducible `RunResult` and manifest |
| Capability | Ingestion, retrieval, fusion, verification, context packing, generation | Authorized candidate evidence and cited answer/abstention |
| Observability and evaluation | Traces, metrics, fixtures, experiments, regressions | Evidence for accepting or rejecting a strategy |

## Configuration ownership

| Layer | Owns | Must not own |
| --- | --- | --- |
| Platform | local infrastructure, installed providers, storage, CORS | customer policy or graph semantics |
| Customer | permitted corpora, policy, data, evaluation sets, budgets | forked shared domain code |
| Pipeline | graph nodes, edges, versions, component configuration | credentials, provider implementation values, customer secrets |

The current release runs one local administrator while retaining tenant/corpus/ACL fields in its contracts for
future use. See [ADRs](docs/adr/) for decisions and [Definition of Done](docs/definition-of-done/README.md) for
the acceptance standard.
