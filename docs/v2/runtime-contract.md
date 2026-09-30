# Runtime graph contracts

Graph schema `1.0.0` retains the existing terminal node convention and canonical fingerprint. Graph schema `2.0.0` supports explicit terminal bindings, so components need not be named `generate` or `context`.

Example additions to a pipeline YAML:

```yaml
pipeline:
  id: example
  version: 2.0.0
  graph_schema_version: 2.0.0
  # nodes and edges remain explicit as in the baseline graph
  outputs:
    answer: generate.answer
    citations: generate.citations
    abstained: generate.abstained
    context: context.context
```

This fragment is not a standalone runnable graph. Answer, citations and abstained are required; context is optional. Bindings must name existing compatible output ports. Missing runtime values cause a traced failure instead of a fabricated successful answer.

Loops execute their declared node order, including conditional skips, after initial node execution and before downstream consumers. Feedback must stay within one declared loop. Overlapping/reordered loops and premature downstream consumers are rejected. Iterations are additional passes after the initial graph pass. Exhaustion forces the declared fail/abstain outcome; abstention clears citations and context. Run manifests include `loop_outcomes` and schema version `1.1.0`.

Authorization denials now persist a safe failed run with no node executions. Deadline checks precede the completed event, preventing a node from being marked both completed and failed for a single deadline overrun. Evidence/candidate port lists validate their element types.

Verified by `tests/test_runtime_v2.py` and the complete deterministic regression suite. This does not yet provide provider cancellation, error-edge recovery, config-schema enforcement or a corrective strategy.
