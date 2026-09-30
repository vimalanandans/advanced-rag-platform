# ADR-013: Versioned local-real retrieval composition

## Status

Accepted for experimental implementation; local-real operational and quality acceptance pending.

## Context

Hash vectors and simplified lexical scoring are useful fixtures but cannot establish semantic retrieval quality. A persistent lexical baseline and explicit embedding identity are prerequisites for A–F comparisons.

## Decision

Keep v1 fixture components. Add persistent `retrieval.bm25@2.0.0` and `retrieval.exact@1.0.0`; adapt the neutral vector retriever to an explicit embedding provider. The local-real profile requires model/digest/dimension settings and selects a graph-schema-2 pipeline. SQLite caches immutable term statistics and scoring uses only permitted documents. Ollama serves pinned, bounded batches with no truncation or hash fallback. Compile-time JSON Schema validation enforces published component configuration.

## Consequences

API profile selection is explicit, but the local-real graph remains experimental until hierarchy, verification, routing and experiments are accepted. No model license/default is assumed. Existing indexes remain intact; incompatible dimensions require a new collection. Candidate decisions and corpus/model identity are traceable. Live provider integration and M3 resource validation are outstanding; unit doubles do not demonstrate semantic recall.
