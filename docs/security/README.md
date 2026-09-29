# Security Guide

The reference release is a **single-admin local workbench**, not a multi-tenant security product. Its security
model protects the evidence boundary now and preserves the contracts needed to add stronger authentication and
authorization later.

## Current controls

| Control | Current behavior |
| --- | --- |
| Local-admin scope | Protected API routes require a configured local-admin token and `local-admin` user identity. |
| Evidence authorization | Tenant, user, corpus, revision, validity window, approval state, and applicability filters run before retrieval. |
| Provider locality | Provider URLs reject remote endpoints by default; local Qdrant/Ollama are optional adapters. |
| Safe traces | Run manifests capture safe metadata and errors, not raw secrets, credentials, or unauthorized evidence. |
| Bounded execution | Context, output, total tokens, latency, loops, and tool calls have declared limits. |
| Explicit tools | Future tools must be permissioned and workspace-sandboxed; no implicit agent tool access is allowed. |

## Operator responsibilities

- Set a non-default `RAG_WORKBENCH_LOCAL_ADMIN_TOKEN` outside test-only development and do not commit it.
- Keep local provider and trace-storage ports on a trusted machine or network.
- Treat source approval, allowed users, corpus policy, and revision metadata as security-relevant data.
- Review traces by identifier and locator; do not add raw prompt or evidence logging to diagnose an issue.

## Not yet provided

Authenticated multi-user RBAC, tenant isolation enforcement, remote secret management, cloud perimeter controls,
and production audit/compliance controls are later extensions. Do not represent this reference workbench as
production-hardened or multi-tenant until those capabilities are implemented and separately accepted.

See [Configuration](../reference/configuration.md), [Architecture](../architecture/system.md), and the
[Definition of Done](../definition-of-done/README.md) for implementation constraints.
