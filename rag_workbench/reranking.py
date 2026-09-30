"""Bounded local reranking behind a provider-neutral interface."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Protocol

from rag_workbench.contracts import RetrievalCandidate


def model_fingerprint(directory: Path) -> str:
    if not directory.is_dir():
        raise ValueError("reranker model must be an existing local directory")
    files = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.name != ".DS_Store":
            digest = hashlib.sha256()
            with path.open("rb") as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(block)
            files.append((path.relative_to(directory).as_posix(), digest.hexdigest()))
    if not files:
        raise ValueError("reranker model directory is empty")
    return hashlib.sha256(json.dumps(files, separators=(",", ":")).encode()).hexdigest()


class Reranker(Protocol):
    identity: str
    def rerank(self, query: str, candidates: list[RetrievalCandidate], limit: int) -> list[RetrievalCandidate]: ...


class LocalCrossEncoderReranker:
    """Load local safetensors only; verify bytes and reject silent truncation."""

    def __init__(self, directory: Path, revision: str, *, device: str = "cpu", batch_size: int = 8,
                 max_candidates: int = 100, max_length: int = 512):
        if not directory.is_dir() or not revision:
            raise ValueError("reranker requires a local model directory and content fingerprint")
        if min(batch_size, max_candidates, max_length) <= 0 or device not in {"cpu", "mps"}:
            raise ValueError("invalid reranker resource configuration")
        self.directory, self.revision, self.device = directory, revision, device
        self.batch_size, self.max_candidates, self.max_length = batch_size, max_candidates, max_length
        self.identity = f"local-cross-encoder@{revision}"
        self._model = None

    def _load(self):
        if self._model is None:
            if model_fingerprint(self.directory) != self.revision:
                raise ValueError("reranker model fingerprint changed")
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(str(self.directory), device=self.device, local_files_only=True,
                                       trust_remote_code=False, max_length=self.max_length,
                                       model_kwargs={"use_safetensors": True})
        return self._model

    def rerank(self, query: str, candidates: list[RetrievalCandidate], limit: int = 8) -> list[RetrievalCandidate]:
        if limit <= 0 or len(candidates) > self.max_candidates:
            raise ValueError("reranker candidate/output bound exceeded")
        if not candidates:
            return []
        model = self._load()
        pairs = [(query, candidate.evidence.content) for candidate in candidates]
        for left, right in pairs:
            encoded = model.tokenizer(left, right, truncation=False)
            if len(encoded["input_ids"]) > self.max_length:
                raise ValueError("reranker input exceeds token bound; rechunk instead of truncating")
        values = model.predict(pairs, batch_size=self.batch_size, show_progress_bar=False)
        scores = [float(value) for value in values]
        if len(scores) != len(candidates) or any(not math.isfinite(value) for value in scores):
            raise ValueError("reranker returned invalid scores")
        ranked = sorted(zip(candidates, scores), key=lambda pair: (-pair[1], pair[0].evidence.id))[:limit]
        return [candidate.model_copy(update={"score": score, "rank": rank, "lane": "reranker:" + candidate.lane})
                for rank, (candidate, score) in enumerate(ranked, 1)]
