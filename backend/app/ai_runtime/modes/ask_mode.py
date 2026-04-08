from app.ai_runtime.schemas.result import RuntimeResult

MODE_NAME = "ask"
ALLOWED_TOOLS = ("policy_retrieve", "enterprise_retrieve", "mixed_retrieve")
DEFAULT_STUB_TOOL_SEQUENCE = ("policy_retrieve",)
PROMPT_POLICY = (
    "You are CarbonRag ask mode. Always ground the answer in retrieved snippets first. "
    "Respect the effective knowledge scope, do not invent citations, and do not imply access beyond the provided evidence. "
    "If retrieval returns no usable evidence, answer conservatively and say the current system lacks enough basis in the current scope."
)
RESPONSE_SCHEMA = RuntimeResult
