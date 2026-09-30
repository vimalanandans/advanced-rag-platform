# Qdrant authorized point filtering

Reviewed 2026-09-30. Primary sources: [Qdrant filtering](https://qdrant.tech/documentation/search/filtering/) and [search-point API](https://api.qdrant.tech/master/api-reference/search/points).

Problem: filtering provider results only after top-k can let unauthorized or obsolete points consume the candidate budget. The documented `has_id` filter restricts candidate search to a specified set of point IDs. The adapter now requires the point IDs derived from the runtime-authorized snapshot and supplies that filter in every search request.

Point identity includes evidence content/revision, tenant/policy metadata and embedding configuration; an ID cannot silently refer to another scope or changed content. Empty scope avoids provider work. Unexpected returned IDs fail closed. In-memory shared-index fixtures verify exclusion before top-k and point identity separation; a request-contract test checks the outgoing filter. No latency/recall improvement is claimed from these tests.

Limitations: materializing a large ID set has request-size and latency costs; measure before large-corpus adoption and migrate to equivalent indexed policy predicates when necessary. Compose pins Qdrant 1.11.3; the `has_id` feature exists in historical documentation, but a live check against that image remains required. No model or new dependency/license is introduced. M3 feasibility still depends on Docker integration measurement.
