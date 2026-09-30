# ADR-015: Explicit strategy arms and isolated experiment processes

## Status

Accepted for experiment infrastructure; retrieval strategies remain experimental.

## Context

The first V2 milestone requires controlled A–F comparisons and measured reranking/routing. One large pipeline cannot isolate their effects, and peak process memory is misleading if all models/arms share one process.

## Decision

Generate six versioned graph variants with explicit lane, ranking and decision dependencies. Use a local pinned CrossEncoder behind a neutral reranker interface. Retain all lanes in the default graph; F alone uses the declared experimental identifier/phrase policy. Run all-arm comparisons in separate processes, persisting preflight/execution failures as well as results. Include stage rankings, class coverage, abstention and required-claim checks, and never auto-promote a strategy.

## Consequences

A model, its license and M3 envelope still need operator configuration and measured acceptance. Synthetic fixtures validate control flow but cannot justify a quality claim. Unknown policy constraints fail rather than disappear. The comparison runner is an engineering command, not a new API/job service. Advanced corrective/planner behavior remains blocked by the real A–F acceptance gate.
