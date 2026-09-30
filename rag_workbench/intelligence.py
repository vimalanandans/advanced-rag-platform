"""Conservative query decisions, structural navigation and extractive verification."""

from __future__ import annotations

import re
from collections.abc import Iterable

from rag_workbench.contracts import ClaimSupport, Evidence, QueryDecision, RetrievalCandidate
from rag_workbench.retrieval import Retriever, _rank, tokens


def classify_query(query: str) -> QueryDecision:
    rules: list[tuple[str, str, str]] = [
        ("exact_phrase", r'"[^"\n]+"', "quoted phrase"),
        ("exact_identifier", r"\b[a-zA-Z]+[-./]?\d+[\w./-]*\b", "identifier pattern"),
        ("comparison", r"\b(compare|versus|vs|difference)\b", "comparison vocabulary"),
        ("procedure", r"\b(how to|steps|procedure|instructions)\b", "procedure vocabulary"),
        ("table", r"\b(table|row|column|spreadsheet)\b", "tabular vocabulary"),
        ("visual", r"\b(figure|diagram|image|chart|screenshot)\b", "visual vocabulary"),
        ("temporal", r"\b(as of|effective|latest|previous version|previous revision|superseded|current version)\b", "temporal vocabulary"),
        ("multi_hop", r"\b(which.*and.*why|first.*then|across documents)\b", "multi-step vocabulary"),
        ("relationship", r"\b(related|relationship|connected|depends on)\b", "relationship vocabulary"),
        ("conversational", r"\b(you said|previous answer|that answer|follow up)\b", "conversation reference"),
        ("no_rag_required", r"^\s*(hello|hi|thanks|thank you)[.!]?\s*$", "greeting or acknowledgment"),
    ]
    kind, reason, confidence = "semantic", "no specialized rule matched", 0.3
    for candidate, pattern, description in rules:
        if re.search(pattern, query, re.IGNORECASE):
            kind, reason, confidence = candidate, description, 0.7
            break
    lanes = ["exact", "bm25", "dense", "structural"]
    capabilities = {"visual": ["visual_evidence"], "table": ["structured_tables"],
                    "relationship": ["relationship_evidence"], "conversational": ["conversation_context"]}.get(kind, ["text_evidence"])
    # Initial safe routing never suppresses a retrieval lane based on heuristic confidence.
    return QueryDecision(original_query=query, query_class=kind, confidence=confidence,
                         required_capabilities=capabilities, recommended_lanes=lanes, reason=reason)


class StructuralRetriever(Retriever):
    lane = "structural"

    def __init__(self, max_depth: int = 3):
        if not 0 <= max_depth <= 10:
            raise ValueError("structural depth must be between zero and ten")
        self.max_depth = max_depth

    def retrieve(self, query: str, evidence: Iterable[Evidence], limit: int = 5) -> list[RetrievalCandidate]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        docs = {item.id: item for item in evidence if item.approval_state == "approved"}
        wanted = set(tokens(query))
        scored = []
        for item in docs.values():
            heading, _, body = item.content.partition("\n")
            score = 3 * len(wanted & set(tokens(heading))) + len(wanted & set(tokens(body)))
            if score:
                scored.append((item, float(score)))
        seeds = _rank(sorted(scored, key=lambda value: value[0].id), self.lane, limit)
        result = []
        seen = set()
        for seed in seeds:
            if seed.evidence.id not in seen:
                result.append(seed)
                seen.add(seed.evidence.id)
            current = seed.evidence
            chain = {current.id}
            for depth in range(self.max_depth):
                parent = docs.get(current.metadata.get("parent_id"))
                if parent is None:
                    break
                if parent.id in chain or parent.document_id != current.document_id or parent.revision != current.revision:
                    raise ValueError("invalid structural parent chain")
                chain.add(parent.id)
                if parent.id not in seen:
                    result.append(RetrievalCandidate(evidence=parent, lane="structural:parent", score=seed.score / (depth + 2), rank=0))
                    seen.add(parent.id)
                current = parent
        return [item.model_copy(update={"rank": index}) for index, item in enumerate(result[:limit], 1)]



def sentences(text: str) -> list[str]:
    body = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", body) if part.strip()]


def normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


def verify_quoted_claims(answer: str, evidence: list[Evidence], *, allow_next_line: bool = False) -> list[ClaimSupport]:
    """Verify exact complete source sentences and explicit citation IDs.

    This checks source fidelity, not source truth or general semantic entailment.
    Unknown syntax, altered qualifiers and paraphrases fail closed.
    """
    sources = {item.id: {normalize(value) for value in sentences(item.content)} for item in evidence}
    results = []
    lines = answer.splitlines()
    if allow_next_line:
        joined = []
        index = 0
        while index < len(lines):
            line = lines[index]
            if line.strip() and index + 1 < len(lines) and re.fullmatch(r"\s*\[[^\[\]]+\]\s*", lines[index + 1]):
                line += " " + lines[index + 1].strip()
                index += 1
            joined.append(line)
            index += 1
        lines = joined
    for line in lines:
        if not line.strip():
            continue
        match = re.fullmatch(r"\s*(.+?)\s+\[([^\[\]]+)\]\s*", line)
        claim, evidence_id = (match.group(1), match.group(2)) if match else (line.strip(), "")
        supported = evidence_id in sources and normalize(claim) in sources[evidence_id]
        results.append(ClaimSupport(claim=claim, evidence_ids=[evidence_id] if evidence_id in sources else [],
                                    support="supported" if supported else "unsupported", confidence=1.0 if supported else 0.0,
                                    action="keep" if supported else "abstain",
                                    verifier="verbatim-sentence@1.0.1" if allow_next_line else "verbatim-sentence@1.0.0"))
    return results
