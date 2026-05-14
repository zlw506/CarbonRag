import re
from pathlib import Path
from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition
from app.carbon.factor_loader import CarbonFactorLoader, FactorLoadError
from app.carbon.factors.schema import FactorRecord


_SKILL_NAME = "carbon-factor-library"
_SKILL_INDEX_RELATIVE_PATH = (
    "backend/app/ai_runtime/agent_skills/carbon-factor-library/references/carbon-factor-index.md"
)
_SKILL_INDEX_PATH = Path(__file__).resolve().parents[1] / "agent_skills" / _SKILL_NAME / "references" / "carbon-factor-index.md"

_ACTIVITY_ALIASES: dict[str, tuple[str, ...]] = {
    "electricity": ("外购电力", "用电", "电量", "电力", "购电", "kwh", "度电", "purchased_electricity"),
    "natural_gas": ("天然气", "燃气", "natural gas", "natural_gas", "m3", "立方米"),
    "diesel": ("柴油", "diesel"),
    "gasoline": ("汽油", "gasoline"),
    "lpg": ("液化石油气", "lpg"),
    "coal": ("煤", "原煤", "coal"),
    "steam": ("蒸汽", "steam"),
    "water": ("自来水", "用水", "water"),
    "refrigerant": ("制冷剂", "冷媒", "r410a", "r134a", "refrigerant"),
}

