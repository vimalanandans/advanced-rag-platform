# Advanced RAG Strategies — Datasets and Document Corpus

This reference defines the datasets, document collections, and indexes used by the Advanced RAG Learning Lab. It is written for learners first: begin with the dataset concepts and schema, then move to corpus construction and retrieval indexes.

## 1. Source references

- [FlashRAG datasets on Hugging Face](https://huggingface.co/datasets/RUC-NLPIR/FlashRAG_datasets) — prepared benchmark datasets for retrieval-augmented generation experiments.
- [Technically-oriented PDF Collection](https://github.com/tpn/pdfs/tree/master) — a broad collection of technical papers, specifications, manuals, and presentation material suitable for document-ingestion and retrieval experiments.
- [FlashRAG documentation and corpus-processing references](https://github.com/RUC-NLPIR/FlashRAG) — implementation context, preprocessing guidance, and experiment conventions.

These sources are references, not an unrestricted redistribution license. Before shipping any downloaded document or dataset, check its original license, attribution requirements, usage restrictions, and whether it contains personal or copyrighted material.

## 2. Datasets

FlashRAG reports 36 datasets commonly used in RAG research and provides them in a consistent format. Some datasets, including WikiASP, were adapted for RAG-style tasks according to common research practices. Treat dataset transformations as part of the provenance record: preserve the source name, transformation, version or commit, and license.

The prepared dataset is available from [RUC-NLPIR/FlashRAG_datasets](https://huggingface.co/datasets/RUC-NLPIR/FlashRAG_datasets).

### 2.1 Canonical record format

Each split is stored as JSON Lines (`.jsonl`), one JSON object per line:

```json
{
  "id": "example-id",
  "question": "What is retrieval-augmented generation?",
  "golden_answers": ["A method that retrieves evidence before generation."],
  "metadata": {"source": "example-dataset", "split": "test"}
}
```

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | string | Stable identifier for the example. |
| `question` | string | User-style question or task input. |
| `golden_answers` | array of strings | One or more accepted reference answers. |
| `metadata` | object | Dataset-specific provenance and task information. |

### 2.2 Dataset inventory

Counts below are the published sample sizes in the source material. `/` means that a split is not provided or is not applicable.

| Task | Dataset | Knowledge source | Train | Dev | Test |
| --- | --- | --- | ---: | ---: | ---: |
| QA | NQ | Wikipedia | 79,168 | 8,757 | 3,610 |
| QA | TriviaQA | Wikipedia and web | 78,785 | 8,837 | 11,313 |
| QA | PopQA | Wikipedia | / | / | 14,267 |
| QA | SQuAD | Wikipedia | 87,599 | 10,570 | / |
| QA | MSMARCO-QA | Web | 808,731 | 101,093 | / |
| QA | NarrativeQA | Books and stories | 32,747 | 3,461 | 10,557 |
| QA | WikiQA | Wikipedia | 20,360 | 2,733 | 6,165 |
| QA | WebQuestions | Google Freebase | 3,778 | / | 2,032 |
| QA | AmbigQA | Wikipedia | 10,036 | 2,002 | / |
| QA | SIQA | — | 33,410 | 1,954 | / |
| QA | CommonSenseQA | — | 9,741 | 1,221 | / |
| QA | BoolQ | Wikipedia | 9,427 | 3,270 | / |
| QA | PIQA | — | 16,113 | 1,838 | / |
| QA | Fermi | Wikipedia | 8,000 | 1,000 | 1,000 |
| Multi-hop QA | HotpotQA | Wikipedia | 90,447 | 7,405 | / |
| Multi-hop QA | 2WikiMultiHopQA | Wikipedia | 15,000 | 12,576 | / |
| Multi-hop QA | MuSiQue | Wikipedia | 19,938 | 2,417 | / |
| Multi-hop QA | Bamboogle | Wikipedia | / | / | 125 |
| Multi-hop QA | StrategyQA | Wikipedia | 2,290 | / | / |
| Long-form QA | ASQA | Wikipedia | 4,353 | 948 | / |
| Long-form QA | ELI5 | Reddit | 272,634 | 1,507 | / |
| Long-form QA | WikiPassageQA | Wikipedia | 3,332 | 417 | 416 |
| Open-domain summarization | WikiASP | Wikipedia | 300,636 | 37,046 | 37,368 |
| Multiple choice | MMLU | — | 99,842 | 1,531 | 14,042 |
| Multiple choice | TruthfulQA | Wikipedia | / | 817 | / |
| Multiple choice | HellaSwag | ActivityNet | 39,905 | 10,042 | / |
| Multiple choice | ARC | — | 3,370 | 869 | 3,548 |
| Multiple choice | OpenBookQA | — | 4,957 | 500 | 500 |
| Multiple choice | QuaRTz | — | 2,696 | 384 | 784 |
| Fact verification | FEVER | Wikipedia | 104,966 | 10,444 | / |
| Dialog generation | WoW | Wikipedia | 63,734 | 3,054 | / |
| Entity linking | AIDA-CoNLL-YAGO | Freebase and Wikipedia | 18,395 | 4,784 | / |
| Entity linking | WNED | Wikipedia | / | 8,995 | / |
| Slot filling | T-REx | DBpedia | 2,284,168 | 5,000 | / |
| Slot filling | Zero-shot RE | Wikipedia | 147,909 | 3,724 | / |
| In-domain QA | DomainRAG | RUC web pages | / | / | 485 |

## 3. Document corpus

The retrieval corpus is also JSON Lines. Each line is a document record:

```json
{"id": "0", "contents": "Document title\nDocument text"}
{"id": "1", "contents": "Another document"}
```

The `contents` field is the indexing payload. Include title and body as `title\ntext` when both exist. Preserve optional `title`, `metadata`, source, license, date, and section fields for display, filtering, and citations.

For every corpus build, record the source URL or exact revision, retrieval date, parser and cleaning version, chunking parameters, license, language, and whether the text was transformed, truncated, or deduplicated.

## 4. Common research corpora

Wikipedia and MS MARCO are widely used retrieval collections in RAG research.

- Use the [FlashRAG Wikipedia processing guide](https://github.com/RUC-NLPIR/FlashRAG/blob/e82f680b5a3fce1349bf818c249857d14b83516a/docs/original_docs/process-wiki.md) to process a dump into a clean corpus.
- MS MARCO is available as the [Tevatron MS MARCO passage corpus](https://huggingface.co/datasets/Tevatron/msmarco-passage-corpus).
- The [tpn/pdfs collection](https://github.com/tpn/pdfs/tree/master) is useful for heterogeneous technical-document ingestion. Use a curated, licensed subset for demos rather than indexing the repository indiscriminately.

## 5. Indexes

A preprocessed index is available from the [FlashRAG Dataset ModelScope page](https://www.modelscope.cn/datasets/hhjinjiajie/FlashRAG_Dataset/file/view/master?id=47985&status=2&fileName=retrieval_corpus%252Fwiki18_100w_e5_index.zip): `retrieval_corpus/wiki18_100w_e5_index.zip`.

The published index was created with the `e5-base-v2` retriever over the `wiki18_100w` dataset. An index is coupled to its corpus, embedding model, preprocessing, distance metric, and configuration; it is not a universal default.

## 6. How this supports the learning app

Each lesson should show: question → retrieval strategy → retrieved chunks and scores → provenance → context assembly → grounded answer → evaluation trade-offs. The first implementation should use small, deterministic, licensed fixtures derived from these references. Full benchmark downloads belong in an explicit ingestion workflow and should not be committed to the application repository.

## 7. Citation and reproducibility checklist

- Cite the dataset and original task source.
- Record the exact dataset revision or release date.
- Record preprocessing, chunking, embedding, reranking, and index settings.
- Keep train, development, and test data separated; do not tune against test data.
- Preserve document-level citations in generated answers.
- Review licensing and privacy before redistribution.
