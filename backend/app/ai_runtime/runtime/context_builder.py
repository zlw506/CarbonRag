from app.ai_runtime.modes import ModeSpec
from app.ai_runtime.schemas.chat import ChatRequest
from app.ai_runtime.schemas.tool import ToolResult


def _extract_policy_hits(tool_results: list[ToolResult] | None) -> list[dict]:
    if not tool_results:
        return []

    for tool_result in tool_results:
        if tool_result.name != "policy_retrieve":
            continue
        hits = tool_result.output.get("hits", [])
        if isinstance(hits, list):
            return [hit for hit in hits if isinstance(hit, dict)]
    return []


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
        policy_hits = _extract_policy_hits(tool_results)

        limitations = [
            "当前未接入企业私有数据。",
            "当前 citations 仅来自本地公共政策样本语料。",
            "不得伪造引用，也不得声称访问了未检索到的外部证据。",
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

        if policy_hits:
            policy_context_lines = ["当前已检索到以下公共政策片段，请优先基于这些片段作答："]
            for index, hit in enumerate(policy_hits, start=1):
                policy_context_lines.extend(
                    [
                        f"[{index}] 标题：{hit['title']}",
                        f"发布机构：{hit['source']}",
                        f"片段标识：{hit['chunk_id']}",
                        f"片段内容：{hit['snippet']}",
                    ]
                )
        else:
            policy_context_lines = [
                "当前未检索到足够政策依据。",
                "不得伪造引用，只能明确说明当前政策样本未命中足够证据，并给出受限说明。",
            ]

        return {
            "system_role": "CarbonRag 是一个面向中小企业的双碳问答 MVP。",
            "mode_name": "ask",
            "system_prompt": "\n".join(
                [
                    "你是 CarbonRag 的 ask mode 问答助手。",
                    "当前产品定位：面向中小企业的双碳问答 MVP。",
                    *session_context_lines,
                    "当前策略：先检索本地公共政策样本，再基于命中的政策片段回答。",
                    "当前限制：未接入企业私有数据、未接入完整知识库、不得伪造引用。",
                    f"当前知识范围请求：{knowledge_scope_requested}。",
                    f"当前知识范围实际生效：{knowledge_scope_effective}。",
                    *policy_context_lines,
                    "请优先根据上述政策片段作答；如果片段不足，只能给出受限说明，不得编造政策依据。",
                ]
            ),
            "user_question": request.user_input,
            "knowledge_scope_requested": knowledge_scope_requested,
            "knowledge_scope_effective": knowledge_scope_effective,
            "session_context": session_context,
            "policy_context": {
                "ready": True,
                "source": "local_public_policy_corpus",
                "hit_count": len(policy_hits),
                "hits": policy_hits,
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
