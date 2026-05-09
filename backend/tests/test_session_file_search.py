from app.ai_runtime.tools.session_file_search import SessionFileSearchTool
from app.rag.schemas import RagEvidenceChunk, RagEvidenceReference, RagRetrievalMetadata, RagRetrievalResult


class _FakeRagEngine:
    def __init__(self) -> None:
        self.called = False
        self.last_params = None

    def retrieve(self, params):
        self.called = True
        self.last_params = params
        upload_chunk = RagEvidenceChunk(
            reference_id="ref-upload",
            doc_id="file-001",
            knowledge_item_id="file-001",
            title="电费账单.pdf",
            source_type="private_upload",
            source="用户上传知识",
            file_id="file-001",
            page_number=2,
            chunk_id="chunk-upload",
            snippet="第 2 页显示用电量为 1200 kWh。",
            score=1.0,
            retrieval_layer="bm25_fallback",
        )
        sample_chunk = RagEvidenceChunk(
            reference_id="ref-sample",
            doc_id="sample-001",
            knowledge_item_id="sample-001",
            title="样例",
            source_type="private_sample",
            source="样例库",
            chunk_id="chunk-sample",
            snippet="不应进入 session_file_search 结果。",
            score=0.8,
            retrieval_layer="bm25_fallback",
        )
        return RagRetrievalResult(
            query=params.question,
            total_hits=2,
            chunks=[upload_chunk, sample_chunk],
            references=[
                RagEvidenceReference(
                    reference_id="ref-upload",
                    chunk_id=upload_chunk.chunk_id,
                    doc_id=upload_chunk.doc_id,
                    title=upload_chunk.title,
                    source_type=upload_chunk.source_type,
                    source=upload_chunk.source,
                )
            ],
            metadata=RagRetrievalMetadata(
                mode=params.mode,
                knowledge_scope=params.knowledge_scope,
                top_k=params.top_k,
                chunk_top_k=params.top_k,
                retrieval_only=True,
                vector_status="disabled",
                graph_status="unavailable",
                rerank_status="disabled",
            ),
        )


def test_session_file_search_requires_selected_indexed_uploads() -> None:
    rag_engine = _FakeRagEngine()
    tool = SessionFileSearchTool(rag_engine=rag_engine)  # type: ignore[arg-type]

    result = tool.invoke(
        arguments={"question": "读取文件", "payload": {"attached_file_knowledge_item_ids": []}},
        context={"mode": "ask"},
        trace_id="trace-file-search",
    )

    assert result.output["hits"] == []
    assert rag_engine.called is False


def test_session_file_search_filters_private_upload_hits_and_keeps_locator() -> None:
    rag_engine = _FakeRagEngine()
    tool = SessionFileSearchTool(rag_engine=rag_engine)  # type: ignore[arg-type]

    result = tool.invoke(
        arguments={
            "question": "读取电费账单",
            "payload": {"attached_file_knowledge_item_ids": ["file-001"], "top_k": 3},
        },
        context={"mode": "ask"},
        trace_id="trace-file-search",
    )

    assert rag_engine.last_params.knowledge_scope == "private_sample"
    assert rag_engine.last_params.allowed_knowledge_item_ids == ["file-001"]
    assert len(result.output["hits"]) == 1
    assert result.output["hits"][0]["source_type"] == "private_upload"
    assert result.output["hits"][0]["file_id"] == "file-001"
    assert result.output["hits"][0]["page_number"] == 2
