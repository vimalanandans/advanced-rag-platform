# V2 evaluation and experiment specification

Status: specified. Existing `evaluate()` checks expected citation inclusion and abstention for two golden cases. It does not calculate the metrics below. The new fixture experiment runner measures ranked candidate IDs separately and persists versioned artifacts. It does not replace that endpoint or implement local-real A–F comparisons. No V2 retrieval gain has been demonstrated yet.

## Dataset contract and governance

Version immutable corpus snapshots, case files and a dataset manifest containing license/provenance, split membership, content hashes, query/content-class coverage, annotation instructions and reviewer decisions. Required case fields: `case_id`, `query`, `query_class`, `corpus_revision`, `expected_evidence_ids`, `hard_negative_ids`, `expected_claims`, `expected_abstention`, `policy_constraints`, `notes`. Add graded relevance and claim-to-evidence labels where required.

Separate development, tuning, held-out evaluation, adversarial and regression sets. Split by document family/revision and question variants, not random near-duplicate rows. Detect duplicate IDs/content and overlapping source groups before accepting a split. Freeze held-out labels and thresholds before comparing candidates; inspecting held-out failures for tuning requires a new held-out release. Small deterministic fixtures establish correctness, not general retrieval quality.

Representative cases cover exact identifiers/phrases, paraphrases, comparisons, long documents, tables, procedures, warnings, visual/relationship/multi-hop queries, conflicting/obsolete/effective-dated sources, insufficient/unauthorized evidence and malformed input. Unsupported content classes must produce an explicit unsupported/abstaining result instead of invented support. Include multiple principals, corpora, applicability scopes and shared-index hard negatives.

## First V2 experiment

Use identical authorized corpus and split, generation model/prompt, evidence/context/claim verifier, output limits and measurement method for each arm. Pin all identities. Record cold-index build separately from warm-query timing; alternate arm order and repeat timing runs. Differences in budgets must be intentional and visible.

| Arm | Candidate strategy | Question answered |
| --- | --- | --- |
| A | Persistent BM25 only | How strong is lexical recall? |
| B | Real dense embeddings only | Which semantic cases improve or fail? |
| C | BM25 + dense + RRF | Does fusion improve coverage? |
| D | C + structural retrieval + RRF | Does hierarchy recover missing context? |
| E | D + reranker | Does ranking improve at acceptable latency and coverage? |
| F | E + query-class routing | Can routing reduce work without losing evidence? |

A classifier in F must retain the original query, log its class/reason/fallback and account for misrouting. A reranker cannot recover evidence missing from its input; compare candidate recall before reranking as well as final rank quality. Preserve deterministic fixtures separately: hash vectors must never be presented as arm B semantic results.

## Stage metrics and edge cases

| Stage | Metrics and interpretation |
| --- | --- |
| Retrieval | Recall@K = relevant retrieved / relevant expected; Precision@K = relevant retrieved / K (missing slots count as nonrelevant); MRR = reciprocal first relevant rank; nDCG@K uses graded gains and ideal ordering. Deduplicate evidence IDs before ranking metrics. Report K and label completeness. |
| Exact retrieval | Identifier recall, phrase fidelity, normalization/alias failures, hard-negative rejection and per-lane unique contribution |
| Evidence | Authorization, approval, revision, applicability, effective date/freshness correctness; conflict detection precision/recall; any policy leak is a hard failure |
| Context | Required evidence retained, qualifiers/units/warnings preserved, source diversity, duplication, omission reasons, actual/estimated tokens and budget compliance |
| Answer | Claim support, citation precision (supported claim-citation links / emitted links), citation coverage (material claims with support / material claims), unsupported-claim rate, contradictory claims |
| Abstention | Expected abstentions correctly refused; false-abstention rate on answerable cases; unsafe answers on unanswerable cases. Report these separately. |
| Runtime | Per-stage and total latency, p50/p95 across repeats, input/output/context/reasoning tokens, CPU, peak memory, model/index runtime, retries, model/tool calls and loop iterations |
| Reproducibility | Pipeline/strategy/component/prompt/model/embedding/index/parser/chunker/corpus/dataset/policy identities plus configuration fingerprint and hardware/software profile |

Cases without expected relevant evidence have undefined recall/MRR/nDCG: store `null` with a reason and exclude them from those averages, while retaining abstention/policy scores. An answer with zero claims or citations does not receive perfect answer-quality credit automatically. Missing labels or unsupported metrics are `null`, never silently zero or one. Report metric denominators, failures and coverage per query/content class; aggregate numbers alone are insufficient.

Deterministic source/locator/revision and identifier checks take precedence where applicable. Semantic claim judgments require a documented verifier plus human calibration labels; model confidence is not a truth score. Persist raw measurement method/version and repeat count. Use paired per-case comparisons and uncertainty intervals when sample size supports them; do not claim significance from two examples.

## Acceptance and rejection

Set quality/latency/memory thresholds from the baseline and hardware envelope before candidate evaluation. Require zero policy violations in the adversarial fixture suite, no lost critical warning/qualifier, resolvable citations, correct exhaustion/abstention, and reproducible case outputs. Promotion needs a documented improvement on a named problem class without unacceptable regressions or resource cost. A ranking gain cannot compensate for reduced necessary evidence coverage.

Persist baseline and candidate records even on failure. Record `accept`, `reject` or `iterate`, reasons, owner, limitations and rollback target. Agentic/corrective retrieval cannot begin until A–F experiments are reproducible. A failed or incomplete arm is reported as such, not excluded to improve aggregate results.

## Experiment artifacts

Use `experiments/<experiment-id>/` for immutable hypothesis/configuration, dataset/split references, fingerprints, case outputs, metrics, failures and decision. Sensitive queries/evidence stay in access-controlled local artifacts; commit only approved fixtures and safe summaries. Use the [engineering-loop template](../../experiments/templates/engineering-loop.json) to retain work evidence outside chat. Restart/cancel must preserve terminal experiment status and completed case records.

An experiment is reproducible only when referenced corpus/index/model assets remain available. Fingerprints alone do not recreate deleted assets.


## Sourced benchmark input

[HotpotQA benchmark provenance and scope](../research/hotpotqa-benchmark.md) documents the first downloaded, pinned corpus and its retrieval-only BM25 baseline. It covers hard multi-hop and comparison questions in the distractor setting. Other V2 content/query classes need independent sourced evaluation before broad quality acceptance.
