from app.ai_runtime.modes import ModeSpec
from app.ai_runtime.schemas.chat import ChatRequest


def build_context_bundle(request: ChatRequest, mode: ModeSpec) -> dict:
    return {
        "policy_context": {
            "ready": mode.name in {"ask", "report"},
            "source": "policy_stub"
        },
        "enterprise_context": {
            "ready": mode.name in {"ask", "carbon", "report"},
            "source": "enterprise_stub"
        },
        "carbon_context": {
            "ready": mode.name == "carbon",
            "source": "carbon_stub"
        },
        "report_context": {
            "ready": mode.name == "report",
            "source": "report_stub"
        },
        "session_state": {
            "trace_id": request.trace_id,
            "mode": mode.name
        },
        "memory_slot": {
            "status": "reserved",
            "implemented": False
        },
        "payload_keys": sorted(request.payload.keys())
    }
