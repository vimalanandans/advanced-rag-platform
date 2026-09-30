# ADR-016: Keep stage evidence on failure and version citation parsing

Status: accepted for measurement and source-fidelity parsing; prompt candidate not promoted.

Live generation failures exposed two measurement gaps: completed retrieval disappeared from experiment metrics, and generation settings were absent from configuration fingerprints. Capture each case's terminal manifest through a delegating trace-store wrapper. Persist completed rankings, stage timings and run ID even when a later node fails. Report ranked and completed denominators separately. Fingerprint runtime assets, embedding identity and indexes alongside the strategy and graph.

The source-sentence verifier 1.0.1 accepts an identifier on the immediately following line. It still requires an exact complete normalized sentence from that identified source. Unknown citations, paraphrases and altered qualifiers fail; an orphan citation cannot support a claim. Version 1.0.0 remains registered for old graphs.

A prompt candidate at generation/context 2.0.1 was evaluated after observing a literal placeholder citation. The model then emitted next-line citations, and parser correction alone did not produce consistent gains. Keep 2.0.0 as the default prompt. Retain 2.0.1 as an explicit experimental component and preserve every failed experiment. Do not promote a strategy from these small synthetic cases.