_SCORING_STOP_TERMS = {
    "和",
    "及",
    "与",
    "或",
    "的",
    "碳因子",
    "排放因子",
    "碳核算",
    "排放量",
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
    for probe in ("外购电力", "天然气", "柴油", "汽油", "液化石油气", "蒸汽", "煤", "制冷剂", "碳因子", "排放因子"):
        if probe in normalized:
            terms.add(probe)
    return sorted(terms, key=len, reverse=True)


def _has_activity_probe(query: str) -> bool:
    normalized = _normalize_query(query)
    return any(alias.lower() in normalized for aliases in _ACTIVITY_ALIASES.values() for alias in aliases)


def _requested_activity_keys(query: str) -> list[str]:
    normalized = _normalize_query(query)
    return [
        canonical
        for canonical, aliases in _ACTIVITY_ALIASES.items()
        if any(alias.lower() in normalized for alias in aliases)
    ]


def _registry_summary(records: list[FactorRecord]) -> dict[str, Any]:
    activity_pairs = {
        (record.activity_category or "-", record.activity_name or "-")
        for record in records
    }
    categories = {record.activity_category for record in records if record.activity_category}
    official_count = sum(1 for record in records if record.is_official or record.source_type == "official")
    return {
        "record_count": len(records),
        "unique_activity_count": len(activity_pairs),
        "category_count": len(categories),
        "official_record_count": official_count,
        "index_path": _SKILL_INDEX_RELATIVE_PATH,
        "index_available": _SKILL_INDEX_PATH.exists(),
    }


def _should_return_generic_factor_defaults(query: str) -> bool:
    return any(marker in query for marker in ("碳因子", "排放因子", "碳核算", "排放量")) and not _has_activity_probe(query)


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
        if term_lower in _SCORING_STOP_TERMS:
            continue
        if term_lower == record.factor_id.lower():
            score += 100.0
        elif term_lower == (record.activity_name or "").lower():
            score += 45.0
        elif term_lower == (record.activity_category or "").lower():
            score += 30.0
        elif term_lower in (record.activity_name or "").lower():
            score += 25.0
        elif term_lower in (record.activity_category or "").lower():
            score += 25.0
        elif term_lower in haystack:
            score += 12.0 if len(term_lower) >= 3 else 5.0

    # Source quality is a tie-breaker, not a match criterion. Otherwise generic
    # queries containing "碳因子" cause every official electricity factor to
    # crowd out the actually requested categories such as steam or fuels.
    if score <= 0:
        return 0.0

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


def _group_key(record: FactorRecord) -> tuple[str, str]:
    activity_name = (record.activity_name or "").lower()
    activity_category = (record.activity_category or "").lower()
    combined = f"{activity_name} {activity_category}"
    if activity_name in {"electricity", "用电", "电力"} or activity_category == "电力" or "purchased_electricity" in combined:
        return ("canonical_activity", "electricity")
    if activity_name in {"natural_gas", "天然气"}:
        return ("canonical_activity", "natural_gas")
    if activity_name in {"diesel", "柴油"}:
        return ("canonical_activity", "diesel")
    if activity_name in {"gasoline", "汽油"}:
        return ("canonical_activity", "gasoline")
    if activity_name in {"lpg", "液化石油气"}:
        return ("canonical_activity", "lpg")
    if "煤" in combined or activity_name == "coal":
        return ("canonical_activity", "coal")
    if "蒸汽" in combined or activity_name == "steam":
        return ("canonical_activity", "steam")
    if "用水" in combined or "自来水" in combined or activity_name == "water":
        return ("canonical_activity", "water")
    if "制冷剂" in combined or "refrigerant" in combined:
        return ("canonical_activity", "refrigerant")
    return (record.activity_category or "", record.activity_name or "")


def _diverse_hits(scored: list[tuple[float, FactorRecord]], *, top_k: int) -> list[tuple[float, FactorRecord]]:
    grouped: dict[tuple[str, str], list[tuple[float, FactorRecord]]] = {}
    for score, record in scored:
        grouped.setdefault(_group_key(record), []).append((score, record))

    for values in grouped.values():
        values.sort(
            key=lambda item: (
                item[0],
                int(item[1].is_official or item[1].source_type == "official"),
                item[1].effective_year or item[1].year or 0,
                item[1].source_priority,
            ),
            reverse=True,
        )

    selected: list[tuple[float, FactorRecord]] = []
    seen: set[tuple[str, str]] = set()
    best_per_group = sorted(
        (values[0] for values in grouped.values()),
        key=lambda item: (
            item[0],
            int(item[1].is_official or item[1].source_type == "official"),
            item[1].effective_year or item[1].year or 0,
            item[1].source_priority,
        ),
        reverse=True,
    )
    for item in best_per_group:
        if len(selected) >= top_k:
            return selected
        selected.append(item)
        seen.add(_group_key(item[1]))

    for score, record in scored:
        if len(selected) >= top_k:
            return selected
        key = _group_key(record)
        if key in seen:
            selected.append((score, record))
    return selected


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
        requested_activity_keys = _requested_activity_keys(query)
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
                    "skill": {
                        "name": _SKILL_NAME,
                        "triggered": True,
                        "index_path": _SKILL_INDEX_RELATIVE_PATH,
                    },
                    "error": str(exc),
                },
                metadata={"trace_id": trace_id},
            )
        registry_summary = _registry_summary(records)

        scored: list[tuple[float, FactorRecord]] = []
        for record in records:
            score = _score_record(record, terms, query)
            if score > 0:
                scored.append((score, record))
        if not scored and _should_return_generic_factor_defaults(query):
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
        diverse_scored = _diverse_hits(scored, top_k=top_k)
        hits = [_record_to_hit(record, score=score) for score, record in diverse_scored]
        returned_activity_keys = sorted(
            {
                key[1]
                for _, record in diverse_scored
                for key in [_group_key(record)]
                if key[0] == "canonical_activity"
            }
        )
        missing_requested_activity_keys = [
            key for key in requested_activity_keys if key not in returned_activity_keys
        ]
        warnings: list[str] = []
        if not hits:
            warnings.append("本地碳因子库未命中与问题直接相关的因子。")
        if missing_requested_activity_keys:
            warnings.append(
                "以下活动在本轮按需检索中未返回计算就绪因子："
                + "、".join(missing_requested_activity_keys)
                + "。如当前注册表确无记录，不得编造因子。"
            )
        return ToolResult(
            name=self.definition.name,
            status="success",
            output={
                "query": query,
                "terms": terms,
                "skill": {
                    "name": _SKILL_NAME,
                    "triggered": True,
                    "index_path": _SKILL_INDEX_RELATIVE_PATH,
                    "index_available": _SKILL_INDEX_PATH.exists(),
                    "progressive_disclosure": "read factor-name index first, then query details for selected activities",
                },
                "registry": registry_summary,
                "requested_activity_keys": requested_activity_keys,
                "returned_activity_keys": returned_activity_keys,
                "missing_requested_activity_keys": missing_requested_activity_keys,
                "hits": hits,
                "hit_count": len(hits),
                "warnings": warnings,
            },
            metadata={"trace_id": trace_id, "record_count": len(records)}
        )


# Backward-compatible import name; the implementation is no longer a stub.
CarbonFactorLookupStubTool = CarbonFactorLookupTool
