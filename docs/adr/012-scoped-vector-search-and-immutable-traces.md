# ADR-012: Scope vector candidates before selection and preserve terminal records

## Status

Accepted for implementation; live Qdrant/PostgreSQL integration remains unverified.

## Context

Shared Qdrant collections can retain points outside a request's authorized snapshot. Post-filtering cannot prevent them from consuming top-k. Trace adapters allowed replacement of terminal manifests and retained arbitrary exception text.

## Decision

Require `allowed_point_ids` at the VectorIndex search boundary and translate it to a Qdrant ID filter before ranking. Derive point identity from evidence content, revision, scope/policy metadata and embedding configuration. Skip empty-scope searches and reject out-of-scope results. Existing old points need not be destructively removed; they are ineligible under the new identities.

Make terminal stores idempotent for identical writes and reject conflicting writes. JSON uses atomic no-overwrite publication and validates UUID path components; memory returns copies; PostgreSQL inserts without conflict updates then compares the stored record. Persist error class and a safe description instead of arbitrary provider exception text.

## Consequences

Custom vector adapters must implement the new required scope parameter; an adapter that ignores it is invalid. A provider returning an unexpected point fails rather than silently dropping it. Large authorized ID sets need measured scaling work. Existing traces remain readable; no destructive schema migration occurs. Live database concurrency and provider operation require separate acceptance. Raw errors are available to callers for debugging but never copied into run manifests.
