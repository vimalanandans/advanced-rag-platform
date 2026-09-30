# Observability Guide

Observability is a product feature: an answer is not trustworthy if an operator cannot reconstruct why the
pipeline selected its evidence or why it failed.

## What every run records

Each immutable run manifest contains the run and trace IDs, tenant/user scope, pipeline version and graph
fingerprint, component versions, selected model/provider identity, index revision, token use, node execution
events, final status, and failure reason. Node events retain safe counts and types, not raw document content or
credentials.

| Inspect | Use it to answer |
| --- | --- |
| Graph fingerprint and versions | Did this run use the graph and component set we intended? |
| Node status and duration | Where did execution slow, skip, or fail? |
| Retrieval candidates and citations | Which lane found the cited evidence? |
| Context plan and token use | What fit, what was omitted, and did the budget constrain the result? |
| Status and error | Did a selected provider or bounded operation fail visibly? |

## Storage behavior

`TraceStore` is a provider-neutral boundary. Unit tests use memory; a local process with
`RAG_WORKBENCH_STORAGE` uses atomic JSON manifests; Compose uses PostgreSQL JSONB manifests. Database storage
takes precedence when both settings are present. See [Configuration](../reference/configuration.md) for exact
settings.

Never log secrets, raw credentials, or evidence the current request is not authorized to see. When debugging a
bad answer, start with the manifest, source locator, policy filter, lane candidates, and context plan—not a
full prompt dump.


## Terminal-record immutability

Identical terminal writes are idempotent; a different record under an existing run ID raises `TraceConflictError`. JSON publishes atomically without replacing files and rejects non-UUID path components. Memory returns defensive copies. PostgreSQL uses insert-on-conflict-do-nothing and verifies equality; live database acceptance is still outstanding. Error traces retain error type and a safe category, not arbitrary provider exception messages.
