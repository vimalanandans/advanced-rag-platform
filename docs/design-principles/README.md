# Design Principles

These principles guide product and engineering decisions. They are deliberately testable: a feature that
violates one needs an explicit ADR and a compensating control, not a vague exception.

| Principle | In practice | Reject changes that |
| --- | --- | --- |
| Evidence before generation | Authorize, retrieve, verify, and budget evidence before calling generation. | Let a model answer from unapproved evidence or return a response without citations/abstention. |
| Graph-owned orchestration | Declare data, control, error, and feedback dependencies in `PipelineGraph`. | Hide component chaining, retries, or routing inside a component. |
| Local-first portability | Make the deterministic local path work without cloud services; isolate optional adapters. | Require a cloud account or let provider objects cross domain contracts. |
| Explicit configuration | Separate platform, customer, and pipeline configuration. | Add customer-specific shared-code branches or embed secrets in pipeline YAML. |
| Bounded execution | Cap time, context, output, iterations, tools, retries, and concurrency. | Introduce an unbounded loop, agent action, or fallback. |
| Observable failure | Persist safe metadata, graph identity, and failure reason for every run. | Replace failure with an invisible fallback or log raw credentials/evidence. |
| Measured complexity | Add a retrieval strategy only after a baseline gap is demonstrated. | Claim quality from intuition, model confidence, or a single attractive demo. |

Use the [Advanced RAG Strategies](../../ADVANCED_RAG_STRATEGIES.md) guide to identify a candidate strategy,
then use the [Definition of Done](../definition-of-done/README.md) to determine whether the measured change is
acceptable.
