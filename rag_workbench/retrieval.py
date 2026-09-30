"""Three provider-neutral retrieval families and explicit fusion/verification."""

from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from collections import Counter
from collections.abc import Iterable
from typing import TYPE_CHECKING

from rag_workbench.contracts import Evidence, RetrievalCandidate
from rag_workbench.providers import VectorIndex

if TYPE_CHECKING:
    from rag_workbench.embeddings import EmbeddingProvider


def tokens(value: str) -> list[str]:
    stopwords = {"a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "of", "on", "or", "the", "to", "what", "when", "where", "who", "with"}
    return [term for term in re.findall(r"[a-z0-9]+", value.lower()) if term not in stopwords]


class Retriever:
    lane: str

    def retrieve(self, query: str, evidence: Iterable[Evidence], limit: int = 5) -> list[RetrievalCandidate]:
        raise NotImplementedError


class BM25Retriever(Retriever):
    lane = "bm25"

    def retrieve(self, query: str, evidence: Iterable[Evidence], limit: int = 5) -> list[RetrievalCandidate]:
        docs = [item for item in evidence if item.approval_state == "approved"]
        query_terms = tokens(query)
        document_frequency = Counter(term for item in docs for term in set(tokens(item.content)))
        scored: list[tuple[Evidence, float]] = []
        for item in docs:
            terms = tokens(item.content)
            length = max(len(terms), 1)
            frequencies = Counter(terms)
            score = sum((frequencies[term] / length) * math.log((len(docs) + 1) / (document_frequency[term] + 1) + 1) for term in query_terms)
            if score:
                scored.append((item, score))
        return _rank(scored, self.lane, limit)


class DenseRetriever(Retriever):
    """Deterministic local embedding baseline; replace with a Qdrant adapter in deployment."""

    lane = "dense"

    def retrieve(self, query: str, evidence: Iterable[Evidence], limit: int = 5) -> list[RetrievalCandidate]:
        query_vector = _embedding(query)
        query_terms = set(tokens(query))
        # The deterministic fallback intentionally requires a weak lexical anchor. This guards
        # against hash collisions being mistaken for semantic evidence; production embeddings
        # replace this provider without changing the contract.
        scored = [
            (item, _cosine(query_vector, _embedding(item.content)))
            for item in evidence
            if item.approval_state == "approved" and query_terms & set(tokens(item.content))
        ]
        return _rank([(item, score) for item, score in scored if score > 0], self.lane, limit)


class IndexedDenseRetriever(Retriever):
    """Dense retrieval backed by a provider-neutral vector index.

    Only approved evidence passed by the runtime is indexed and considered in the
    result map. This preserves authorization even if a shared local collection has
    stale points from another corpus.
    """

    lane = "dense"

    def __init__(self, index: VectorIndex, dimensions: int | None = None, embeddings: EmbeddingProvider | None = None) -> None:
        self.index = index
        if embeddings is not None and dimensions is not None and dimensions != embeddings.identity.dimensions:
            raise ValueError("embedding dimension differs from index configuration")
        self.embeddings = embeddings
        self.dimensions = embeddings.identity.dimensions if embeddings is not None else (dimensions or 64)
        self._indexed_revision: str | None = None

    def retrieve(self, query: str, evidence: Iterable[Evidence], limit: int = 5) -> list[RetrievalCandidate]:
        approved = [item for item in evidence if item.approval_state == "approved"]
        if not approved:
            return []
        self._ensure_index(approved)
        by_id = {self._point_id(item): item for item in approved}
        matches = self.index.search(self._encode([query], "query")[0], limit=limit, allowed_point_ids=sorted(by_id))
        candidates: list[RetrievalCandidate] = []
        for rank, match in enumerate(matches, start=1):
            item = by_id.get(str(match.get("id", "")))
            if item is None:
                raise PermissionError("vector provider returned a point outside the authorized snapshot")
            score = float(match.get("score", 0.0))
            if not math.isfinite(score):
                raise ValueError("vector provider returned a non-finite score")
            candidates.append(RetrievalCandidate(evidence=item, lane=self.lane, score=score, rank=rank))
        return candidates

    def _ensure_index(self, evidence: list[Evidence]) -> None:
        revision = hashlib.sha256(
            "|".join(sorted(self._point_id(item) for item in evidence)).encode("utf-8")
        ).hexdigest()
        if revision == self._indexed_revision:
            return
        self.index.create_index(self.dimensions)
        vectors = self._encode([item.content for item in evidence], "document")
        for item, vector in zip(evidence, vectors):
            self.index.upsert(
                self._point_id(item),
                vector,
                {"evidence_id": item.id, "document_id": item.document_id, "revision": item.revision},
            )
        self._indexed_revision = revision

    def _point_id(self, item: Evidence) -> str:
        identity = json.dumps({"evidence": item.model_dump(mode="json", exclude={"source_uri"}), "embedding": self.embeddings.identity.model_dump() if self.embeddings else "hashed-fixture-v1", "dimensions": self.dimensions}, sort_keys=True, separators=(",", ":"))
        return str(uuid.uuid5(uuid.NAMESPACE_URL, identity))

    def _encode(self, texts: list[str], purpose: str) -> list[list[float]]:
        vectors = self.embeddings.encode(texts, purpose=purpose) if self.embeddings else [_embedding(text, self.dimensions) for text in texts]
        if len(vectors) != len(texts) or any(len(vector) != self.dimensions or any(not math.isfinite(value) for value in vector) for vector in vectors):
            raise ValueError("embedding provider violated dimension or batch contract")
        return vectors


class VectorlessHierarchicalRetriever(Retriever):
    """Storeless/PageIndex-style structural navigation over sections and headings."""

    lane = "vectorless"

    def retrieve(self, query: str, evidence: Iterable[Evidence], limit: int = 5) -> list[RetrievalCandidate]:
        wanted = set(tokens(query))
        scored: list[tuple[Evidence, float]] = []
        for item in evidence:
            if item.approval_state != "approved":
                continue
            heading, _, body = item.content.partition("\n")
            heading_overlap = len(wanted & set(tokens(heading))) * 3
            body_overlap = len(wanted & set(tokens(body)))
            structure_bonus = 0.5 if item.locator.startswith(("section:", "page:")) else 0
            score = heading_overlap + body_overlap + structure_bonus
            if heading_overlap or body_overlap:
                scored.append((item, float(score)))
        return _rank(scored, self.lane, limit)


def reciprocal_rank_fusion(candidate_lists: list[list[RetrievalCandidate]], limit: int = 8, k: int = 60) -> list[RetrievalCandidate]:
    merged: dict[str, tuple[Evidence, float, list[str]]] = {}
    for candidates in candidate_lists:
        for candidate in candidates:
            evidence, score, lanes = merged.get(candidate.evidence.id, (candidate.evidence, 0.0, []))
            merged[candidate.evidence.id] = (evidence, score + 1 / (k + candidate.rank), lanes + [candidate.lane])
    ranked = sorted(merged.values(), key=lambda value: value[1], reverse=True)[:limit]
    return [RetrievalCandidate(evidence=item, lane="rrf:" + "+".join(lanes), score=score, rank=index) for index, (item, score, lanes) in enumerate(ranked, start=1)]


def evidence_sufficient(candidates: list[RetrievalCandidate]) -> bool:
    return bool(candidates and candidates[0].score > 0)


def _rank(scored: list[tuple[Evidence, float]], lane: str, limit: int) -> list[RetrievalCandidate]:
    return [RetrievalCandidate(evidence=item, lane=lane, score=score, rank=index) for index, (item, score) in enumerate(sorted(scored, key=lambda pair: pair[1], reverse=True)[:limit], start=1)]


def _embedding(text: str, dimensions: int = 64) -> list[float]:
    vector = [0.0] * dimensions
    for term in tokens(text):
        bucket = int.from_bytes(hashlib.sha256(term.encode("utf-8")).digest()[:8], "big") % dimensions
        vector[bucket] += 1.0
    return vector


def _cosine(left: list[float], right: list[float]) -> float:
    denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(sum(value * value for value in right))
    return sum(a * b for a, b in zip(left, right)) / denominator if denominator else 0.0
