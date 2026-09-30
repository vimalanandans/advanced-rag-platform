from pathlib import Path

import pytest

from rag_workbench.contracts import Budget, Evidence, RequestContext, RetrievalCandidate
from rag_workbench.ingestion import ingest_structural_path
from rag_workbench.intelligence import StructuralRetriever, classify_query, verify_quoted_claims
from rag_workbench.runtime import ExecutionContext
from rag_workbench.v2_components import pack_context, verify_claims, verify_evidence


def doc(identifier="source", content="Never remove the safety guard.", **updates):
    return Evidence(**({"id": identifier, "document_id": "manual", "source_uri": "file:///manual", "revision": "1",
                        "content": content, "title": "Manual", "locator": "section:1"} | updates))


@pytest.mark.parametrize("query, expected", [
    ('Find "safety guard"', "exact_phrase"), ("AB-123 status", "exact_identifier"),
    ("Compare options", "comparison"), ("How to install", "procedure"),
    ("Which table", "table"), ("Explain diagram", "visual"),
    ("As of yesterday", "temporal"), ("First select then check", "multi_hop"),
    ("What depends on this", "relationship"), ("Explain your previous answer", "conversational"),
    ("hello", "no_rag_required"), ("Explain safety", "semantic"),
])
def test_classifier_preserves_query_and_conservative_fallback(query, expected):
    decision = classify_query(query)
    assert decision.original_query == query
    assert decision.query_class == expected
    assert decision.fallback == "all_available_lanes"
    assert "dense" in decision.recommended_lanes


def test_structural_parent_mapping_and_authorized_expansion(tmp_path):
    path = tmp_path / "manual.md"
    path.write_text("# Safety\nNever bypass guards.\n## Repair\nDisconnect the cable.\n### Motor\nInspect winding.")
    evidence = ingest_structural_path(path)
    assert evidence[2].metadata["parent_id"] == evidence[1].id
    found = StructuralRetriever().retrieve("winding", evidence)
    assert [item.evidence.id for item in found] == [evidence[2].id, evidence[1].id, evidence[0].id]
    scoped = StructuralRetriever().retrieve("winding", [evidence[2]])
    assert [item.evidence.id for item in scoped] == [evidence[2].id]


def test_structural_cycle_fails_instead_of_unbounded_expansion():
    item = doc(metadata={"parent_id": "source"})
    with pytest.raises(ValueError, match="parent chain"):
        StructuralRetriever().retrieve("safety", [item])


def test_claim_verifier_requires_complete_sentence_and_real_citation():
    evidence = [doc()]
    good = verify_quoted_claims("Never remove the safety guard. [source]", evidence)
    assert good[0].support == "supported"
    for answer in ["Remove the safety guard. [source]", "Never remove the safety guard. [invented]", "the safety guard. [source]", "Never remove the safety guard."]:
        assert verify_quoted_claims(answer, evidence)[0].support == "unsupported"
        assert verify_claims({"answer": answer, "citations": evidence, "abstained": False}, None, {})["abstained"]


def test_context_omits_whole_block_instead_of_truncating_warning():
    context = ExecutionContext(RequestContext(tenant_id="local", user_id="local-admin"), Budget(max_context_tokens=10))
    item = doc()
    result = pack_context({"question": "safety", "candidates": [RetrievalCandidate(evidence=item, lane="exact", score=1, rank=1)]}, context, {})["context"]
    assert result.included == []
    assert result.omitted == [item.id]
    assert result.truncated == []
    assert result.decisions[0]["reason"] == "context_budget"


def test_unresolved_revision_conflict_forces_insufficient_evidence():
    candidates = [RetrievalCandidate(evidence=doc(revision=revision), lane="dense", score=1, rank=index)
                  for index, revision in enumerate(["1", "2"], 1)]
    result = verify_evidence({"candidates": candidates, "decision": classify_query("safety")}, None, {})
    assert not result["sufficient"]
    assert result["conflicts"] == ["revision:manual"]


