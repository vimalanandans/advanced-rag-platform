# Security Model

The reference release is single-admin and local-first. It still models tenant, corpus, document, user,
and policy identities so authenticated multi-tenant deployment does not require a domain rewrite.

The local API requires `X-Tenant-Id`, `X-User-Id`, and `X-Local-Admin-Token` for pipeline runs,
evaluation, and trace access. Configure `RAG_WORKBENCH_LOCAL_ADMIN_TOKEN`; the development-only
default is intentionally unsuitable for a shared deployment.

- Evidence access, revision, freshness, and applicability filters run before ranking and generation.
- Tool contracts require declared permissions and workspace-only sandbox boundaries.
- Secrets are supplied through environment variables and are never emitted in trace attributes.
- Trace data contains safe metadata, versions, and evidence identifiers; viewers must enforce future ACLs.
- Inputs and component outputs are schema-validated. Failed validation is an explicit, traced error.
- Cloud providers/exporters are adapters; they receive only explicitly configured, redacted data.
