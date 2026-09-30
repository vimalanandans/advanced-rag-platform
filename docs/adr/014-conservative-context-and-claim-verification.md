# ADR-014: Conservative structural context and claim verification

## Status

Accepted for the experimental V2 graph; representative quality acceptance pending.

## Context

Heading overlap did not preserve parent context. Generation truncated excerpts and attached citations without checking claims. A permissive semantic verifier would require calibration data not yet available.

## Decision

Add a versioned structural parser and bounded parent traversal within the authorized snapshot. Keep v1 ingestion unchanged. Classify twelve query classes with transparent rules, preserving the original and a safe all-lane fallback. Missing visual/table/relationship/conversation capabilities force insufficient evidence rather than pretending text retrieval supplies them.

Pack whole evidence blocks with byte-based conservative token estimates, explicit source quotas and omission reasons. Detect unresolved multiple revisions of one source and explicitly annotated conflicting assertions. Generate complete quoted source sentences and validate each line against a real cited source sentence. Any unsupported line abstains; unsupported text is not returned as a verified answer. Bind the graph terminal to claim verification, never raw generation.

## Consequences

This is extractive source-fidelity checking, not general semantic entailment or a guarantee that the source is true. Paraphrases, malformed citations and changed qualifiers abstain. Structural PDF hierarchy and inferred semantic contradictions remain unimplemented. Routing does not suppress lanes until measured comparisons justify it. Trace decisions omit raw query and claim text; API results expose authorized claim details. No general evidence-sufficiency quality threshold is claimed.
