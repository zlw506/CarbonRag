from app.langchain_rag.answer_chain import LangChainRagAnswerChain
from app.langchain_rag.schemas import LangChainRagHit, LangChainRagTrace


class FakeResult:
    content = "根据政策片段，企业应优先核算外购电力排放。"


class FakeProvider:
    def generate_response(self, *, system_prompt: str, user_input: str):
        assert "检索片段" in system_prompt
        return FakeResult()


def test_answer_chain_returns_citations_and_trace(monkeypatch) -> None:
    monkeypatch.setattr("app.langchain_rag.answer_chain.get_chat_provider", lambda: FakeProvider())
    hit = LangChainRagHit(
        chunk_id="chunk-1",
        knowledge_item_id="ki-1",
        doc_id="ki-1",
        title="电力因子公告",
        snippet="2023 年全国电力平均二氧化碳排放因子为 0.5306 kgCO2/kWh。",
        source_type="public_policy",
        source="MEE/NBS",
        page_number=3,
    )
    trace = LangChainRagTrace(bm25_count=1, vector_count=1, rerank_applied=True)

    result = LangChainRagAnswerChain().answer(question="电力因子是多少？", hits=[hit], trace=trace)

    assert "外购电力" in result.answer
    assert result.citations[0]["chunk_id"] == "chunk-1"
    assert result.citations[0]["page_number"] == 3
    assert result.retrieval_trace.rerank_applied is True
