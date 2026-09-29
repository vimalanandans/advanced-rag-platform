# Product Goals

## Product concept

The RAG Engineering Workbench is a **local-first reference environment for deciding how a RAG system should
retrieve, verify, and cite evidence**. It is not a generic chat application and it is not a vector database
dashboard. Its job is to make retrieval behavior explicit, measurable, repeatable, and inspectable before a
team ships it into a customer product.

The core idea is simple: a RAG answer is only as trustworthy as the evidence selected before generation. The
workbench therefore treats authorization, source revision, retrieval lanes, verification, context limits,
citations, and abstention as first-class engineering concerns.

## Who it serves

| User | Job to be done | What success looks like |
| --- | --- | --- |
| RAG product owner | Decide whether a retrieval approach is ready to adopt | Can compare a baseline and an experiment using citations, abstentions, traces, and versioned evaluation. |
| Data engineer | Turn local Markdown/PDF sources into policy-controlled evidence | Can preserve source, page/section, revision, approval state, and corpus policy through retrieval. |
| Developer | Add a retrieval, ranking, or generation capability safely | Can register a typed component and graph it explicitly without embedding provider behavior in contracts. |
| Operator | Run and diagnose a local workbench | Can start the local stack, inspect durable run records, reproduce a failure, and understand the provider profile. |

## Goals for the reference release

1. **Make evidence inspectable.** Every response has authorized citations or an explicit abstention.
2. **Make orchestration explicit.** A validated, versioned `PipelineGraph` owns sequencing, conditions,
   budgets, retries, and loops; components do not hide downstream behavior.
3. **Establish a measured retrieval baseline.** Run lexical/BM25, dense, and vectorless structural retrieval,
   fuse candidates, verify evidence, and apply bounded context assembly before generation.
4. **Keep local execution real.** The deterministic profile works without cloud services; Compose provides
   local PostgreSQL, MinIO, Qdrant, Ollama, API, worker, and Studio adapters.
5. **Keep providers replaceable.** Provider choice is platform configuration, never a public contract or a
   customer-specific branch. A selected provider failure remains visible in the trace.
6. **Make change measurable.** Every strategy has deterministic tests, versioned golden fixtures, graph
   fingerprints, and evaluation guidance before it is accepted.
7. **Prioritize inspection before authoring.** The first Studio makes runs, evidence, lanes, context, budgets,
   errors, and evaluation results legible; visual graph editing is deliberately later.

## Explicit non-goals

The reference release is not yet a multi-tenant SaaS, a production deployment template, a visual pipeline
authoring system, an autonomous-agent platform, or a general-purpose document-management product. It models
future tenant and ACL boundaries in contracts, but operates as a single local administrator today.

It does not assume that advanced RAG techniques are improvements by default. A new strategy enters only when
evaluation identifies a retrieval, provenance, citation, abstention, latency, or budget gap that the baseline
cannot satisfy.

## Product decisions and acceptance

The [Advanced RAG Strategies guide](ADVANCED_RAG_STRATEGIES.md) explains when a retrieval technique is worth
adding. [Architecture](ARCHITECTURE.md) explains the boundaries that keep it composable. The
[Definition of Done](docs/definition-of-done/README.md) defines the evidence required to call a change
accepted.
