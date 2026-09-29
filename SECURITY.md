# Security Model

This is a single-admin, local-first reference workbench. It protects the evidence boundary now while modelling
tenant, corpus, document, user, and policy identities for a future authenticated deployment. It is not yet a
multi-tenant or production-hardened security product.

## Current boundary

Protected API routes require `X-Tenant-Id`, `X-User-Id`, and `X-Local-Admin-Token`. Configure
`RAG_WORKBENCH_LOCAL_ADMIN_TOKEN` outside test-only development; the development default is unsuitable for a
shared machine or network.

| Protect | Current control |
| --- | --- |
| Evidence access | Tenant, user, corpus, approval, revision, validity, and applicability filters run before retrieval and generation. |
| Execution | Graph and component schemas validate inputs/outputs; budgets bound tokens, latency, loops, and tools. |
| Provider boundary | Local endpoints are required by default; optional adapters receive only explicitly configured local data. |
| Secrets and traces | Credentials are environment-provided and excluded from traces; manifests contain safe metadata, versions, and identifiers. |
| Future tools | Tool contracts require declared permissions and workspace-only sandbox boundaries. |

When validation or a provider fails, the error is traced explicitly. It must not turn into a silent fallback or
an untraceable answer.

## Limits and operator responsibilities

Keep local service ports on a trusted machine/network, do not commit tokens, and treat source approval and
policy metadata as security-relevant. Multi-user RBAC, tenant isolation enforcement, cloud secret management,
remote perimeter controls, and compliance/audit features remain later work.

Read the detailed [Security guide](docs/security/README.md), [Configuration reference](docs/reference/configuration.md),
and [Definition of Done](docs/definition-of-done/README.md) before extending the boundary.
