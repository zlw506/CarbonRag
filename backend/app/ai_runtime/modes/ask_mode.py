from app.ai_runtime.schemas.result import RuntimeResult

MODE_NAME = "ask"
ALLOWED_TOOLS = ("policy_retrieve", "enterprise_retrieve")
DEFAULT_STUB_TOOL_SEQUENCE = ("policy_retrieve", "enterprise_retrieve")
PROMPT_POLICY = "Answer with policy and enterprise retrieval stubs only. Do not perform carbon calculation or report drafting."
RESPONSE_SCHEMA = RuntimeResult
