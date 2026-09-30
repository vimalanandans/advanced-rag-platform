# ADR-010: Incremental V2 evolution and measured promotion

## Status

Accepted for specification and implementation sequencing; runtime capabilities remain subject to their acceptance gates.

## Context

The current graph/registry/local-provider foundations support incremental evolution, while retrieval, verification and evaluation implementations are intentionally small. Replacing the platform would discard useful contracts and fixtures without resolving their measured gaps. The V2 brief requires a strong local baseline before adaptive retrieval.

## Decision

Retain the platform-owned graph IR, registry boundary, provider-neutral contracts and deterministic profile. Specify a separate local-real profile, versioned strategy/dataset/experiment records, explicit claim verification and an A–F baseline comparison. Require authorization inside indexed candidate selection and on every corrective action. Introduce advanced-research only after the baseline is reproducible. Target Apple Silicon M3 with Docker Desktop and optional native local model serving.

## Consequences

Existing artifacts remain readable; changed behavior gets new versions and index migration. Reranking, classification and claim verification enter the first V2 milestone. Model and provider choices remain pending measured feasibility and licensing research. No new dependency, service, or research technique is accepted by this ADR alone. Rollback restores a compatible previous strategy/graph/model/index/corpus release. See the [migration plan](../v2/migration-plan.md).
