from app.langchain_rag.tool import LangChainRagSearchTool
from app.rag.kb.models import RagHit, RagSearchRequest, RagSearchResult, RagTrace


class FakeRagService:
    def search(self, *, owner_user_id: str, request: RagSearchRequest):
        assert owner_user_id == "user-1"
        assert request.query == "双碳"
        assert request.knowledge_scope == "mixed"
        assert request.allowed_knowledge_item_ids == ["ki-file"]
        return RagSearchResult(
            query=request.query,
            hits=[
                RagHit(
                    chunk_id="chunk-1",
                    doc_id="ki-file",
                    title="上传文件",
                    snippet="双碳相关内容",
                    source_type="private_upload",
                    file_id="file-1",
                    sparse_score=1.0,
                )
            ],
            trace=RagTrace(sparse_count=1, dense_count=1, rerank_applied=False),
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
    assert result.output["retrieval_trace"]["sparse_count"] == 1
