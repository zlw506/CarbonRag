from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Mapping

from app.ai_runtime.providers.base import (
    BaseChatProvider,
    BaseEmbeddingProvider,
    ChatCompletionResult,
    EmbeddingResult,
    ProviderDescriptor,
)
from app.ai_runtime.runtime.orchestrator import AIRuntimeOrchestrator
from app.ai_runtime.schemas.chat import ChatRequest
from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition
from app.ai_runtime.tools.registry import ToolRegistry
from app.api.v1.endpoints.sessions import build_chat_request
from app.auth.schemas import AuthenticatedUser
from app.rag.kb.models import KnowledgeBaseCreate, RagDocumentCreate, RagSearchRequest
from app.rag.kb.storage import RagKnowledgeStore
from app.rag.spine import RagSpineService
from app.schemas.ask import AskRequest


class FakeChatProvider(BaseChatProvider):
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(name="fake-chat", provider_type="test", mode="chat", default_model="fake-model")

    def generate_response(self, *, system_prompt: str, user_input: str) -> ChatCompletionResult:
        self.calls.append({"system_prompt": system_prompt, "user_input": user_input})
        return ChatCompletionResult(content="这是基于检索片段生成的测试回答。")


class FakeEmbeddingProvider(BaseEmbeddingProvider):
    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(name="fake-embedding", provider_type="test", mode="embedding", default_model="fake-embedding")

    def embed_stub(self, texts) -> EmbeddingResult:  # noqa: ANN001
        return EmbeddingResult(vectors=[[0.1, 0.2, 0.3] for _ in texts])


class CaptureRagTool(BaseTool):
    def __init__(self) -> None:
        self.last_arguments: dict[str, Any] | None = None

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(name="langchain_rag_search", description="capture RAG tool")

    def invoke(self, *, arguments: Mapping[str, Any], context: Mapping[str, Any], trace_id: str) -> ToolResult:
        self.last_arguments = dict(arguments)
        return ToolResult(
            name="langchain_rag_search",
            status="success",
            output={
                "hits": [],
                "retrieval_trace": {
                    "kb_id": arguments.get("kb_id"),
                    "retrieval_mode": arguments.get("rag_mode"),
                    "dense_count": 0,
                    "sparse_count": 0,
                    "merged_count": 0,
                    "rerank_applied": False,
                    "degraded": True,
                    "warnings": ["test capture"],
                },
            },
        )


class FakeSessionService:
    def list_session_knowledge_items(self, *, owner_user_id: str, session_id: str):  # noqa: ARG002
        return []

    def build_session_context(self, **kwargs):  # noqa: ANN003
        return {"recent_messages": [], "context_usage_estimate": 0}


def test_ask_page_selected_kb_is_passed_to_runtime(monkeypatch) -> None:
    chat_request = _build_selected_kb_chat_request(monkeypatch, kb_id="kb-A", rag_mode="hybrid_rerank")

    assert chat_request.payload["kb_id"] == "kb-A"

    capture_tool = _prepare_runtime_with_capture(monkeypatch, chat_request)
    assert capture_tool.last_arguments is not None
    assert capture_tool.last_arguments["kb_id"] == "kb-A"
    assert capture_tool.last_arguments["payload"]["kb_id"] == "kb-A"


def test_ask_page_rag_mode_is_passed_to_runtime(monkeypatch) -> None:
    chat_request = _build_selected_kb_chat_request(monkeypatch, kb_id="kb-A", rag_mode="sparse")

    assert chat_request.payload["rag_mode"] == "sparse"

    capture_tool = _prepare_runtime_with_capture(monkeypatch, chat_request)
    assert capture_tool.last_arguments is not None
    assert capture_tool.last_arguments["rag_mode"] == "sparse"
    assert capture_tool.last_arguments["payload"]["rag_mode"] == "sparse"


def test_ask_with_two_kbs_only_retrieves_selected_kb(monkeypatch, tmp_path) -> None:
    service = _build_rag_service(monkeypatch, tmp_path)
    kb_a = service.create_kb(owner_user_id="user-1", payload=KnowledgeBaseCreate(name="KB-A"))
    kb_b = service.create_kb(owner_user_id="user-1", payload=KnowledgeBaseCreate(name="KB-B"))
    _index_text_doc(service, kb_id=kb_a.kb_id, title="甲公司电力数据", text="甲公司电力数据：一月用电量 1000 kWh。")
    _index_text_doc(service, kb_id=kb_b.kb_id, title="乙公司天然气数据", text="乙公司天然气数据：一月天然气 200 立方米。")

    result = service.search(
        owner_user_id="user-1",
        request=RagSearchRequest(query="一月能源数据", kb_id=kb_a.kb_id, mode="hybrid", top_k=5),
    )

    assert result.trace.kb_id == kb_a.kb_id
    assert result.hits
    assert all(hit.kb_id == kb_a.kb_id for hit in result.hits)
    assert all(hit.kb_id != kb_b.kb_id for hit in result.hits)


