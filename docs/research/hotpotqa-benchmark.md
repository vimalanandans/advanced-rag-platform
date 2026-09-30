# HotpotQA as the first sourced local retrieval benchmark

The repository's [dataset and corpus reference](../../advanced-rag-datasets-and-corpus.md) lists FlashRAG benchmarks, large Wikipedia/MS MARCO corpora, and a technical PDF collection. For the first reproducible M3 evaluation, select [HotpotQA distractor validation](https://hotpotqa.github.io/) because a single bounded file contains questions, candidate passages, answers, and sentence-level supporting-fact labels. The [official repository](https://github.com/hotpotqa/hotpot/blob/master/README.md) describes its 10-passage distractor setting and CC BY-SA 4.0 license. The original host timed out during TLS negotiation; the [official Hugging Face mirror](https://huggingface.co/datasets/hotpotqa/hotpot_qa) was downloaded at commit `1908d6afbbead072334abe2965f91bd2709910ab`.

| Source property | Verified value |
| --- | --- |
| File | `distractor/validation-00000-of-00001.parquet` |
| SHA-256 | `c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6` |
| Size / rows | 27,452,575 bytes / 7,405 questions |
| License | CC BY-SA 4.0; attribute HotpotQA and preserve share-alike terms for redistribution |
| Local raw path | `.local/corpora/hotpotqa/validation-00000-of-00001.parquet` (Git ignored) |

`python3 scripts/prepare_hotpotqa.py` verifies the source hash and selects the 24 lowest SHA-256 question IDs in each of the bridge and comparison categories. All validation records are labeled `hard`; there is no easy/medium stratum to claim. The resulting 48 cases and 476 passages are stored under ignored `.local/corpora/hotpotqa/benchmark/`. Paragraph IDs include the question ID; each case's allowed-corpus policy restricts retrieval to its own candidate passages. Positive paragraph labels derive from supporting-fact titles, and sentence indexes are validated. The gold answer is kept in case notes for audit, never inserted into evidence. No answers are used in selection. Corpus revision and dataset fingerprint are recorded in local provenance.

The source is a **validation set**, used here as a locked local held-out benchmark. Do not tune generation or retrieval on its labels and call it an independent test. This measures retrieval in the supplied distractor context. It does not measure open-Wikipedia retrieval, document parsing, visual/table/temporal classes, or the full V2 domain. Some questions require short yes/no or inferred answers that the current verbatim sentence verifier cannot emit; report retrieval and answer/abstention separately. A later open-corpus or licensed technical-document benchmark will need its own source, labels, and release.

The separate `scripts/evaluate_hotpotqa_retrieval.py` baseline uses the authorized per-question passage set and persistent BM25. On the pinned 48 cases, recall@5 averaged **0.8125**, MRR averaged **0.8792**, and all labeled supporting paragraphs appeared in the top five for **31/48** questions (bridge 15/24; comparison 16/24). This is retrieval-only development evidence, not a V2 acceptance or improvement claim. Source data, transformed passages, question text and full traces remain outside Git; only aggregate numbers and provenance are committed.

## Local A–F comparison on the locked subset

All six versioned graph arms completed 48/48 cases with the same pinned source, generation/embedding identities, request scope and budget. Case records and traces remain in Git-ignored `.local/corpora/hotpotqa/benchmark/arm-*/`; the [aggregate record](../../experiments/v2-10-hotpotqa-comparison/aggregate.json) contains no questions or passages. The comparison script checks controlled settings and computes a paired, query-class-stratified bootstrap interval for recall differences. These intervals describe variation in this selected sample; they do not establish transfer to open Wikipedia or other document classes.

| Arm | Lanes / ranking | Recall@5 | MRR | All supporting paragraphs in top five | Answer/citation cases passed |
| --- | --- | ---: | ---: | ---: | ---: |
| A | BM25 | 0.8125 | 0.8792 | 31/48 | 0/48 |
| B | Dense | 0.9167 | 0.9444 | 41/48 | 1/48 |
| C | BM25 + dense, RRF | **0.9583** | 0.9167 | **44/48** | 0/48 |
| D | C + structural, RRF | 0.8958 | 0.9035 | 38/48 | 0/48 |
| E | D + local reranker | 0.8958 | 0.9219 | 39/48 | 0/48 |
| F | E + explicit routing | 0.8958 | 0.9219 | 39/48 | 0/48 |

B and C improved recall over A on this fixed distractor subset; C had the highest recall, while B had the highest MRR. D reduced recall compared with C. E promoted one more case to complete support within the top five than D, but mean recall did not improve. F's experimental routing targets identifier/phrase queries, absent from this benchmark, so it produced the same ranking metrics as E. The current model generally abstained after source-sentence verification; HotpotQA often needs multi-document inference or a yes/no answer that the verifier cannot establish from a copied sentence. Do not weaken citation support to raise answer coverage. No arm is promoted, and this does not satisfy the V2 advanced-loop gate.

Latency values in the aggregate are observed per-case runtimes from one sequential pass with changing model/index warmth. They are not controlled comparative latency estimates. Raw source, transformed passages, gold answers and full traces are retained locally for audit, while only aggregate metrics and identities are committed.
