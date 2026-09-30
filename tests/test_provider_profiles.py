from pathlib import Path

import pytest

from rag_workbench.contracts import Evidence
from rag_workbench.graph import pipeline_from_yaml
from rag_workbench.ingestion import ingest_path
from rag_workbench.providers import provider_profile_from_environment
from rag_workbench.registry import baseline_registry
from rag_workbench.retrieval import IndexedDenseRetriever
from rag_workbench.runtime import WorkbenchRuntime


class FakeVectorIndex:
    def __init__(self) -> None:
        self.created: list[int] = []
        self.points: list[dict] = []

    def create_index(self, dimensions: int) -> None:
        self.created.append(dimensions)

    def upsert(self, point_id: str, vector: list[float], payload: dict) -> None:
        self.points.append({"id": point_id, "vector": vector, "payload": payload})

    def search(self, _vector: list[float], limit: int = 5, *, allowed_point_ids: list[str]) -> list[dict]:
        allowed = [point for point in self.points if point["id"] in allowed_point_ids]
        return [{"id": point["id"], "payload": point["payload"], "score": 0.9} for point in allowed[:limit]]

    def health(self) -> bool:
        return True


class FakeLocalModel:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "The approved evidence supports abstaining when evidence is insufficient."


def test_indexed_dense_retriever_indexes_only_the_authorized_evidence_passed_to_it():
    index = FakeVectorIndex()
    approved = Evidence(
        id="approved", document_id="a", source_uri="file:///a", revision="v1", title="A",
        locator="section:1", content="Approved retrieval evidence",
    )
    rejected = approved.model_copy(update={"id": "rejected", "approval_state": "rejected"})

    results = IndexedDenseRetriever(index).retrieve("retrieval evidence", [approved, rejected])

    assert index.created == [64]
    assert [point["payload"]["evidence_id"] for point in index.points] == ["approved"]
    assert [result.evidence.id for result in results] == ["approved"]


def test_provider_profile_is_explicit_and_rejects_unknown_modes():
    profile = provider_profile_from_environment({
        "RAG_WORKBENCH_DENSE_MODE": "qdrant",
        "RAG_WORKBENCH_GENERATION_MODE": "ollama",
        "RAG_WORKBENCH_OLLAMA_MODEL": "qwen3:8b",
    })
    assert profile.model_version == "ollama:qwen3:8b"

    with pytest.raises(ValueError, match="DENSE_MODE"):
        provider_profile_from_environment({"RAG_WORKBENCH_DENSE_MODE": "implicit-fallback"})


def test_local_model_profile_preserves_workbench_citations_and_records_model_version():
    root = Path(__file__).parent.parent
    model = FakeLocalModel()
    runtime = WorkbenchRuntime(
        registry=baseline_registry(generation_provider=model),
        model_version="ollama:test-model",
    )
    runtime.set_evidence(ingest_path(root / "data/fixtures/rag_basics.md"))
    plan = runtime.compile(pipeline_from_yaml((root / "configs/pipelines/baseline.yaml").read_text()))

    result = runtime.run(plan, "When should a RAG system abstain?")

    assert result.answer.startswith("The approved evidence")
    assert result.citations
    assert result.manifest.model_version == "ollama:test-model"
    assert len(model.prompts) == 1
