# ADR-017: Immutable local originals and explicit corpus releases

Status: accepted for local-admin publication; index-release promotion remains separate.

Parsing a file must not approve it or depend on bytes that can change after fingerprinting. Store originals in a tenant-separated content-addressed directory before parsing a temporary snapshot. Remap all evidence and hierarchy IDs to stable document/revision/locator identities. Keep full original hashes and parser/chunker/policy versions in the release.

Staging produces an immutable review-required release. Approval creates a different immutable release; it never rewrites the draft. The runtime selects an explicit approved release ID, validates release/original integrity and retains that ID in manifests. There is no mutable latest pointer. Rollback selects a prior approved compatible release; vector identities already bind content and embedding configuration.

Only the authenticated local administrator contract is supported. Source resolution checks the selected release, corpus, tenant, evidence identity, validity, revision and applicability. Local filesystem administration remains trusted. No remote upload, parser sandbox, multi-user approval workflow, garbage collection, durable ingestion queue or atomic index-build promotion is claimed. Unreferenced original objects may remain after failed staging and are retained rather than deleted automatically.
