import re
from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition
from app.carbon.factor_loader import CarbonFactorLoader, FactorLoadError
from app.carbon.factors.schema import FactorRecord


_ACTIVITY_ALIASES: dict[str, tuple[str, ...]] = {
    "electricity": ("外购电力", "用电", "电量", "电力", "购电", "kwh", "度电", "purchased_electricity"),
    "natural_gas": ("天然气", "燃气", "natural gas", "natural_gas", "m3", "立方米"),
    "diesel": ("柴油", "diesel"),
    "gasoline": ("汽油", "gasoline"),
    "lpg": ("液化石油气", "lpg"),
    "coal": ("煤", "原煤", "coal"),
    "steam": ("蒸汽", "steam"),
    "water": ("自来水", "用水", "water"),
}


def _normalize_query(value: Any) -> str:
    return str(value or "").strip().lower()


def _query_terms(query: str) -> list[str]:
    normalized = _normalize_query(query)
    terms = {item for item in re.split(r"[\s,，。；;:：/\\|()\[\]{}<>《》、]+", normalized) if item}
    for canonical, aliases in _ACTIVITY_ALIASES.items():
        if any(alias.lower() in normalized for alias in aliases):
            terms.add(canonical)
            terms.update(alias.lower() for alias in aliases)
    # Keep short Chinese trigger words as substring probes; word splitting does
    # not help much for "外购电力排放因子" style queries.
    for probe in ("外购电力", "天然气", "柴油", "汽油", "液化石油气", "蒸汽", "煤", "碳因子", "排放因子"):
        if probe in normalized:
            terms.add(probe)
    return sorted(terms, key=len, reverse=True)


def _record_haystack(record: FactorRecord) -> str:
    fields = [
        record.factor_id,
        record.factor_version,
        record.source_type,
        record.source_name,
        record.scope,
        record.activity_category,
        record.activity_name,
        record.region,
        record.region_code,
        record.region_name,
        record.method_type,
        record.applicable_industry,
        record.applicable_standard,
        record.quality_level,
        record.factor_unit,
        record.activity_unit,
        record.notes,
        " ".join(record.tags or []),
    ]
    return " ".join(str(item or "") for item in fields).lower()


def _score_record(record: FactorRecord, terms: list[str], query: str) -> float:
    haystack = _record_haystack(record)
    score = 0.0
    for term in terms:
        if not term:
            continue
        term_lower = term.lower()
        if term_lower == record.factor_id.lower():
            score += 100.0
        elif term_lower == (record.activity_name or "").lower():
            score += 45.0
        elif term_lower == (record.activity_category or "").lower():
            score += 30.0
        elif term_lower in haystack:
            score += 12.0 if len(term_lower) >= 3 else 5.0

    normalized_query = _normalize_query(query)
    if ("官方" in normalized_query or "国家" in normalized_query) and (record.is_official or record.source_type == "official"):
        score += 10.0
    if ("中国" in normalized_query or "全国" in normalized_query or "cn" in normalized_query) and (
        record.region == "CN" or record.region_code == "CN" or record.region_level == "national"
    ):
        score += 6.0
    if record.is_default:
        score += 2.0
    if record.is_official or record.source_type == "official":
        score += 4.0
    score += min(record.source_priority, 100) / 100.0
    return score


def _record_to_hit(record: FactorRecord, *, score: float) -> dict[str, Any]:
    year = record.effective_year or record.year
    region = record.region_name or record.region_code or record.region or "适用范围未标注"
    source = record.source_name or record.source_type
    factor_text = f"{record.factor_value:g} {record.factor_unit}"
    snippet = (
        f"{record.activity_name}（{record.activity_category}，{region}，{year or '年份未标注'}）"
        f" 的排放因子为 {factor_text}，来源：{source}。"
    )
    return {
        "doc_id": record.factor_id,
        "knowledge_item_id": record.factor_id,
        "chunk_id": record.factor_id,
        "title": f"{record.activity_name} 碳因子",
        "source_type": "carbon_factor",
        "source": source,
        "source_url": record.source_url,
        "snippet": snippet,
        "library_scope": "carbon_factor_library",
        "factor_id": record.factor_id,
        "factor_version": record.factor_version,
        "activity_name": record.activity_name,
        "activity_category": record.activity_category,
        "scope": record.scope,
        "factor_value": record.factor_value,
        "factor_unit": record.factor_unit,
        "activity_unit": record.activity_unit,
        "result_unit": record.result_unit,
        "region": record.region,
        "region_code": record.region_code,
        "region_name": record.region_name,
        "year": year,
        "source_name": source,
        "source_priority": record.source_priority,
        "is_official": record.is_official or record.source_type == "official",
        "score": round(score, 4),
    }


class CarbonFactorLookupTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="carbon_factor_lookup",
            description="Search CarbonRag local/runtime carbon factor library and return calculation-ready emission factors.",
            category="carbon_factor",
        )

    def invoke(
        self,
        *,
        arguments: Mapping[str, Any],
        context: Mapping[str, Any],
        trace_id: str
    ) -> ToolResult:
        del context
        query = _normalize_query(
            arguments.get("question") or arguments.get("user_input") or arguments.get("query")
        )
        try:
            top_k = int(arguments.get("top_k") or 5)
        except (TypeError, ValueError):
            top_k = 5
        top_k = min(max(top_k, 1), 10)
        terms = _query_terms(query)
        try:
            records = CarbonFactorLoader().load_registry().records
        except FactorLoadError as exc:
            return ToolResult(
                name=self.definition.name,
                status="error",
                output={
                    "query": query,
                    "hits": [],
                    "hit_count": 0,
                    "error": str(exc),
                },
                metadata={"trace_id": trace_id},
            )

        scored: list[tuple[float, FactorRecord]] = []
        for record in records:
            score = _score_record(record, terms, query)
            if score > 0:
                scored.append((score, record))
        if not scored and any(marker in query for marker in ("碳因子", "排放因子", "碳核算", "排放量")):
            scored = [
                (
                    1.0
                    + (4.0 if record.is_default else 0.0)
                    + (8.0 if record.is_official or record.source_type == "official" else 0.0)
                    + min(record.source_priority, 100) / 100.0,
                    record,
                )
                for record in records
                if record.is_default or record.is_official or record.source_type in {"official", "guidance_default"}
            ]

        scored.sort(
            key=lambda item: (
                item[0],
                int(item[1].is_official or item[1].source_type == "official"),
                item[1].effective_year or item[1].year or 0,
                item[1].source_priority,
            ),
            reverse=True,
        )
        hits = [_record_to_hit(record, score=score) for score, record in scored[:top_k]]
        warnings: list[str] = []
        if not hits:
            warnings.append("本地碳因子库未命中与问题直接相关的因子。")
        return ToolResult(
            name=self.definition.name,
            status="success",
            output={
                "query": query,
                "terms": terms,
                "hits": hits,
                "hit_count": len(hits),
                "warnings": warnings,
            },
            metadata={"trace_id": trace_id, "record_count": len(records)}
        )


# Backward-compatible import name; the implementation is no longer a stub.
CarbonFactorLookupStubTool = CarbonFactorLookupTool
