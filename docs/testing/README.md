# Testing Guide

Testing protects the evidence boundary as well as code behavior. A green happy-path test is insufficient when a
change can affect authorization, provenance, budgets, citations, abstention, or provider selection.

## Required checks

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
python scripts/check_docs.py
npm --prefix apps/studio run build
python -m compileall -q rag_workbench scripts
```

The CI workflow also runs Ruff after installing development dependencies. Docker Compose checks are required by
the [Definition of Done](../definition-of-done/README.md) when a change affects the local stack.

## Test layers

| Layer | Protects | Example |
| --- | --- | --- |
| Unit | A single algorithm or adapter behavior | BM25 ranking, URL locality, PDF locator extraction |
| Contract | Typed, provider-neutral boundary behavior | Component manifests, request scope, trace-store interface |
| Graph | Valid pipeline topology and bounded control flow | Port types, cycles, budgets, declared loops |
| Pipeline | End-to-end cited answer or abstention | Three retrieval lanes, fusion, verification, context packing |
| Regression evaluation | Measured retrieval/citation/abstention behavior | Versioned golden cases and pipeline fingerprints |
| Studio/API | User-visible state and local request boundary | CORS/proxy, authorization, production build |
| Provider smoke | Optional local adapter readiness | Qdrant/Ollama selected profile with a real local service |

Add the smallest deterministic fixture that demonstrates the behavior and the smallest failure fixture that
proves the system refuses or records the failure safely. Follow the [Evaluation guide](../evaluation/README.md)
for retrieval changes.
