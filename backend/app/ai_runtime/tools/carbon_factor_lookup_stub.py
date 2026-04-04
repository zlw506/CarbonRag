from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition


class CarbonFactorLookupStubTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="carbon_factor_lookup",
            description="Return emission factor placeholders from a controlled stub source."
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
                "factor_name": "electricity_grid_factor_stub",
                "factor_value": 0.0,
                "unit": "kgCO2e/unit"
            },
            metadata={"trace_id": trace_id}
        )
