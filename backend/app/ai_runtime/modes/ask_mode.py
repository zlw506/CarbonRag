from app.ai_runtime.schemas.result import RuntimeResult

MODE_NAME = "ask"
ALLOWED_TOOLS = ("policy_retrieve",)
DEFAULT_STUB_TOOL_SEQUENCE = ("policy_retrieve",)
PROMPT_POLICY = (
    "You are CarbonRag ask mode. Always ground the answer in retrieved public policy snippets first. "
    "Do not claim private enterprise data access, do not invent citations, and do not imply full RAG coverage. "
    "If policy retrieval returns no usable evidence, answer conservatively and say the current system lacks enough policy basis."
)
RESPONSE_SCHEMA = RuntimeResult
