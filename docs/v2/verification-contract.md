# V2 structural context and verification

The experimental local-real graph now runs classification → exact/BM25/dense/structural → RRF → evidence verification → whole-block context → quoted generation → claim/citation verification. Its explicit terminal returns the verified answer.

## Query classification

The rules produce all twelve specified classes, original query, confidence, required capabilities, recommended lanes, reason, classifier version and fallback. Confidence is heuristic telemetry. The initial safe fallback retains all lanes; this is classification, not an accepted adaptive routing policy. Unsupported visual, typed table, relationship or conversational requirements yield an insufficient-evidence result. No-RAG greetings are classified but do not bypass the evidence-first answer policy.

## Structural evidence

`ingest_structural_path` adds parser version, heading level and parent/child identities to the v1 text blocks without changing the v1 parser. Parent traversal is depth bounded, detects cycles and rejects cross-document/revision chains. Only already-authorized parents can be expanded. PDF remains page text; layout/OCR/table/visual extraction is pending.

## Context

The planner retains complete blocks, including warnings and qualifiers, or omits the entire block. Each decision names evidence ID, token estimate and inclusion/quota/budget reason. Input overhead is budgeted separately, output space reserved, and source quotas explicit. The estimator is `utf8-byte-upper-bound@1.0.0`; reported usage is an estimate, not provider tokenizer telemetry. Model-specific accounting remains outstanding.

## Verification

Multiple eligible revisions of one document are unresolved unless request policy has already selected one. Annotated `conflict_group`/`assertion_value` disagreement is visible and blocks generation. This does not infer arbitrary natural-language contradictions.

The generator requests one complete source sentence and citation ID per line. `verbatim-sentence@1.0.0` checks complete normalized sentence equality and the citation's existence in the selected evidence. Changed warnings, fragments, paraphrases and invented IDs fail closed. Empty output and explicit ABSTAIN abstain. Any failed claim clears delivered citations and returns a verification abstention; claim records remain inspectable in the response.

This checks quoted source fidelity, not source truth, relevance completeness, or unrestricted semantic entailment. Do not market it as calibrated general claim support. A later verifier must have separate identity, fixtures and measured acceptance.

## Citation layout revision

`verification.claims@1.0.1` additionally accepts a citation immediately following its claim on the next line. This changes layout parsing only: the full sentence and actual source ID must still match. The preceding `1.0.0` verifier remains available for replay. Experimental generation/context `2.0.1` clarified citation instructions but did not establish a consistent measured gain; default graphs retain the `2.0.0` prompt. See ADR-016 and `experiments/v2-07-generation`.
