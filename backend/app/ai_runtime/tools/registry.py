from app.ai_runtime.tools.base import BaseTool
from app.ai_runtime.tools.carbon_calc_stub import CarbonCalcStubTool
from app.ai_runtime.tools.carbon_factor_lookup_stub import CarbonFactorLookupTool
from app.ai_runtime.tools.enterprise_retrieve import EnterpriseRetrieveTool
from app.ai_runtime.tools.mixed_retrieve import MixedRetrieveTool
from app.ai_runtime.tools.policy_retrieve import PolicyRetrieveTool
from app.ai_runtime.tools.report_carbon_extract_calc import ReportCarbonExtractCalcTool
from app.ai_runtime.tools.report_draft_stub import ReportDraftStubTool
from app.ai_runtime.tools.session_file_search import SessionFileSearchTool
from app.langchain_rag.tool import LangChainRagAnswerTool, LangChainRagSearchTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        tool_name = tool.definition.name
        if tool_name in self._tools:
            raise ValueError(f"Tool already registered: {tool_name}")
        self._tools[tool_name] = tool

    def get(self, tool_name: str) -> BaseTool:
        try:
            return self._tools[tool_name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {tool_name}") from exc

    def list_tool_names(self) -> list[str]:
        return sorted(self._tools)

    def invoke(self, tool_name: str, *, arguments: dict, context: dict, trace_id: str):
        tool = self.get(tool_name)
        return tool.invoke(arguments=arguments, context=context, trace_id=trace_id)


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for tool in (
        PolicyRetrieveTool(),
        EnterpriseRetrieveTool(),
        MixedRetrieveTool(),
        SessionFileSearchTool(),
        LangChainRagSearchTool(tool_name="rag_pro_search"),
        LangChainRagAnswerTool(tool_name="rag_pro_answer"),
        LangChainRagSearchTool(),
        LangChainRagAnswerTool(),
        ReportCarbonExtractCalcTool(),
        CarbonFactorLookupTool(),
        CarbonCalcStubTool(),
        ReportDraftStubTool(),
    ):
        registry.register(tool)
    return registry
