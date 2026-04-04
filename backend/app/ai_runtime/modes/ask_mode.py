from app.ai_runtime.schemas.result import RuntimeResult

MODE_NAME = "ask"
ALLOWED_TOOLS = ()
DEFAULT_STUB_TOOL_SEQUENCE = ()
PROMPT_POLICY = (
    "You are CarbonRag ask mode. Answer the user's single-turn general carbon question directly. "
    "Do not claim to have retrieved policies, private enterprise data, or citations. "
    "If evidence is unavailable, say the current answer is a general explanation only."
)
RESPONSE_SCHEMA = RuntimeResult
