# Contributing

Contributions should make RAG behavior easier to inspect, reproduce, and evaluate. Start by reading
[Product Goals](Goals.md), [AGENTS.md](AGENTS.md), [Architecture](ARCHITECTURE.md), and the relevant
[ADRs](docs/adr/). Keep a change narrow, contract-first, and measurable.

## Before you change code

1. State the evidence-selection or operational gap you are addressing and the explicit non-goal.
2. Identify the affected public contract, graph, component, provider adapter, corpus policy, or Studio surface.
3. Add an ADR before making a material architecture decision.
4. For a retrieval change, add or update deterministic fixtures before tuning it.

## Delivery checklist

- Register typed, versioned component contracts and declare all dependencies in `PipelineGraph`.
- Preserve authorization before generation, bounded execution, safe telemetry, cited answers, and abstention.
- Document public configuration and operator impact; use the same terms as the product documentation.
- Add success and failure coverage. Provider, budget, and policy failures must remain visible rather than fall
  back silently.

Run the relevant checks before review:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
python scripts/check_docs.py
npm --prefix apps/studio run build
python -m compileall -q rag_workbench scripts
```

The full [Definition of Done](docs/definition-of-done/README.md) determines acceptance. Do not add large
corpora, secrets, model weights, generated build outputs, or unlicensed documents to the repository.
