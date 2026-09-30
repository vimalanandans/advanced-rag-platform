"""Pin and prepare a local HotpotQA distractor benchmark without committing source data."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rag_workbench.contracts import Evidence
from rag_workbench.experimentation import DatasetManifest, ExperimentCase, corpus_fingerprint

SOURCE_REVISION = "1908d6afbbead072334abe2965f91bd2709910ab"
SOURCE_SHA256 = "c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6"
SOURCE_URL = f"https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/{SOURCE_REVISION}/distractor/validation-00000-of-00001.parquet"
SOURCE_FILENAME = "validation-00000-of-00001.parquet"


def verified_hash(path: Path, expected: str) -> None:
    digest = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != expected:
        raise ValueError("HotpotQA source checksum mismatch")


def download(path: Path, *, expected: str = SOURCE_SHA256) -> Path:
    if path.exists():
        verified_hash(path, expected)
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    try:
        request = Request(SOURCE_URL, headers={"User-Agent": "advanced-rag-platform local research"})
        digest = sha256()
        size = 0
        with urlopen(request, timeout=60) as response, temporary.open("wb") as output:
            for block in iter(lambda: response.read(1024 * 1024), b""):
                size += len(block)
                if size > 100_000_000:
                    raise ValueError("HotpotQA download exceeds 100 MB bound")
                digest.update(block)
                output.write(block)
        if digest.hexdigest() != expected:
            raise ValueError("HotpotQA source checksum mismatch")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def prepare(path: Path, output: Path, *, expected_sha256: str = SOURCE_SHA256,
            per_stratum: int = 24) -> dict:
    if per_stratum <= 0:
        raise ValueError("per-stratum count must be positive")
    verified_hash(path, expected_sha256)
    from pyarrow import parquet
    table = parquet.read_table(path)
    if not {"id", "question", "answer", "type", "level", "context", "supporting_facts"} <= set(table.column_names):
        raise ValueError("HotpotQA schema is incomplete")
    strata = defaultdict(list)
    for row in table.to_pylist():
        if row["type"] in {"bridge", "comparison"} and row["level"] == "hard":
            strata[(row["type"], row["level"])].append(row)
    chosen = []
    for key in sorted(strata):
        rows = sorted(strata[key], key=lambda row: sha256(row["id"].encode()).hexdigest())
        if len(rows) < per_stratum:
            raise ValueError(f"HotpotQA stratum {key} has too few records")
        chosen.extend(rows[:per_stratum])
    if len(chosen) != 2 * per_stratum:
        raise ValueError("HotpotQA hard comparison/bridge strata are incomplete")
    evidence, cases = [], []
    for row in chosen:
        question_id = row["id"]
        corpus_id = "hotpotqa-" + question_id
        contexts = row["context"]
        titles, sentences = contexts["title"], contexts["sentences"]
        if len(titles) != len(sentences) or len(set(titles)) != len(titles):
            raise ValueError("HotpotQA context titles are ambiguous")
        supports = row["supporting_facts"]
        support_titles = set(supports["title"])
        if len(supports["title"]) != len(supports["sent_id"]):
            raise ValueError("HotpotQA supporting facts are invalid")
        by_title = {}
        for index, (title, lines) in enumerate(zip(titles, sentences)):
            if not title or not lines or not any(line.strip() for line in lines):
                raise ValueError("HotpotQA passage is empty")
            identifier = f"hotpotqa:{question_id}:{index}"
            by_title[title] = identifier
            evidence.append(Evidence(
                id=identifier, document_id=identifier,
                source_uri=f"hotpotqa://distractor/{question_id}/{index}",
                revision=expected_sha256, title=title, locator=f"paragraph:{index}",
                content=title + "\n" + " ".join(line.strip() for line in lines),
                tenant_id="local", allowed_users=["local-admin"], approval_state="approved",
                metadata={"corpus_id": corpus_id, "content_type": "markdown", "source_dataset": "HotpotQA distractor validation",
                          "source_revision": SOURCE_REVISION, "source_sha256": expected_sha256,
                          "sentence_count": len(lines), "license": "CC-BY-SA-4.0"},
            ))
        if not support_titles or not support_titles <= set(by_title):
            raise ValueError("HotpotQA supporting paragraph is absent")
        for title, sentence_index in zip(supports["title"], supports["sent_id"]):
            if sentence_index < 0 or sentence_index >= len(sentences[titles.index(title)]):
                raise ValueError("HotpotQA supporting sentence index is invalid")
        positive = sorted(by_title[title] for title in support_titles)
        cases.append(ExperimentCase(
            case_id="hotpotqa-" + question_id, query=row["question"],
            query_class="comparison" if row["type"] == "comparison" else "multi_hop",
            corpus_revision="placeholder", source_group=question_id, split="held_out",
            expected_evidence_ids=positive, relevance={identifier: 1 for identifier in positive},
            policy_constraints={"allowed_corpora": [corpus_id]},
            notes=f"HotpotQA {row['type']}/{row['level']}; answer label retained outside runtime: {row['answer']}",
        ))
    revision = corpus_fingerprint(evidence)
    for case in cases:
        case.corpus_revision = revision
    dataset = DatasetManifest(dataset_id="hotpotqa-distractor-local", version="1.0.0",
                              corpus_revision=revision, provenance=f"{SOURCE_URL} sha256:{expected_sha256}",
                              license="CC-BY-SA-4.0", cases=cases)
    output.mkdir(parents=True, exist_ok=True)
    (output / "corpus.json").write_text(json.dumps([item.model_dump(mode="json") for item in evidence], indent=2) + "\n")
    (output / "dataset.json").write_text(dataset.model_dump_json(indent=2) + "\n")
    manifest = {"source_url": SOURCE_URL, "source_revision": SOURCE_REVISION, "source_sha256": expected_sha256,
                "source_rows": table.num_rows, "selected_cases": len(cases), "passages": len(evidence),
                "strata": {f"{kind}/{level}": per_stratum for kind, level in sorted(strata)},
                "corpus_revision": revision, "dataset_fingerprint": dataset.fingerprint,
                "license": "CC-BY-SA-4.0", "setting": "question-scoped 10-passage distractor retrieval",
                "selection": "lowest SHA-256(question ID) per type; all validation rows are hard; no answer-based selection",
                "transformation": "title plus original sentences; paragraph-level labels from supporting facts; no answer text in evidence"}
    (output / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / ".local/corpora/hotpotqa" / SOURCE_FILENAME)
    parser.add_argument("--output", type=Path, default=ROOT / ".local/corpora/hotpotqa/benchmark")
    parser.add_argument("--per-stratum", type=int, default=24)
    args = parser.parse_args()
    download(args.source)
    print(json.dumps(prepare(args.source, args.output, per_stratum=args.per_stratum), indent=2))


if __name__ == "__main__":
    main()
