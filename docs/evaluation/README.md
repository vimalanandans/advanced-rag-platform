# Evaluation Guide

Evaluation answers one question: **does this measured change improve the evidence-selection system without
weakening trust, reproducibility, or bounds?** It is not a model popularity contest and it is not a one-off
demo review.

## Baseline dataset

Golden cases live in `data/golden/` and are versioned with the pipeline. Each case records a stable ID,
question, expected evidence IDs, and whether the correct outcome is abstention. Run the checked-in baseline:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

or call `POST /evaluations/baseline` with the normal local-admin request scope. Record the resulting pipeline
fingerprint alongside comparison results.

## What to measure

| Dimension | Question | Evidence to retain |
| --- | --- | --- |
| Retrieval | Did at least one approved expected item reach the candidate set? | Lane, rank, score, corpus/revision filters |
| Citation | Does the answer cite the exact authorized evidence that supports it? | Citation IDs and source locators |
| Abstention | Does the pipeline refuse when evidence is absent, disallowed, or insufficient? | Expected and actual abstention outcome |
| Context | Did the relevant evidence fit without hiding qualifiers or exceeding the budget? | Included/omitted IDs and token use |
| Runtime | Is the quality gain worth the latency and token/tool cost? | Run manifest, component timings, budget use |
| Reproducibility | Can the result be repeated with the same graph/data/provider profile? | Graph fingerprint, versions, index revision, model version |

## Change protocol

1. State the observed baseline gap and the affected question/source class.
2. Add or update deterministic cases before tuning the new strategy.
3. Compare the new graph against the same cases and retain both fingerprints.
4. Inspect failures by lane, source policy, context packing, citation, and abstention—not just aggregate pass count.
5. Add the evaluation guidance, telemetry, and acceptance evidence required by the
   [Definition of Done](../definition-of-done/README.md).

Keep tuning data separate from held-out regression cases. Do not promote a strategy merely because it improves
a single metric while degrading citations, policy enforcement, cost, or abstention.
