from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.ai_runtime.providers.chat_openai_compatible import OpenAICompatibleChatProvider
from app.ai_runtime.modes import resolve_mode
from app.ai_runtime.runtime.context_builder import build_context_bundle
from app.ai_runtime.schemas.chat import ChatRequest
from app.ai_runtime.schemas.tool import ToolResult
from app.main import app
from app.files.service import FileService
from app.files.storage import FileStorage
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import patch_test_auth_service, register_and_login


client = TestClient(app)


class FakeStreamingResponse:
    def __init__(self, *, status_code: int, lines: list[str]) -> None:
        self.status_code = status_code
        self._lines = lines

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def iter_lines(self):
        for line in self._lines:
            yield line


def test_context_builder_orders_summary_recent_messages_memory_and_grounding() -> None:
    request = ChatRequest(
        mode="ask",
        user_input="请继续说明双碳目标。",
        payload={
            "session_id": "session-demo",
            "recent_messages": [
                {"role": "user", "content": "先讲碳达峰。"},
                {"role": "assistant", "content": "碳达峰是排放达到峰值后进入下降。"},
            ],
            "session_summary": "用户已经理解碳达峰，正在继续询问双碳目标。",
            "memory_notes": [
                {"title": "表达偏好", "content": "回答尽量简洁。"},
            ],
            "context_usage_estimate": 1350,
            "context_budget_estimate": 258000,
            "compacted_message_count": 4,
            "compaction_status": "compacted",
            "knowledge_scope_requested": "mixed",
            "knowledge_scope_effective": "mixed",
            "top_k": 5,
            "attached_knowledge_item_ids": ["knowledge-item-1"],
        },
    )
    tool_results = [
        ToolResult(
            name="mixed_retrieve",
            status="success",
            output={
                "hits": [
                    {
                        "doc_id": "policy-001",
                        "title": "2030年前碳达峰行动方案",
                        "source_type": "public_policy",
                        "source": "国务院",
                        "source_url": "https://example.com/policy-001",
                        "snippet": "双碳目标是碳达峰和碳中和。",
                        "chunk_id": "policy-001_chunk_01",
                    },
                    {
                        "doc_id": "sample-001",
                        "title": "企业能耗样例",
                        "source_type": "private_sample",
                        "source": "脱敏企业样例",
                        "source_url": None,
                        "snippet": "企业当前月度电耗为 12000 kWh。",
                        "chunk_id": "sample-001_chunk_01",
                    },
                ]
            },
        )
    ]

    bundle = build_context_bundle(request, resolve_mode("ask"), tool_results=tool_results)
    system_prompt = bundle["system_prompt"]

    assert system_prompt.index("以下是当前会话的自动摘要") < system_prompt.index("[history-1]")
    assert system_prompt.index("[history-1]") < system_prompt.index("以下是用户级长期记忆预留条目")
    assert system_prompt.index("以下是用户级长期记忆预留条目") < system_prompt.index("当前已检索到以下公共政策片段")
    assert "不要使用 Markdown 的 # / ## / ### 标题" in system_prompt
    assert "优先使用 Markdown 表格" in system_prompt
    assert "先给一句结论" in system_prompt
    assert "当前未检索到足够依据。" not in system_prompt
    assert bundle["policy_context"]["hit_count"] == 1
    assert bundle["enterprise_context"]["hit_count"] == 1
    assert bundle["session_state"]["compaction_status"] == "compacted"
    assert bundle["session_state"]["compacted_message_count"] == 4


def test_context_builder_keeps_selected_upload_hits_with_rag_pro_enabled() -> None:
    request = ChatRequest(
        mode="ask",
        user_input="你看不见我上传的文件吗？",
        payload={
            "session_id": "session-upload",
            "recent_messages": [],
            "knowledge_scope_requested": "public",
            "knowledge_scope_effective": "public",
            "attached_file_knowledge_item_ids": ["file-knowledge-1"],
            "kb_id": "kb-default",
            "rag_mode": "hybrid_rerank",
        },
    )
    tool_results = [
        ToolResult(
            name="rag_pro_search",
            status="success",
            output={"hits": [], "retrieval_trace": {"kb_id": "kb-default", "merged_count": 0}},
        ),
        ToolResult(
            name="session_file_search",
            status="success",
            output={
                "hits": [
                    {
                        "doc_id": "file-knowledge-1",
                        "knowledge_item_id": "file-knowledge-1",
                        "title": "按项目生命周期描述我经历的一个项目.docx",
                        "source_type": "private_upload",
                        "source": "用户上传文件",
                        "source_url": None,
                        "snippet": "项目经历包括需求分析、方案设计、实现与验收。",
                        "chunk_id": "chunk-upload-1",
                        "file_id": "file-1",
                    }
                ],
            },
        ),
    ]

    bundle = build_context_bundle(request, resolve_mode("ask"), tool_results=tool_results)
    system_prompt = bundle["system_prompt"]

    assert "当前已检索到以下私有知识或上传文件片段" in system_prompt
    assert "项目经历包括需求分析、方案设计、实现与验收" in system_prompt
    assert "不要再声称无法读取该文件" in system_prompt
    assert "当前未检索到足够依据。" not in system_prompt
    assert bundle["enterprise_context"]["hit_count"] == 1


