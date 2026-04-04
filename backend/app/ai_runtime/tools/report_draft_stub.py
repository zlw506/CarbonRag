from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition


class ReportDraftStubTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="report_draft",
            description="Return report drafting placeholders from a controlled stub source."
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
                "format": "markdown",
                "content": "# CarbonRag Report Stub\n\nThis is a report draft placeholder."
            },
            metadata={"trace_id": trace_id}
        )
