from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition


class EnterpriseRetrieveStubTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="enterprise_retrieve",
            description="Retrieve enterprise sample context from a controlled stub source."
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
                "enterprise_profile": "脱敏企业样例上下文",
                "payload_keys": sorted(arguments.get("payload", {}).keys())
            },
            metadata={"trace_id": trace_id}
        )