def test_context_builder_injects_selected_upload_file_overview() -> None:
    request = ChatRequest(
        mode="ask",
        user_input="根据上传报告回答表格中的排放数据。",
        payload={
            "session_id": "session-upload",
            "recent_messages": [],
            "knowledge_scope_requested": "public",
            "knowledge_scope_effective": "public",
            "attached_file_knowledge_item_ids": ["file-knowledge-1"],
        },
    )
    tool_results = [
        ToolResult(
            name="session_file_search",
            status="success",
            output={
                "hits": [],
                "file_overviews": [
                    {
                        "knowledge_item_id": "file-knowledge-1",
                        "title": "企业双碳评估报告.docx",
                        "source": "用户上传知识",
                        "chunk_count": 8,
                        "table_like_chunk_count": 2,
                        "numeric_chunk_count": 5,
                        "chunks": [
                            {
                                "chunk_id": "chunk-table-1",
                                "content_kind": "table_or_structured",
                                "page_number": 4,
                                "section_title": "排放明细表",
                                "snippet": "指标=外购电力 | 数值=7800 | 单位=MWh | 占比=65%",
                            }
                        ],
                    }
                ],
            },
        ),
    ]

    bundle = build_context_bundle(request, resolve_mode("ask"), tool_results=tool_results)
    system_prompt = bundle["system_prompt"]

    assert "当前显式选择的上传文件结构化摘录如下" in system_prompt
    assert "指标=外购电力" in system_prompt
    assert "排放明细表" in system_prompt
    assert "只有摘录和命中片段都缺失时，才说明材料不足" in system_prompt
    assert bundle["enterprise_context"]["file_overview_count"] == 1


def test_chat_provider_stream_response_emits_thinking_and_answer_chunks(monkeypatch) -> None:
    def fake_stream(method: str, url: str, *, headers: dict, json: dict, timeout: float):
        del method, url, headers, json, timeout
        return FakeStreamingResponse(
            status_code=200,
            lines=[
                'event: reasoning',
                'data: {"id":"chatcmpl-stream","choices":[{"delta":{"reasoning_content":"先梳理上下文。"}}]}',
                "",
                'event: message',
                'data: {"id":"chatcmpl-stream","choices":[{"delta":{"content":"双碳目标是碳达峰和碳中和。"}}],"usage":{"prompt_tokens":12,"completion_tokens":18}}',
                "",
                "data: [DONE]",
            ],
        )

    monkeypatch.setattr("app.ai_runtime.providers.chat_openai_compatible.httpx.stream", fake_stream)

    provider = OpenAICompatibleChatProvider(
        base_url="https://example.com/v1",
        api_key="demo-key",
        model_name="gpt-5.4",
        temperature=0.2,
        max_tokens=4096,
        timeout_seconds=30.0,
    )

    events = list(
        provider.stream_response(
            system_prompt="你是 CarbonRag 的 ask mode 问答助手。",
            user_input="什么是双碳目标？",
        )
    )

    assert [event.kind for event in events[:4]] == ["status", "thinking_delta", "status", "answer_delta"]
    assert events[0].data["status"] == "thinking"
    assert events[1].data["delta"] == "先梳理上下文。"
    assert events[2].data["status"] == "streaming"
    assert events[3].data["delta"] == "双碳目标是碳达峰和碳中和。"
    assert events[-1].kind == "done"
    assert events[-1].data["metadata"]["thinking_chunk_count"] == 1
    assert events[-1].data["metadata"]["answer_chunk_count"] == 1
    assert events[-1].data["metadata"]["transport"] == "streaming_sse_aggregate"


def test_session_ask_stream_contract_emits_sse_sequence(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    session_service = SessionService(store=SQLiteSessionStore(db_path))
    file_service = FileService(
        session_service=session_service,
        storage=FileStorage(tmp_path / "uploads"),
    )
    patch_test_auth_service(monkeypatch, db_path=db_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.files.get_file_service", lambda: file_service)

    def fake_stream(method: str, url: str, *, headers: dict, json: dict, timeout: float):
        del method, url, headers, json, timeout
        return FakeStreamingResponse(
            status_code=200,
            lines=[
                'event: reasoning',
                'data: {"id":"chatcmpl-stream-contract","choices":[{"delta":{"reasoning_content":"先检查会话上下文。"}}]}',
                "",
                'event: message',
                'data: {"id":"chatcmpl-stream-contract","choices":[{"delta":{"content":"双碳目标包括碳达峰和碳中和。"}}]}',
                "",
                "data: [DONE]",
            ],
        )

    monkeypatch.setattr("app.ai_runtime.providers.chat_openai_compatible.httpx.stream", fake_stream)

    register_and_login(client, prefix="stream-contract")
    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]

    with client.stream(
        "POST",
        f"/api/v1/sessions/{session_id}/ask/stream",
        json={
            "question": "什么是双碳目标？",
            "knowledge_scope": "public",
            "top_k": 3,
        },
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())
        assert "event: message_start" in body
        assert "event: status" in body
        assert "event: thinking_delta" in body
        assert "event: answer_delta" in body
        assert "event: metadata" in body
        assert "event: done" in body

    detail = client.get(f"/api/v1/sessions/{session_id}").json()
    assert detail["messages"][-1]["role"] == "assistant"
    assert detail["messages"][-1]["status"] == "done"
    assert detail["messages"][-1]["trace_id"]
    assert detail["messages"][-1]["citations"]
    assert detail["memory_state"]["compaction_status"] in {"idle", "compacted"}
