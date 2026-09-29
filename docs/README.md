# Documentation

This is the living documentation index for the Local-First Graph-Native RAG Workbench. Product behavior is
defined by typed contracts, versioned pipeline YAML, and executable tests; these guides explain how to use and
operate that behavior without duplicating provider implementation details.

## Start here

| Audience | Read this | Outcome |
| --- | --- | --- |
| Product owner | [Goals](../Goals.md), [Design principles](design-principles/README.md), [Definition of Done](definition-of-done/README.md), [Evaluation](evaluation/README.md) | Decide whether a retrieval strategy is ready to accept. |
| Studio user | [First local run](user-guide/first-local-run.md) | Run and inspect the evidence-first baseline. |
| API consumer | [API reference](api/README.md) | Call the local control API with the required request scope. |
| Data engineer | [Data engineer guide](data-engineer-guide/README.md), [Configuration reference](reference/configuration.md) | Prepare evidence and select measured retrieval behavior. |
| Developer | [Developer guide](developer-guide/README.md), [Architecture](architecture/system.md), [ADRs](adr/) | Extend components without breaking graph or provider boundaries. |
| Operator | [Operations](operations/README.md), [Configuration reference](reference/configuration.md), [Security](security/README.md) | Start a reproducible local stack and inspect durable traces. |

## Reference map

- [Architecture](architecture/system.md) explains dependencies, runtime flow, and local service boundaries.
- [API reference](api/README.md) documents the FastAPI endpoints. The live local OpenAPI schema is served at
  `/openapi.json`, with interactive Swagger UI at `/docs`.
- [Configuration](reference/configuration.md) lists supported local settings and their ownership layer.
- [First local run](user-guide/first-local-run.md) is a safe deterministic walkthrough.
- [Definition of Done](definition-of-done/README.md) is the acceptance gate for every change.

## Writing standard

Write for the decision the reader must make. Lead with the product outcome, state what is available today and
what is intentionally later, use the same terms as the code (`PipelineGraph`, evidence, citation, abstention,
run manifest), and never turn a local default or a placeholder token into a production promise. Update a guide
when its public behavior changes; `scripts/check_docs.py` protects the API, configuration, and local links.

## Maintenance

`scripts/check_docs.py` extracts routes from `rag_workbench/api.py` and checks that the API and configuration
references still cover the public local surface. It runs in CI. Update the relevant guide, this index, and the
check when a new public route or configuration setting is intentionally introduced.