def test_rag_test_qa_calls_chat_provider_with_grounded_context(monkeypatch, tmp_path) -> None:
    chat_provider = FakeChatProvider()
    service = _build_rag_service(monkeypatch, tmp_path, chat_provider=chat_provider)
    kb = service.create_kb(owner_user_id="user-1", payload=KnowledgeBaseCreate(name="测试库"))
    _index_text_doc(service, kb_id=kb.kb_id, title="双碳文件", text="双碳目标包括碳达峰和碳中和。")

    result = service.test_qa(
        owner_user_id="user-1",
        request=RagSearchRequest(query="双碳目标包括什么？", kb_id=kb.kb_id, mode="hybrid", top_k=3),
    )

    assert result["answer_mode"] == "llm_grounded"
    assert result["provider_name"] == "fake-chat"
    assert result["selected_chunks"]
    assert result["citations"]
    assert result["retrieval_trace"]["kb_id"] == kb.kb_id
    assert chat_provider.calls
    assert "可用检索片段" in chat_provider.calls[0]["user_input"]
    assert "双碳目标包括碳达峰和碳中和" in chat_provider.calls[0]["user_input"]


def test_rag_test_qa_no_hits_does_not_call_provider(monkeypatch, tmp_path) -> None:
    chat_provider = FakeChatProvider()
    service = _build_rag_service(monkeypatch, tmp_path, chat_provider=chat_provider)
    kb = service.create_kb(owner_user_id="user-1", payload=KnowledgeBaseCreate(name="空库"))

    result = service.test_qa(
        owner_user_id="user-1",
        request=RagSearchRequest(query="没有资料的问题", kb_id=kb.kb_id, mode="hybrid", top_k=3),
    )

    assert result["answer_mode"] == "no_hits"
    assert result["selected_chunks"] == []
    assert result["citations"] == []
    assert result["retrieval_trace"]["degraded"] is True
    assert chat_provider.calls == []


def _build_selected_kb_chat_request(monkeypatch, *, kb_id: str, rag_mode: str) -> ChatRequest:
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: FakeSessionService())
    now = datetime.now(timezone.utc)
    user = AuthenticatedUser(
        user_id="user-1",
        username="tester",
        display_name="tester",
        role="user",
        is_active=True,
        password_must_change=False,
        created_at=now,
        updated_at=now,
    )
    chat_request, _ = build_chat_request(
        session_id="session-1",
        current_user=user,
        payload=AskRequest(question="测试问题", knowledge_scope="mixed", kb_id=kb_id, rag_mode=rag_mode),
    )
    return chat_request


def _prepare_runtime_with_capture(monkeypatch, chat_request: ChatRequest) -> CaptureRagTool:
    monkeypatch.setattr("app.ai_runtime.runtime.orchestrator.get_settings", lambda: SimpleNamespace(rag_langchain_enabled=True))
    capture_tool = CaptureRagTool()
    registry = ToolRegistry()
    registry.register(capture_tool)
    AIRuntimeOrchestrator(
        registry=registry,
        chat_provider=FakeChatProvider(),
        embedding_provider=FakeEmbeddingProvider(),
    )._prepare_runtime(chat_request)
    return capture_tool


def _build_rag_service(monkeypatch, tmp_path, *, chat_provider: FakeChatProvider | None = None) -> RagSpineService:
    monkeypatch.setattr("app.rag.spine.get_settings", lambda: SimpleNamespace(rag_vector_backend="memory", rag_milvus_uri=None))
    return RagSpineService(
        store=RagKnowledgeStore(sqlite_db_path=tmp_path / "carbonrag.sqlite3"),
        chat_provider=chat_provider or FakeChatProvider(),
    )


def _index_text_doc(service: RagSpineService, *, kb_id: str, title: str, text: str) -> None:
    doc = service.create_document(
        owner_user_id="user-1",
        kb_id=kb_id,
        payload=RagDocumentCreate(title=title, text=text, source_type="manual"),
    )
    service.parse_document(owner_user_id="user-1", kb_id=kb_id, doc_id=doc.doc_id)
    service.chunk_document(owner_user_id="user-1", kb_id=kb_id, doc_id=doc.doc_id)
    service.index_document(owner_user_id="user-1", kb_id=kb_id, doc_id=doc.doc_id)
