from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    category: str = "business_stub"


class BaseTool(ABC):
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        raise NotImplementedError

    @abstractmethod
    def invoke(
        self,
        *,
        arguments: Mapping[str, Any],
        context: Mapping[str, Any],
        trace_id: str
    ) -> ToolResult:
        raise NotImplementedError
