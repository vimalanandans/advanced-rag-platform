# Developer Guide

Implement components against provider-neutral typed contracts; register a capability manifest, add telemetry,
tests, documentation, and evaluation guidance. Start with [System Architecture](../architecture/system.md),
[Configuration](../reference/configuration.md), and the [Definition of Done](../definition-of-done/README.md).

## Git workflow

Keep `main` as the integration branch. Create a short `ai-coding/<topic>` branch for each focused change,
commit the verified change, and open a pull request to `main`. The `verify` workflow checks pull requests
and changes to `main`; ordinary feature-branch pushes and tags do not start duplicate runs. Merge after
the required checks pass, then delete the short branch. Create an annotated version tag on `main` only
for a reviewed release checkpoint. Keep downloaded corpora, transformed passages, question text, and
full traces under ignored `.local/`; commit the download/preparation scripts, pinned provenance, and
text-free aggregate metrics needed to reproduce an experiment.
