from rag_workbench.contracts import Evidence
from rag_workbench.retrieval import BM25Retriever, DenseRetriever, VectorlessHierarchicalRetriever, reciprocal_rank_fusion


def evidence():
    return [Evidence(id="one", document_id="doc", source_uri="file:///one", revision="v1", title="Retrieval", locator="section:retrieval", content="# Retrieval\nLexical retrieval protects exact identifiers.")]


def test_all_baseline_retrieval_lanes_return_candidates():
    docs = evidence()
    lane_results = [retriever.retrieve("exact identifiers", docs) for retriever in (BM25Retriever(), DenseRetriever(), VectorlessHierarchicalRetriever())]
    assert all(results for results in lane_results)
    assert reciprocal_rank_fusion(lane_results)[0].evidence.id == "one"