def test_full_v2_graph_returns_only_verified_claims(tmp_path, monkeypatch):
    from rag_workbench.embeddings import OllamaEmbeddingProvider
    from rag_workbench.graph import pipeline_from_yaml
    from rag_workbench.local_real import local_real_runtime
    from rag_workbench.providers import OllamaModelProvider, QdrantVectorIndex
    points = {}
    monkeypatch.setattr(OllamaEmbeddingProvider, "encode", lambda self, texts, **kwargs: [[1.0, 0.0] for _ in texts])
    monkeypatch.setattr(QdrantVectorIndex, "create_index", lambda *args: None)
    monkeypatch.setattr(QdrantVectorIndex, "upsert", lambda self, point_id, vector, payload: points.update({point_id: payload}))
    monkeypatch.setattr(QdrantVectorIndex, "search", lambda self, vector, limit=5, *, allowed_point_ids: [{"id": point_id, "score": 1.0} for point_id in allowed_point_ids][:limit])
    monkeypatch.setattr(OllamaModelProvider, "generate", lambda *args, **kwargs: "Never remove the safety guard. [source]")
    runtime = local_real_runtime(environ={"RAG_WORKBENCH_EMBEDDING_MODEL": "test:latest", "RAG_WORKBENCH_EMBEDDING_REVISION": "digest",
                                         "RAG_WORKBENCH_EMBEDDING_DIMENSIONS": "2", "RAG_WORKBENCH_OLLAMA_MODEL": "test:latest",
                                         "RAG_WORKBENCH_GENERATION_REVISION": "digest", "RAG_WORKBENCH_STORAGE": str(tmp_path)})
    runtime.set_evidence([doc()])
    plan = runtime.compile(pipeline_from_yaml((Path(__file__).parent.parent / "configs/pipelines/local-real.yaml").read_text()))
    result = runtime.run(plan, "Which safety precaution applies?")
    assert not result.abstained
    assert result.claims[0].support == "supported"
    assert [item.id for item in result.citations] == ["source"]
    assert result.manifest.embedding_identity["revision"] == "digest"
    assert result.manifest.decisions
    monkeypatch.setattr(OllamaModelProvider, "generate", lambda *args, **kwargs: "Remove the safety guard. [source]")
    rejected = runtime.run(plan, "Which safety precaution applies?")
    assert rejected.abstained
    assert rejected.citations == []
    assert rejected.claims[0].support == "unsupported"


def test_unavailable_visual_capability_does_not_fall_through_to_text_answer():
    candidate = RetrievalCandidate(evidence=doc(), lane="dense", score=1, rank=1)
    result = verify_evidence({"candidates": [candidate], "decision": classify_query("Explain this diagram")}, None, {})
    assert not result["sufficient"]
    assert result["limitations"] == ["missing_capability:visual_evidence"]


def test_legacy_prompt_components_remain_replayable():
    from rag_workbench.registry import baseline_registry
    from rag_workbench.v2_components import LEGACY_INSTRUCTION, prompt_for, register_v2_components
    registry = baseline_registry()
    register_v2_components(registry)
    for identifier in ['generation.local', 'context.evidence_packer']:
        assert registry.get(identifier + '@2.0.0')
        assert registry.get(identifier + '@2.0.1')
    assert prompt_for('question', [], legacy=True).startswith(LEGACY_INSTRUCTION)
    assert 'copy the bracketed source identifier' in prompt_for('question', [])


def test_next_line_citation_preserves_source_fidelity():
    from rag_workbench.contracts import Evidence
    from rag_workbench.intelligence import verify_quoted_claims
    source = Evidence(id='source', document_id='d', source_uri='fixture://d', revision='1', title='d', locator='1', content='Never remove the safety guard.')
    answer = 'Never remove the safety guard.\n[source]'
    assert all(c.support == 'supported' for c in verify_quoted_claims(answer, [source], allow_next_line=True))
    assert any(c.support != 'supported' for c in verify_quoted_claims(answer, [source]))
    for answer in ['Remove the safety guard.\n[source]', 'Never remove the safety guard.\n[unknown]', '[source]']:
        assert any(c.support != 'supported' for c in verify_quoted_claims(answer, [source], allow_next_line=True))
