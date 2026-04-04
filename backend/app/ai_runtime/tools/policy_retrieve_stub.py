from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition


class PolicyRetrieveStubTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="policy_retrieve",
            description="Retrieve policy snippets from a controlled stub source."
        )

    def invoke(
        self,
        *,
        arguments: Mapping[str, Any],
        context: Mapping[str, Any],
        trace_id: str
    ) -> ToolResult:
        return ToolResult(
            name=self.definition.name,
            status="stub",
            output={
                "policy_hits": [
                    "双碳政策占位摘要",
                    "政策条文检索 stub 结果"
                ],
                "query": arguments.get("user_input", "")
            },
            metadata={"trace_id": trace_id, "context_keys": sorted(context)}
        )
