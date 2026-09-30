"""Persistent, scope-local BM25 statistics and exact identifier retrieval."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
from collections import Counter
from collections.abc import Iterable
from contextlib import closing
from pathlib import Path

from rag_workbench.contracts import Evidence, RetrievalCandidate
from rag_workbench.retrieval import Retriever, _rank, tokens


class PersistentBM25Retriever(Retriever):
    """Cache immutable term counts; score only the authorized snapshot.

    Corpus statistics are derived after scope filtering so denied documents do
    not affect ranks or appear through shared-index document frequencies.
    """

    lane = "bm25"
    version = "2.0.0"
    tokenizer_version = "ascii-stopwords-v1"

    def __init__(self, path: Path, *, k1: float = 1.2, b: float = 0.75):
        if not math.isfinite(k1) or not math.isfinite(b) or k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("BM25 requires k1 > 0 and 0 <= b <= 1")
        self.path, self.k1, self.b = path, k1, b
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
        except FileExistsError:
            pass
        with closing(self._connect()) as connection, connection:
            connection.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            connection.execute("INSERT OR IGNORE INTO metadata VALUES ('format', ?)", (self.tokenizer_version,))
            if connection.execute("SELECT value FROM metadata WHERE key='format'").fetchone()[0] != self.tokenizer_version:
                raise ValueError("lexical index tokenizer mismatch; build a new index")
            connection.execute("CREATE TABLE IF NOT EXISTS terms (identity TEXT PRIMARY KEY, counts TEXT NOT NULL, length INTEGER NOT NULL)")

    def _connect(self):
        return sqlite3.connect(self.path, timeout=5)

    @staticmethod
    def _identity(item: Evidence) -> str:
        return hashlib.sha256(item.model_dump_json(exclude={"source_uri"}).encode()).hexdigest()

    def retrieve(self, query: str, evidence: Iterable[Evidence], limit: int = 5) -> list[RetrievalCandidate]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        docs = [item for item in evidence if item.approval_state == "approved"]
        if len({item.id for item in docs}) != len(docs):
            raise ValueError("authorized snapshot contains duplicate evidence IDs")
        if not docs:
            return []
        statistics = []
        connection = self._connect()
        try:
            with connection:
                for item in docs:
                    identity = self._identity(item)
                    stored = connection.execute("SELECT counts, length FROM terms WHERE identity=?", (identity,)).fetchone()
                    if stored:
                        counts, length = Counter(json.loads(stored[0])), stored[1]
                    else:
                        counts = Counter(tokens(item.content))
                        length = sum(counts.values())
                        connection.execute("INSERT OR IGNORE INTO terms VALUES (?, ?, ?)", (identity, json.dumps(counts, sort_keys=True), length))
                    statistics.append((item, counts, length))
        finally:
            connection.close()
        average_length = sum(length for _, _, length in statistics) / len(docs) or 1
        frequency = Counter(term for _, counts, _ in statistics for term in counts)
        query_terms = set(tokens(query))
        scored = []
        for item, counts, length in statistics:
            score = 0.0
            for term in query_terms:
                tf = counts[term]
                if tf:
                    idf = math.log1p((len(docs) - frequency[term] + 0.5) / (frequency[term] + 0.5))
                    score += idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * length / average_length))
            if score > 0:
                scored.append((item, score))
        scored.sort(key=lambda item: item[0].id)
        return _rank(scored, self.lane, limit)


class ExactRetriever(Retriever):
    lane = "exact"

    def retrieve(self, query: str, evidence: Iterable[Evidence], limit: int = 5) -> list[RetrievalCandidate]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        phrases = re.findall(r'"([^"\n]+)"', query)
        identifiers = [term for term in re.findall(r"[\w]+(?:[-./][\w]+)*", query) if any(char.isdigit() for char in term)]
        needles = {value.casefold() for value in phrases + identifiers}
        if not needles:
            return []
        scored = []
        for item in evidence:
            if item.approval_state != "approved":
                continue
            text = item.content.casefold()
            hits = sum(bool(re.search(r"(?<![\w./-])" + re.escape(needle) + r"(?![\w./-])", text)) for needle in needles)
            if hits:
                scored.append((item, float(hits)))
        scored.sort(key=lambda item: item[0].id)
        return _rank(scored, self.lane, limit)
