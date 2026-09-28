# Architecture

## Dependency direction

`Studio/API → control and runtime services → contracts, graph engine, registries → components → providers`.
Dependencies point inward. Providers implement contracts and cannot define domain behavior.

## Planes

- **Control plane:** pipeline versions, components/capabilities, corpora, configuration, datasets, and releases.
- **Execution plane:** PipelineGraph compiler, scheduler, bounded executor, context/budget manager, and run manifest.
- **Capability plane:** ingestion, retrieval, fusion, verification, context packing, generation, and abstention.
- **Observability/evaluation plane:** local traces, metrics, golden datasets, experiments, and regressions.

## Configuration layers

- Platform configuration defines local infrastructure and installed providers.
- Customer configuration defines allowed corpora, models, skills, policies, and budgets.
- Pipeline configuration defines graph nodes, edges, versions, and component configuration.

The current release runs one local administrator while retaining customer/ACL fields in its contracts.
