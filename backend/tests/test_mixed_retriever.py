from app.retrieval.mixed_retriever import MixedScopeRetriever


def test_mixed_retriever_returns_public_and_private_hits() -> None:
    retriever = MixedScopeRetriever()

    result = retriever.search(
        question="双碳目标对样例企业的能耗管理意味着什么？",
        top_k=5,
        allowed_doc_ids={"enterprise_doc_001", "enterprise_doc_002", "energy_bill_sample_001"},
    )

    assert result.total_hits >= 2
    source_types = {hit.source_type for hit in result.hits}
    assert "public_policy" in source_types
    assert "private_sample" in source_types


def test_mixed_retriever_prefers_balanced_quota() -> None:
    retriever = MixedScopeRetriever()

    result = retriever.search(
        question="双碳目标和企业样例现状有什么关系？",
        top_k=5,
        allowed_doc_ids={"enterprise_doc_001", "enterprise_doc_002"},
    )

    public_count = sum(1 for hit in result.hits if hit.source_type == "public_policy")
    private_count = sum(1 for hit in result.hits if hit.source_type == "private_sample")

    assert public_count >= private_count
    assert public_count - private_count <= 1
