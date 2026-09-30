# Local immutable corpus publication

The local-real runtime can load an explicitly approved Markdown/PDF corpus release. Originals and releases live beneath `<storage>/evidence/<tenant-hash>/`; files are created without overwrite and verified by SHA-256 on read. Parsing uses the saved bytes. A source path changing later cannot alter an existing release.

```bash
python3 scripts/publish_corpus.py stage --corpus manuals manual.md policy.pdf
# Inspect the returned draft ID before approval:
python3 scripts/publish_corpus.py inspect '<draft-id>'
python3 scripts/publish_corpus.py approve '<draft-id>'
# Select the different approved ID in the local-real profile:
export RAG_WORKBENCH_CORPUS_RELEASE='<approved-id>'
```

The commands default to tenant `local`, principal `local-admin` and `.local/evidence`; `--storage` and `--tenant` are explicit CLI options before the subcommand. Runtime loading currently uses the local profile's tenant and `<RAG_WORKBENCH_STORAGE>/evidence`. Without a release ID the existing fixture remains available. Drafts, missing originals, tampered hashes and cross-tenant reads fail closed. No approval is inferred from successful extraction.

A document key is its corpus plus filename. Duplicate filenames in a release are rejected; rename or split the corpus intentionally. Markdown hierarchy links are remapped to immutable evidence IDs; PDF retains page locators. Each original is limited to 20 MiB by default. Source resolution uses a selected approved release and evidence ID, with scope checks; raw object hashes are not a public source-read interface.

The store is for trusted local administration. It does not sandbox PDF parsing or expose a network upload endpoint. Empty/scanned PDFs without extracted text fail staging. OCR, durable jobs, source retention/garbage collection, selective ACL editing and atomic index-build promotion are still pending. A corpus release pins source material; it does not certify retrieval quality or model/index compatibility. See ADR-017.

Validation covers deterministic staging, immutable revisions, explicit approval, database-free reopen, original resolution, scope/revision rejection, invalid formats, size bounds, duplicate IDs, content tampering and generated PDF page extraction. A checked-in Markdown fixture was staged and approved through the CLI and passed into a real-model runtime smoke run; answer-quality acceptance remains separate.
