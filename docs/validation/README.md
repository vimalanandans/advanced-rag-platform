# Validation Guide

Validation answers whether a pipeline is safe and meaningful to execute. It happens before runtime work begins;
it is not a substitute for evaluation after the run.

## Compiler checks

The graph compiler validates:

1. Pipeline schema and semantic version.
2. Unique nodes, known component references, and component capability manifests.
3. Typed input/output ports and every declared data/control/error/feedback dependency.
4. Graph ordering, conditional expressions, and cycles.
5. Declared loop exit condition, iteration/time/token/tool limits, fallback, and tracing.
6. Pipeline and component budget compatibility.

Call `POST /pipelines/validate` to obtain a validated execution order and graph fingerprint for the checked-in
baseline. A `422` response means the graph cannot be run; correct the declarative pipeline or component
manifest rather than relying on runtime fallback behavior.

## Validation is not acceptance

A valid graph can still retrieve the wrong source, omit a crucial qualifier, exceed a practical latency target,
or abstain incorrectly. After validation, run deterministic fixtures and inspect the trace. Use the
[Evaluation guide](../evaluation/README.md) and [Definition of Done](../definition-of-done/README.md) as the
acceptance gates.
