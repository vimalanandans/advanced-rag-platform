import pytest

from rag_workbench.providers import QdrantVectorIndex


def test_qdrant_adapter_is_provider_neutral_and_does_not_connect_at_construction():
    adapter = QdrantVectorIndex("http://localhost:6333", "demo")
    assert adapter.collection == "demo"
    assert adapter.url == "http://localhost:6333"


def test_remote_provider_requires_explicit_opt_in():
    with pytest.raises(ValueError, match="allow_remote"):
        QdrantVectorIndex("https://example.invalid", "demo")
