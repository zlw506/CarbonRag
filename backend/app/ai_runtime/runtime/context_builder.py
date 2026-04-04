from app.ai_runtime.modes import ModeSpec
from app.ai_runtime.schemas.chat import ChatRequest


def build_context_bundle(request: ChatRequest, mode: ModeSpec) -> dict:
    if mode.name == "ask":
        knowledge_scope_requested = request.payload.get("knowledge_scope_requested", "public")
        knowledge_scope_effective = request.payload.get("knowledge_scope_effective", "public")
        limitations = [
            "当前未接入 RAG 检索。",
            "当前未接入企业私有数据。",
            "不得伪造引用或声称已检索外部证据。",
        ]
        return {
            "system_role": "CarbonRag 是一个面向中小企业的双碳问答 MVP。",
            "mode_name": "ask",
            "system_prompt": "\n".join(
                [
                    "你是 CarbonRag 的 ask mode 问答助手。",
                    "当前产品定位：面向中小企业的双碳问答 MVP。",
                    "当前限制：未接入 RAG、未接入企业私有数据、不得伪造引用。",
                    f"当前知识范围请求：{knowledge_scope_requested}。",
                    f"当前知识范围实际生效：{knowledge_scope_effective}。",
                    "请基于用户输入给出清晰、克制的通用双碳解释，并明确当前回答不附带检索引用。",
                ]
            ),
            "user_question": request.user_input,
            "knowledge_scope_requested": knowledge_scope_requested,
            "knowledge_scope_effective": knowledge_scope_effective,
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
