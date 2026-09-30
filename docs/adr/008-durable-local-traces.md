# ADR-008: Durable Trace Storage With Local and PostgreSQL Adapters

## Status

Accepted

## Context

Run manifests must survive API restarts and remain inspectable by the Studio without binding the runtime to one storage vendor.

## Decision

Use the `TraceStore` contract. Unit tests retain an in-memory store, local development without a database uses atomic JSON manifests, and Docker Compose uses PostgreSQL JSONB manifests.

## Consequences

Runtime contracts stay provider-neutral while local runs become durable. Object-backed evidence packages remain a separate future adapter.
