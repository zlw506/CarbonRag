from app.ai_runtime.schemas.result import RuntimeResult

MODE_NAME = "ask"
ALLOWED_TOOLS = (
    "policy_retrieve",
    "enterprise_retrieve",
    "mixed_retrieve",
    "session_file_search",
    "rag_pro_search",
    "rag_pro_answer",
    "langchain_rag_search",
    "langchain_rag_answer",
    "report_carbon_extract_calc",
)
DEFAULT_STUB_TOOL_SEQUENCE = ("policy_retrieve",)
PROMPT_POLICY = (
    "You are CarbonRag ask mode. Always ground the answer in retrieved snippets first. "
    "Respect the effective knowledge scope, do not invent citations, and do not imply access beyond the provided evidence. "
    "If retrieval returns no usable evidence, answer conservatively and say the current system lacks enough basis in the current scope. "
    "Do not use Markdown # headings; use concise bold section labels, numbered steps, bullet lists, and tables when comparison or numeric data is involved."
)
RESPONSE_SCHEMA = RuntimeResult
