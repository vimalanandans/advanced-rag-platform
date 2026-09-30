"""Built-in component executors. The graph runtime invokes these through the registry only."""

from __future__ import annotations

from typing import Any
import time

from rag_workbench.contracts import ContextPlan, Evidence, TokenUsage
from rag_workbench.providers import OllamaModelProvider
from rag_workbench.retrieval import BM25Retriever, DenseRetriever, Retriever, VectorlessHierarchicalRetriever, evidence_sufficient, reciprocal_rank_fusion


def classify(inputs: dict[str, Any], _context: Any, _config: dict[str, Any]) -> dict[str, Any]:
    return {"route": "all"}


def bm25(inputs: dict[str, Any], _context: Any, config: dict[str, Any]) -> dict[str, Any]:
    return {"candidates": BM25Retriever().retrieve(inputs["query"], inputs["evidence"], config.get("limit", 5))}


def dense(inputs: dict[str, Any], _context: Any, config: dict[str, Any], retriever: Retriever | None = None) -> dict[str, Any]:
    return {"candidates": (retriever or DenseRetriever()).retrieve(inputs["query"], inputs["evidence"], config.get("limit", 5))}


def vectorless(inputs: dict[str, Any], context: Any, config: dict[str, Any]) -> dict[str, Any]:
    context.consume_retrieval_reasoning(len(inputs["query"].split()))
    return {"candidates": VectorlessHierarchicalRetriever().retrieve(inputs["query"], inputs["evidence"], config.get("limit", 5))}


def rrf(inputs: dict[str, Any], _context: Any, config: dict[str, Any]) -> dict[str, Any]:
    return {"candidates": reciprocal_rank_fusion(inputs["candidate_lists"], limit=config.get("limit", 8))}


def verify(inputs: dict[str, Any], _context: Any, _config: dict[str, Any]) -> dict[str, Any]:
    return {"sufficient": evidence_sufficient(inputs["candidates"])}


def pack_context(inputs: dict[str, Any], context: Any, _config: dict[str, Any]) -> dict[str, Any]:
    included, omitted, used = [], [], 0
    for candidate in inputs["candidates"]:
        estimate = len(candidate.evidence.content.split())
        if used + estimate <= context.budget.max_context_tokens:
            included.append(candidate.evidence.id); used += estimate
        else:
            omitted.append(candidate.evidence.id)
    return {"context": ContextPlan(included=included, omitted=omitted, token_usage=TokenUsage(input_tokens=used, context_tokens=used))}


def generate(inputs: dict[str, Any], context: Any, _config: dict[str, Any], provider: OllamaModelProvider | None = None) -> dict[str, Any]:
    selected = [candidate.evidence for candidate in inputs["candidates"] if candidate.evidence.id in inputs["context"].included]
    if not inputs["sufficient"] or not selected:
        answer, citations, abstained = "I cannot answer from the approved evidence available.", [], True
    else:
        excerpts = " ".join(item.content.replace("\n", " ")[:220] for item in selected[:2])
        labels = ", ".join(f"[{item.id}]" for item in selected[:2])
        if provider is None:
            answer = f"Based on the approved evidence: {excerpts} {labels}"
        else:
            prompt = (
                "Answer only from the approved local evidence below. If it is insufficient, say so. "
                "Do not invent citations or facts.\n\nQuestion: " + inputs["question"] + "\n\nEvidence:\n" + excerpts
            )
            if isinstance(provider, OllamaModelProvider):
                context.assert_within_deadline()
                remaining = context.budget.max_latency_ms / 1000 - (time.monotonic() - context.started_at)
                answer = provider.generate(prompt, timeout=max(0.001, remaining), max_tokens=context.budget.max_output_tokens).strip()
            else:
                answer = provider.generate(prompt).strip()
            if not answer:
                raise RuntimeError("local model returned an empty answer")
        citations, abstained = selected[:2], False
    return {"answer": answer, "citations": citations, "abstained": abstained}


def baseline_executors(
    dense_retriever: Retriever | None = None,
    generation_provider: OllamaModelProvider | None = None,
) -> dict[str, Any]:
    """Bind adapters at platform composition time, never inside pipeline graphs."""
    return {
        "query.classifier@1.0.0": classify,
        "retrieval.bm25@1.0.0": bm25,
        "retrieval.dense@1.0.0": lambda inputs, context, config: dense(inputs, context, config, dense_retriever),
        "retrieval.vectorless@1.0.0": vectorless,
        "fusion.rrf@1.0.0": rrf,
        "verification.evidence@1.0.0": verify,
        "context.evidence_packer@1.0.0": pack_context,
        "generation.local@1.0.0": lambda inputs, context, config: generate(inputs, context, config, generation_provider),
    }


BASELINE_EXECUTORS = baseline_executors()
