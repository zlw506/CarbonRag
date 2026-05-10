from app.langchain_rag.bm25_store import LangChainBm25Store
from app.langchain_rag.schemas import LangChainRagDocument


def test_langchain_rag_bm25_returns_metadata_rich_hits() -> None:
    documents = [
        LangChainRagDocument(
            page_content="双碳目标要求企业降低外购电力排放。",
            metadata={
                "chunk_id": "chunk-policy",
                "knowledge_item_id": "policy-1",
                "title": "双碳政策",
                "source_type": "public_policy",
                "source": "政策库",
                "page_number": 2,
            },
        ),
        LangChainRagDocument(
            page_content="实验报告讨论 STM32 中断流程。",
            metadata={"chunk_id": "chunk-lab", "knowledge_item_id": "file-1", "title": "实验报告"},
        ),
    ]

    hits = LangChainBm25Store(documents).search(query="双碳 外购电力", top_k=2)

    assert hits
    assert hits[0].chunk_id == "chunk-policy"
    assert hits[0].knowledge_item_id == "policy-1"
    assert hits[0].source_type == "public_policy"
    assert hits[0].page_number == 2
    assert hits[0].bm25_score is not None
