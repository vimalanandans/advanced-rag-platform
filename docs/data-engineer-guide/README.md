# Data Engineer Guide

Your job is to turn source material into **authorized, revisable evidence**, not merely text chunks. A source
is usable only when a later run can explain where it came from, which revision was selected, and why it was
permitted.

## Evidence contract

Markdown and PDFs are ingested into immutable evidence packages. Each package retains a source URI, document
identifier, revision hash, title, section/page locator, corpus identifier, content type, approval state, tenant,
allowed users, validity window, and applicability tags. This metadata is evaluated before retrieval.

| Preserve | Why it matters |
| --- | --- |
| Source and locator | Lets a user inspect the exact document section or PDF page behind a citation. |
| Revision and validity | Prevents an old or superseded source from being treated as current. |
| Corpus and authorization | Prevents a semantically relevant but disallowed source entering context. |
| Approval and applicability | Separates published/appropriate evidence from draft or out-of-scope material. |

## Prepare a corpus

1. Start with a small, licensed Markdown/PDF fixture and identify questions it must answer or refuse.
2. Ingest it with a stable corpus identifier. The runtime extracts Markdown sections and PDF pages into evidence.
3. Review approval state, allowed users, revision, validity dates, and applicability tags before publishing it.
4. Create golden cases that name expected evidence identifiers and expected abstentions.
5. Run the baseline and inspect citations, omitted context, and lane candidates before changing retrieval.

The current reference release exposes ingestion through the Python API (`ingest_path`) rather than a Studio
upload workflow. Do not document an upload, a corpus editor, or multi-user administration as available until it
exists.

## Choose a retrieval lane from evidence characteristics

| Source/question characteristic | Start with | Measure before adding |
| --- | --- | --- |
| Exact names, codes, citations, or phrasing | BM25 / lexical | Identifier recall and citation correctness |
| Paraphrased concepts | Dense | Candidate recall against expected evidence |
| Long manuals or hierarchical policies | Vectorless structural retrieval | Section/page provenance and context completeness |
| Mixed question types | Fuse multiple lanes with RRF | Per-lane contribution and final citation quality |
| Missing, stale, or conflicting material | Abstain and route to review | False-answer rate and abstention behavior |

Read [Advanced RAG Strategies](../../ADVANCED_RAG_STRATEGIES.md) before adding a capability, then follow the
[Evaluation guide](../evaluation/README.md) and [Definition of Done](../definition-of-done/README.md).
