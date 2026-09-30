# V2 synthetic evaluation fixtures

`corpus.json` contains original fictional evidence and policy metadata; `dataset.json` contains 22 versioned cases across five isolated split groups and all twelve query classes. Source URIs identify synthetic fixtures rather than external authoritative documents. Content follows the repository license.

These fixtures test experiment contracts and policy/verification behavior. They are not a representative production benchmark, a measured semantic retrieval improvement, or a model recommendation. Corpus fingerprints include policy metadata. Any edit requires a new dataset/corpus release before comparing historical results.

Use the [comparison command](../../docs/v2/strategy-comparison.md) with a pinned request timestamp; the adversarial obsolete document expires before that time. Real model/services must be configured. Do not use fixture-only or hashed embeddings as arm B and call them semantic results.
