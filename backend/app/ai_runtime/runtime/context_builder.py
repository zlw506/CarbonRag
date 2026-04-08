from app.ai_runtime.modes import ModeSpec
from app.ai_runtime.schemas.chat import ChatRequest
from app.ai_runtime.schemas.tool import ToolResult


def _extract_hits(tool_results: list[ToolResult] | None) -> list[dict]:
    if not tool_results:
        return []

    hits: list[dict] = []
    for tool_result in tool_results:
        tool_hits = tool_result.output.get("hits", [])
        if isinstance(tool_hits, list):
            hits.extend(hit for hit in tool_hits if isinstance(hit, dict))
    return hits


def build_context_bundle(
    request: ChatRequest,
    mode: ModeSpec,
    *,
    tool_results: list[ToolResult] | None = None,
) -> dict:
    if mode.name == "ask":
        knowledge_scope_requested = request.payload.get("knowledge_scope_requested", "public")
        knowledge_scope_effective = request.payload.get("knowledge_scope_effective", "public")
        session_context = request.payload.get("session_context", [])
        retrieval_hits = _extract_hits(tool_results)
        public_hits = [hit for hit in retrieval_hits if hit.get("source_type") == "public_policy"]
        private_hits = [hit for hit in retrieval_hits if hit.get("source_type") == "private_sample"]

        limitations = [
            "不得伪造引用，也不得声称访问了未检索到的外部证据。",
            "private sample 当前只是脱敏演示样例，不代表真实客户审计结果。",
            "上传文件本轮不会进入 retrieval，只作为 session 绑定资产展示。",
        ]

        if session_context:
            session_context_lines = ["最近单会话历史如下，请仅用于延续当前会话上下文："]
            for index, message in enumerate(session_context, start=1):
                if not isinstance(message, dict):
                    continue
                role = message.get("role", "unknown")
                content = message.get("content", "")
                session_context_lines.append(f"[history-{index}] {role}: {content}")
        else:
            session_context_lines = ["当前会话历史为空，这是本轮对话的起点。"]

        evidence_lines: list[str] = []
        if public_hits:
            evidence_lines.append("当前已检索到以下公共政策片段：")
            for index, hit in enumerate(public_hits, start=1):
                evidence_lines.extend(
                    [
                        f"[policy-{index}] 标题：{hit['title']}",
                        f"发布机构：{hit['source']}",
                        f"片段标识：{hit['chunk_id']}",
                        f"片段内容：{hit['snippet']}",
                    ]
                )
        if private_hits:
            evidence_lines.append("当前已检索到以下脱敏企业样例片段：")
            for index, hit in enumerate(private_hits, start=1):
                evidence_lines.extend(
                    [
                        f"[private-{index}] 标题：{hit['title']}",
                        f"来源：{hit['source']}",
                        f"片段标识：{hit['chunk_id']}",
                        f"片段内容：{hit['snippet']}",
                    ]
                )
        if not evidence_lines:
            evidence_lines = [
                "当前未检索到足够依据。",
                "不得伪造引用，只能明确说明当前 scope 下未命中足够证据，并给出受限说明。",
            ]

        if knowledge_scope_effective == "public":
            scope_strategy_lines = [
                "当前策略：仅检索本地公共政策样本，再基于命中的政策片段回答。",
                "不得声称使用了企业样例或上传附件。",
            ]
        elif knowledge_scope_effective == "private_sample":
            scope_strategy_lines = [
                "当前策略：仅检索当前 session 已关联的脱敏企业样例。",
                "必须明确这些样例仅用于演示，不代表真实企业审计结果。",
            ]
        else:
            scope_strategy_lines = [
                "当前策略：同时参考公共政策依据和当前 session 已关联的脱敏企业样例。",
                "回答时必须区分政策要求与样例现状，不能把企业样例当成政策依据。",
            ]

        return {
            "system_role": "CarbonRag 是一个面向中小企业的双碳问答 MVP。",
            "mode_name": "ask",
            "system_prompt": "\n".join(
                [
                    "你是 CarbonRag 的 ask mode 问答助手。",
                    "当前产品定位：面向中小企业的双碳问答 MVP。",
                    *session_context_lines,
                    *scope_strategy_lines,
                    "当前限制：未接入完整知识库、不得伪造引用。",
                    f"当前知识范围请求：{knowledge_scope_requested}。",
                    f"当前知识范围实际生效：{knowledge_scope_effective}。",
                    *evidence_lines,
                    "如果存在政策和样例两类依据，请分层表达“政策要求”与“样例现状”；如果片段不足，只能给出受限说明。",
                ]
            ),
            "user_question": request.user_input,
            "knowledge_scope_requested": knowledge_scope_requested,
            "knowledge_scope_effective": knowledge_scope_effective,
            "session_context": session_context,
            "policy_context": {
                "ready": True,
                "source": "local_public_policy_corpus",
                "hit_count": len(public_hits),
                "hits": public_hits,
            },
            "enterprise_context": {
                "ready": True,
                "source": "local_private_sample_corpus",
                "hit_count": len(private_hits),
                "hits": private_hits,
            },
            "limitations": limitations,
            "session_state": {
                "trace_id": request.trace_id,
                "mode": mode.name,
            },
            "memory_slot": {
                "status": "reserved",
                "implemented": False,
            },
            "payload_keys": sorted(request.payload.keys()),
        }

    return {
        "policy_context": {
            "ready": mode.name in {"ask", "report"},
            "source": "policy_stub",
        },
        "enterprise_context": {
            "ready": mode.name in {"ask", "carbon", "report"},
            "source": "enterprise_stub",
        },
        "carbon_context": {
            "ready": mode.name == "carbon",
            "source": "carbon_stub",
        },
        "report_context": {
            "ready": mode.name == "report",
            "source": "report_stub",
        },
        "session_state": {
            "trace_id": request.trace_id,
            "mode": mode.name,
        },
        "memory_slot": {
            "status": "reserved",
            "implemented": False,
        },
        "payload_keys": sorted(request.payload.keys()),
    }
