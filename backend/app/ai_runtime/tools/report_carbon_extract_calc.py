from __future__ import annotations

from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition
from app.carbon.report_extraction import ReportCarbonCalculationService
from app.knowledge import get_knowledge_service
from app.knowledge.schemas import KnowledgeChunk


class ReportCarbonExtractCalcTool(BaseTool):
    def __init__(self, service: ReportCarbonCalculationService | None = None) -> None:
        self._service = service

    @property
    def service(self) -> ReportCarbonCalculationService:
        if self._service is None:
            self._service = ReportCarbonCalculationService()
        return self._service

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="report_carbon_extract_calc",
            description="Extract carbon activity quantities from selected uploaded reports and calculate emissions.",
            category="carbon_report_extraction",
        )

    def invoke(
        self,
        *,
        arguments: Mapping[str, Any],
        context: Mapping[str, Any],
        trace_id: str,
    ) -> ToolResult:
        payload = arguments.get("payload", {})
        owner_user_id = str(payload.get("owner_user_id") or "")
        session_id = _optional_str(payload.get("session_id"))
        allowed_ids = _resolve_allowed_knowledge_item_ids(payload)
        if not owner_user_id:
            return _empty_result(
                trace_id=trace_id,
                status="skipped_missing_owner",
                warnings=["缺少 owner_user_id，已跳过报告碳活动抽取。"],
                context=context,
            )
        if not allowed_ids:
            return _empty_result(
                trace_id=trace_id,
                status="skipped_no_selected_uploads",
                warnings=["本轮未选择已解析上传文件，无法从报告中抽取碳活动数据。"],
                context=context,
            )

        chunks = _load_selected_upload_chunks(owner_user_id=owner_user_id, allowed_ids=allowed_ids)
        if not chunks:
            return _empty_result(
                trace_id=trace_id,
                status="skipped_no_chunks",
                warnings=["已选择上传文件，但没有找到可用于抽取的已解析 private_upload chunk。"],
                context=context,
            )

        result = self.service.extract_and_calculate(
            owner_user_id=owner_user_id,
            session_id=session_id,
            chunks=chunks,
        )
        hits = [
            extracted.to_hit(index=index)
            for index, extracted in enumerate(result.extracted_activities, start=1)
        ]
        output = result.to_output()
        output.update(
            {
                "query": str(arguments.get("question") or arguments.get("user_input") or ""),
                "hits": hits,
                "retrieval_trace": {
                    "tool": self.definition.name,
                    "selected_knowledge_item_count": len(allowed_ids),
                    "inspected_chunk_count": len(chunks),
                    "extracted_activity_count": len(result.extracted_activities),
                    "calculation_status": result.status,
                    "calculation_trace_id": result.calculation.trace_id if result.calculation else None,
                    "warnings": result.warnings,
                },
            }
        )
        return ToolResult(
            name=self.definition.name,
            status="success",
            output=output,
            metadata={
                "trace_id": trace_id,
                "hit_count": len(hits),
                "context_keys": sorted(context),
                "calculation_status": result.status,
            },
        )


def _resolve_allowed_knowledge_item_ids(payload: Mapping[str, Any]) -> set[str]:
    raw = payload.get("attached_file_knowledge_item_ids") or payload.get("attached_knowledge_item_ids") or []
    return {str(item).strip() for item in raw if str(item).strip()}


def _load_selected_upload_chunks(*, owner_user_id: str, allowed_ids: set[str]) -> list[KnowledgeChunk]:
    knowledge_service = get_knowledge_service()
    chunks = knowledge_service.list_chunks(knowledge_item_ids=sorted(allowed_ids))
    selected = [
        chunk for chunk in chunks
        if chunk.knowledge_item_id in allowed_ids
        and chunk.source_type == "private_upload"
        and (chunk.owner_user_id in {None, owner_user_id})
    ]
    selected.sort(key=lambda chunk: (chunk.knowledge_item_id, chunk.order_index))
    return selected


def _empty_result(*, trace_id: str, status: str, warnings: list[str], context: Mapping[str, Any]) -> ToolResult:
    return ToolResult(
        name="report_carbon_extract_calc",
        status="success",
        output={
            "status": status,
            "extracted_activity_count": 0,
            "extracted_activities": [],
            "calculation": None,
            "warnings": warnings,
            "hits": [],
            "retrieval_trace": {
                "tool": "report_carbon_extract_calc",
                "selected_knowledge_item_count": 0,
                "inspected_chunk_count": 0,
                "extracted_activity_count": 0,
                "calculation_status": status,
                "warnings": warnings,
            },
        },
        metadata={"trace_id": trace_id, "hit_count": 0, "context_keys": sorted(context), "calculation_status": status},
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
