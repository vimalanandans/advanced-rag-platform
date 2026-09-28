# System Architecture

## Dependency rule

Dependencies point inward: Studio and API call control/runtime services; those services depend on contracts,
the graph compiler, and registry; components depend on provider-neutral interfaces; provider adapters do not
define domain contracts or graph behavior.

```mermaid
flowchart LR
    Studio[React Studio] --> API[FastAPI control API]
    API --> Runtime[Workbench runtime]
    API --> Evaluation[Golden evaluation runner]
    Runtime --> Graph[PipelineGraph compiler]
    Runtime --> Registry[Component registry]
    Runtime --> Trace[TraceStore contract]
    Registry --> Components[Retrieval, verification, context, generation]
    Components --> Providers[Provider-neutral adapters]
    Trace --> Json[Local JSON traces]
    Trace --> Postgres[(PostgreSQL)]
    Providers --> Qdrant[(Qdrant)]
    Providers --> Ollama[Ollama]
    Runtime --> Evidence[Authorized Markdown/PDF evidence]
```

The component registry is the only execution boundary. A component declares inputs and outputs in a manifest;
the graph binds it explicitly. Components cannot invoke arbitrary downstream components.

## Evidence-first execution

```mermaid
sequenceDiagram
    participant U as User or Studio
    participant A as Control API
    participant R as Runtime
    participant G as PipelineGraph
    participant T as Trace store

    U->>A: POST /runs + local request scope
    A->>R: compile validated baseline
    R->>R: authorize tenant, user, corpus, revision, freshness, applicability
    R->>G: classify → BM25 + dense + vectorless
    G->>G: fuse → verify → bounded context → generate
    G-->>R: cited answer or abstention
    R->>T: persist graph fingerprint, budgets, node trace, result
    R-->>A: RunResult + manifest
    A-->>U: inspectable response
```

Authorization happens before retrieval. The generator receives only approved, permitted evidence that fits the
context budget. If verification finds insufficient evidence, generation returns an explicit abstention.

## Local deployment boundary

The deterministic profile is the reproducible default: it needs no model download and is the fixture/CI
baseline. The optional local provider profile selects Qdrant for dense search and Ollama for generation through
platform configuration, not pipeline YAML. The selected model is recorded in each run manifest. Adapter failure
fails the trace; it never changes provider silently.

| Layer | Owns | Does not own |
| --- | --- | --- |
| Platform configuration | local services, provider profile, trace storage, local CORS | customer policy or pipeline semantics |
| Customer configuration | corpus permissions, policy, data, evaluation sets | shared-code forks |
| Pipeline configuration | versioned nodes, edges, component config, budgets | provider credentials or tenant secrets |

See [ADRs](../adr/) for decisions and [Configuration](../reference/configuration.md) for local settings.
