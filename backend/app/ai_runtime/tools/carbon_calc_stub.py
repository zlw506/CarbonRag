from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition


class CarbonCalcStubTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="carbon_calc",
            description="Return carbon calculation placeholders from a controlled stub source."
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
                "total_emission": 0.0,
                "unit": "kgCO2e",
                "breakdown": [
                    {"item": "electricity", "value": 0.0},
                    {"item": "fuel", "value": 0.0}
                ]
            },
            metadata={"trace_id": trace_id}
        )
