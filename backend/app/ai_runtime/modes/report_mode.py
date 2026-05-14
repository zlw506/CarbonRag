from app.ai_runtime.schemas.result import RuntimeResult

MODE_NAME = "report"
ALLOWED_TOOLS = ("policy_retrieve", "enterprise_retrieve", "report_draft", "report_file_generate")
DEFAULT_STUB_TOOL_SEQUENCE = ("policy_retrieve", "enterprise_retrieve", "report_draft")
PROMPT_POLICY = "Use retrieval and report drafting stubs only. Do not execute arbitrary tools or system actions."
RESPONSE_SCHEMA = RuntimeResult
