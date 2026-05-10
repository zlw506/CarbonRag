from types import SimpleNamespace

from app.ai_runtime.runtime.orchestrator import AIRuntimeOrchestrator
from app.ai_runtime.schemas.chat import ChatRequest


def test_ask_tool_sequence_prefers_langchain_rag_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.ai_runtime.runtime.orchestrator.get_settings",
        lambda: SimpleNamespace(rag_langchain_enabled=True),
    )

    request = ChatRequest(
        mode="ask",
        user_input="双碳目标是什么？",
        payload={
            "knowledge_scope_effective": "mixed",
            "attached_file_knowledge_item_ids": ["file-ki"],
        },
    )

    assert AIRuntimeOrchestrator._resolve_ask_tool_sequence(request) == ("langchain_rag_search",)
