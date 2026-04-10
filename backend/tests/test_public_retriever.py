from app.retrieval.public_chunker import chunk_public_policy_document
from app.retrieval.public_corpus_loader import load_public_policy_documents
from app.retrieval.public_retriever import get_public_policy_retriever


def test_public_policy_documents_can_be_loaded() -> None:
    documents = load_public_policy_documents()

    assert len(documents) == 5
    assert {document.metadata.doc_id for document in documents} == {
        "policy_001",
        "policy_002",
        "policy_003",
        "policy_004",
        "policy_005",
    }


def test_public_policy_document_can_be_chunked() -> None:
    document = next(
        candidate
        for candidate in load_public_policy_documents()
        if candidate.metadata.doc_id == "policy_001"
    )

    chunks = chunk_public_policy_document(document)

    assert chunks
    assert chunks[0].chunk_id.startswith("policy_001_chunk_")
    assert all(chunk.snippet.strip() for chunk in chunks)


def test_public_retriever_returns_hits_for_dual_carbon_question() -> None:
    retriever = get_public_policy_retriever()

    result = retriever.search(
        question="什么是双碳目标？",
        top_k=3,
        knowledge_scope="public",
    )

    assert result.total_hits >= 1
    assert len(result.hits) >= 1
    assert any(
        keyword in hit.title
        for hit in result.hits
        for keyword in ("碳达峰", "碳中和", "统计核算", "标准计量")
    )
