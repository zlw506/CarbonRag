from app.langchain_rag.schemas import LangChainRagHit, LangChainRagSearchResult, LangChainRagTrace
from app.langchain_rag.tool import LangChainRagSearchTool


class FakeRagService:
    def search(self, *, owner_user_id: str, query: str, knowledge_scope: str, top_k: int, allowed_knowledge_item_ids: list[str]):
        assert owner_user_id == "user-1"
        assert query == "双碳"
        assert knowledge_scope == "mixed"
        assert allowed_knowledge_item_ids == ["ki-file"]
        return LangChainRagSearchResult(
            query=query,
            hyde_query="假设性双碳回答",
            hits=[
                LangChainRagHit(
                    chunk_id="chunk-1",
                    doc_id="ki-file",
                    title="上传文件",
                    snippet="双碳相关内容",
                    source_type="private_upload",
                    source="file",
                    file_id="file-1",
                )
            ],
            trace=LangChainRagTrace(bm25_count=1, vector_count=1, rerank_applied=False),
        )


def test_langchain_rag_search_tool_outputs_hits_and_trace() -> None:
    result = LangChainRagSearchTool(rag_service=FakeRagService()).invoke(
        arguments={
            "question": "双碳",
            "knowledge_scope": "mixed",
            "payload": {
                "owner_user_id": "user-1",
                "attached_file_knowledge_item_ids": ["ki-file"],
            },
        },
        context={},
        trace_id="trace-1",
    )

    assert result.status == "success"
    assert result.output["hits"][0]["source_type"] == "private_upload"
    assert result.output["retrieval_trace"]["bm25_count"] == 1
