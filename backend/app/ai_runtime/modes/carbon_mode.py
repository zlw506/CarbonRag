from app.ai_runtime.schemas.result import RuntimeResult

MODE_NAME = "carbon"
ALLOWED_TOOLS = ("enterprise_retrieve", "carbon_factor_lookup", "carbon_calc")
DEFAULT_STUB_TOOL_SEQUENCE = ("enterprise_retrieve", "carbon_factor_lookup", "carbon_calc")
PROMPT_POLICY = "Focus on carbon input normalization and factor lookup stubs. Do not draft reports."
RESPONSE_SCHEMA = RuntimeResult
