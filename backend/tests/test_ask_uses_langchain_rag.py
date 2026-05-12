from types import SimpleNamespace

from app.ai_runtime.runtime.orchestrator import AIRuntimeOrchestrator
from app.ai_runtime.schemas.chat import ChatRequest


def test_ask_tool_sequence_prefers_rag_pro_when_enabled(monkeypatch) -> None:
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

    assert AIRuntimeOrchestrator._resolve_ask_tool_sequence(request) == (
        "rag_pro_search",
        "session_file_search",
    )


def test_ask_tool_sequence_uses_only_rag_pro_without_selected_uploads(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.ai_runtime.runtime.orchestrator.get_settings",
        lambda: SimpleNamespace(rag_langchain_enabled=True),
    )

    request = ChatRequest(
        mode="ask",
        user_input="双碳目标是什么？",
        payload={"knowledge_scope_effective": "mixed"},
    )

    assert AIRuntimeOrchestrator._resolve_ask_tool_sequence(request) == ("rag_pro_search",)


def test_ask_tool_sequence_adds_report_carbon_extraction_for_selected_report(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.ai_runtime.runtime.orchestrator.get_settings",
        lambda: SimpleNamespace(rag_langchain_enabled=True),
    )

    request = ChatRequest(
        mode="ask",
        user_input="根据这份报告识别每类碳因子的量，并核算碳排放量。",
        payload={
            "knowledge_scope_effective": "mixed",
            "attached_file_knowledge_item_ids": ["file-ki"],
        },
    )

    assert AIRuntimeOrchestrator._resolve_ask_tool_sequence(request) == (
        "rag_pro_search",
        "session_file_search",
        "report_carbon_extract_calc",
    )
