from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from app.carbon.factor_loader import CarbonFactorLoader, get_factor_loader
from app.carbon.factors.schema import FactorRecord
from app.carbon.schemas import CalcCarbonRequest, CalcCarbonResponse, CarbonActivityItem
from app.carbon.service import CarbonService, get_carbon_service
from app.knowledge.schemas import KnowledgeChunk


_NUMBER = r"(?P<value>\d+(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)"
_SUPPORTED_UNITS = (
    "人·公里",
    "人-公里",
    "人公里",
    "人千米",
    "吨·公里",
    "吨-公里",
    "吨公里",
    "千瓦时",
    "立方米",
    "平方米",
    "平方公里",
    "kg",
    "kWh",
    "kw·h",
    "MWh",
    "m³",
    "m3",
    "m²",
    "m2",
    "㎡",
    "km",
    "公里",
    "千米",
    "tkm",
    "pkm",
    "L",
    "l",
    "升",
    "t",
    "吨",
    "千克",
    "公斤",
    "g",
    "克",
    "件",
    "个",
    "台",
    "张",
    "只",
    "次",
    "人次",
    "间夜",
    "度",
    "方",
)
_UNIT = r"(?P<unit>" + "|".join(re.escape(unit) for unit in sorted(_SUPPORTED_UNITS, key=len, reverse=True)) + r")"
_VALUE_THEN_UNIT_RE = re.compile(_NUMBER + r"\s*" + _UNIT, re.IGNORECASE)
_UNIT_THEN_VALUE_RE = re.compile(_UNIT + r"[\s:：）\)]{0,8}" + _NUMBER, re.IGNORECASE)
_TABLE_VALUE_UNIT_RE = re.compile(
    r"(?:数值|数量|消耗量|用量|活动量|value|amount|quantity)\s*(?:=|:|：)?\s*"
    + _NUMBER
    + r"(?:\s*\|\s*|\s{1,12}|[,，;；])"
    + r"(?:单位|unit)\s*(?:=|:|：)?\s*"
    + _UNIT,
    re.IGNORECASE,
)
_TABLE_UNIT_VALUE_RE = re.compile(
    r"(?:单位|unit)\s*(?:=|:|：)?\s*"
    + _UNIT
    + r"(?:\s*\|\s*|\s{1,12}|[,，;；])"
    + r"(?:数值|数量|消耗量|用量|活动量|value|amount|quantity)\s*(?:=|:|：)?\s*"
    + _NUMBER,
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ActivityPattern:
    scope: str
    activity_category: str
    activity_name: str
    canonical_unit: str
    aliases: tuple[str, ...]
    factor_preference: str
    region: str | None = None
    scope2_method: str = "location_based"


@dataclass(frozen=True)
class ExtractedReportActivity:
    activity: CarbonActivityItem
    title: str
    chunk_id: str
    knowledge_item_id: str
    file_id: str | None
    page_number: int | None
    sheet_name: str | None
    slide_number: int | None
    section_title: str | None
    snippet: str
    confidence: float
    matched_alias: str

    def to_output(self) -> dict:
        payload = self.activity.model_dump(mode="json")
        payload.update(
            {
                "title": self.title,
                "chunk_id": self.chunk_id,
                "knowledge_item_id": self.knowledge_item_id,
                "file_id": self.file_id,
                "page_number": self.page_number,
                "sheet_name": self.sheet_name,
                "slide_number": self.slide_number,
                "section_title": self.section_title,
                "snippet": self.snippet,
                "confidence": self.confidence,
                "matched_alias": self.matched_alias,
            }
        )
        return payload

    def to_hit(self, *, index: int) -> dict:
        return {
            "reference_id": f"report-carbon-{index}",
            "doc_id": self.knowledge_item_id,
            "knowledge_item_id": self.knowledge_item_id,
            "title": self.title,
            "source_type": "private_upload",
            "source": "用户上传报告",
            "source_url": None,
            "library_scope": "personal",
            "file_id": self.file_id,
            "page_number": self.page_number,
            "sheet_name": self.sheet_name,
            "slide_number": self.slide_number,
            "section_title": self.section_title,
            "chunk_id": self.chunk_id,
            "snippet": self.snippet,
            "score": self.confidence,
            "retrieval_layer": "report_carbon_activity_extraction",
        }


@dataclass(frozen=True)
class FactorMatchCandidate:
    record: FactorRecord
    score: int
    matched_terms: tuple[str, ...]


@dataclass
class ReportCarbonExtractionResult:
    extracted_activities: list[ExtractedReportActivity] = field(default_factory=list)
    calculation: CalcCarbonResponse | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.calculation:
            return "calculated"
        if self.extracted_activities:
            return "extracted_not_calculated"
        return "no_supported_activity_found"

    def to_output(self) -> dict:
        return {
            "status": self.status,
            "extracted_activity_count": len(self.extracted_activities),
            "extracted_activities": [item.to_output() for item in self.extracted_activities],
            "calculation": self.calculation.model_dump(mode="json") if self.calculation else None,
            "calculation_table": _build_calculation_table(self.calculation, self.extracted_activities),
            "warnings": self.warnings,
        }


REPORT_ACTIVITY_PATTERNS: tuple[ActivityPattern, ...] = (
    ActivityPattern(
        scope="scope2",
        activity_category="purchased_electricity",
        activity_name="electricity",
        canonical_unit="kWh",
        aliases=(
            "外购电力",
            "购入电力",
            "购买电力",
            "购电量",
            "购电",
            "用电量",
            "用电",
            "耗电量",
            "耗电",
            "电耗",
            "电力消耗",
            "电力",
            "电量",
            "electricity",
            "power consumption",
        ),
        factor_preference="official_latest",
        region="CN",
    ),
    ActivityPattern(
        scope="scope1",
        activity_category="stationary_combustion",
        activity_name="natural_gas",
        canonical_unit="m3",
        aliases=("天然气", "燃气", "natural gas"),
        factor_preference="guidance_default",
    ),
    ActivityPattern(
        scope="scope1",
        activity_category="stationary_combustion",
        activity_name="diesel",
        canonical_unit="L",
        aliases=("柴油", "diesel"),
        factor_preference="guidance_default",
    ),
    ActivityPattern(
        scope="scope1",
        activity_category="stationary_combustion",
        activity_name="gasoline",
        canonical_unit="L",
        aliases=("汽油", "gasoline", "petrol"),
        factor_preference="guidance_default",
    ),
    ActivityPattern(
        scope="scope1",
        activity_category="stationary_combustion",
        activity_name="lpg",
        canonical_unit="kg",
        aliases=("液化石油气", "lpg", "LPG"),
        factor_preference="guidance_default",
    ),
    ActivityPattern(
        scope="scope1",
        activity_category="stationary_combustion",
        activity_name="coal",
        canonical_unit="t",
        aliases=("煤炭", "原煤", "烟煤", "无烟煤", "煤", "coal"),
        factor_preference="guidance_default",
    ),
)

_DOMAIN_ALIASES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (
        ("外购电力", "购入电力", "购买电力", "购电", "用电", "用电量", "耗电", "电耗", "电力消耗", "电力"),
        ("electricity", "purchased_electricity", "电力", "外购电力", "购电"),
    ),
    (("货车", "货运", "物流运输", "公路运输"), ("载货汽车", "货车")),
    (("客车", "乘用车", "小汽车", "轿车", "公务车", "车辆行驶"), ("载客汽车", "客车", "乘用车", "家庭车")),
    (("公交", "公共汽车", "班车"), ("公交", "公共交通")),
    (("飞机", "航班", "航空", "空运"), ("飞机", "航空", "飞机排放")),
    (("船舶", "货船", "海运", "水运"), ("货船", "船舶")),
    (("纸箱", "包装箱", "瓦楞纸箱"), ("纸箱", "瓦楞")),
    (("办公用纸", "复印纸", "纸张"), ("纸制品", "纸张")),
    (("用水", "自来水", "供水"), ("水", "自来水")),
    (("废弃物", "垃圾", "固废", "焚烧", "填埋"), ("废弃物", "废弃物处理")),
)


class ReportCarbonActivityExtractor:
    """Extract carbon activity quantities from parsed upload chunks.

    This consumes the repository's parsed chunk representation. Text, tables,
    and OCR output are expected to be normalized by the existing document
    parser before this extractor runs.
    """

    def __init__(
        self,
        *,
        factor_loader: CarbonFactorLoader | None = None,
        dynamic_match_threshold: int = 85,
    ) -> None:
        self.factor_loader = factor_loader or get_factor_loader()
        self.dynamic_match_threshold = dynamic_match_threshold

    def extract(self, chunks: Iterable[KnowledgeChunk]) -> ReportCarbonExtractionResult:
        extracted: list[ExtractedReportActivity] = []
        warnings: list[str] = []
        seen: set[tuple[str, str, float, str, str]] = set()
        seen_quantities: set[tuple[str, float, str]] = set()
        factor_records = self._load_factor_records(warnings)

        for chunk in chunks:
            for segment in _iter_segments(chunk.snippet):
                for pattern in REPORT_ACTIVITY_PATTERNS:
                    alias = _matched_alias(segment, pattern.aliases)
                    if not alias:
                        continue
                    for value, unit in _find_quantities(segment, expected_unit=pattern.canonical_unit):
                        key = (chunk.chunk_id, pattern.activity_name, value, unit, alias.lower())
                        if key in seen:
                            continue
                        local_candidate = None
                        if factor_records:
                            candidates = _rank_factor_candidates(segment=segment, unit=unit, records=factor_records)
                            if candidates and candidates[0].score >= self.dynamic_match_threshold:
                                local_candidate = candidates[0]
                        seen.add(key)
                        seen_quantities.add((chunk.chunk_id, round(value, 6), _canonical_unit(unit)))
                        extracted.append(
                            _build_activity(
                                chunk=chunk,
                                pattern=pattern,
                                value=value,
                                unit=unit,
                                alias=alias,
                                segment=segment,
                                local_factor=local_candidate.record if local_candidate else None,
                                local_candidate=local_candidate,
                            )
                        )
                if factor_records:
                    extracted.extend(
                        self._extract_local_factor_matches(
                            chunk=chunk,
                            segment=segment,
                            factor_records=factor_records,
                            seen_quantities=seen_quantities,
                        )
                    )

        if not extracted:
            warnings.append(
                "未在已选上传报告片段中识别到可核算活动量。请确认报告里包含活动名称、数量和单位；系统会优先按本地碳因子库尝试匹配。"
            )
        return ReportCarbonExtractionResult(extracted_activities=extracted, warnings=warnings)

    def _load_factor_records(self, warnings: list[str]) -> list[FactorRecord]:
        try:
            return [
                record
                for record in self.factor_loader.load_registry().records
                if record.factor_value > 0 and record.activity_unit
            ]
        except Exception as exc:
            warnings.append(f"本地碳因子库暂不可用，仅使用内置基础抽取规则：{exc}")
            return []

    def _extract_local_factor_matches(
        self,
        *,
        chunk: KnowledgeChunk,
        segment: str,
        factor_records: list[FactorRecord],
        seen_quantities: set[tuple[str, float, str]],
    ) -> list[ExtractedReportActivity]:
        matched: list[ExtractedReportActivity] = []
        for value, unit in _find_any_quantities(segment):
            quantity_key = (chunk.chunk_id, round(value, 6), _canonical_unit(unit))
            if quantity_key in seen_quantities:
                continue
            candidates = _rank_factor_candidates(segment=segment, unit=unit, records=factor_records)
            if not candidates or candidates[0].score < self.dynamic_match_threshold:
                continue
            selected = candidates[0]
            seen_quantities.add(quantity_key)
            matched.append(
                _build_factor_activity(
                    chunk=chunk,
                    factor=selected.record,
                    value=value,
                    unit=unit,
                    segment=segment,
                    candidate=selected,
                )
            )
        return matched


class ReportCarbonCalculationService:
    def __init__(
        self,
        *,
        extractor: ReportCarbonActivityExtractor | None = None,
        carbon_service: CarbonService | None = None,
    ) -> None:
        self.extractor = extractor or ReportCarbonActivityExtractor()
        self.carbon_service = carbon_service or get_carbon_service()

    def extract_and_calculate(
        self,
        *,
        owner_user_id: str,
        session_id: str | None,
        chunks: Iterable[KnowledgeChunk],
    ) -> ReportCarbonExtractionResult:
        result = self.extractor.extract(chunks)
        if not result.extracted_activities:
            return result

        try:
            calculation = self.carbon_service.calculate(
                owner_user_id=owner_user_id,
                payload=CalcCarbonRequest(
                    session_id=session_id,
                    period_label="report-extracted",
                    inventory_standard="report_upload_extraction_v1",
                    activity_items=[item.activity for item in result.extracted_activities],
                ),
            )
            result.calculation = calculation
        except Exception as exc:  # pragma: no cover - exact engine failures depend on runtime factor DB
            result.warnings.append(f"已抽取活动数据，但碳核算失败：{exc}")
        return result


def _build_calculation_table(
    calculation: CalcCarbonResponse | None,
    extracted_activities: Iterable[ExtractedReportActivity] = (),
) -> list[dict]:
    if calculation is None:
        return []

    citations_by_factor = {item.factor_id: item for item in calculation.citations}
    snapshots_by_factor = {item.factor_id: item for item in calculation.factor_snapshot}
    extracted = list(extracted_activities)
    rows: list[dict] = []
    for item in calculation.breakdown:
        snapshot = snapshots_by_factor.get(item.factor_id)
        citation = citations_by_factor.get(item.factor_id)
        source_name = (
            snapshot.source_name
            if snapshot is not None
            else citation.source if citation is not None else "未知来源"
        )
        source_url = (
            snapshot.source_url
            if snapshot is not None
            else citation.source_url if citation is not None else None
        )
        factor_year = snapshot.effective_year or snapshot.year if snapshot is not None else None
        rows.append(
            {
                "emission_source": _resolve_emission_source_label(item, extracted),
                "scope": item.scope,
                "activity_category": item.activity_category,
                "activity_name": item.activity_name,
                "activity_value": item.activity_value,
                "activity_unit": item.activity_unit,
                "normalized_activity_value": item.normalized_activity_value,
                "normalized_activity_unit": item.normalized_activity_unit,
                "factor_value": item.factor_value,
                "factor_unit": item.factor_unit,
                "factor_id": item.factor_id,
                "factor_source": source_name,
                "factor_source_url": source_url,
                "factor_year": factor_year,
                "emission_kgco2e": item.emission_kgco2e,
            }
        )
    return rows


def _resolve_emission_source_label(item, extracted_activities: list[ExtractedReportActivity]) -> str:
    for extracted in extracted_activities:
        activity = extracted.activity
        if (
            activity.activity_name == item.activity_name
            and activity.activity_unit == item.activity_unit
            and abs(float(activity.activity_value) - float(item.activity_value)) < 0.000001
        ):
            return _activity_display_name(extracted.matched_alias or activity.activity_name)
    return _activity_display_name(item.activity_name or item.item)


def _activity_display_name(value: str | None) -> str:
    if not value:
        return "未知排放源"
    normalized = str(value).strip()
    if normalized in {
        "electricity",
        "purchased_electricity",
        "外购电力",
        "购入电力",
        "购买电力",
        "购电",
        "购电量",
        "用电",
        "用电量",
        "耗电",
        "耗电量",
        "电耗",
        "电力",
        "电量",
    } or any(term in normalized for term in ("外购电力", "购电", "用电", "耗电", "电力消耗")):
        return "外购电力"
    labels = {
        "natural_gas": "天然气",
        "diesel": "柴油",
        "gasoline": "汽油",
        "lpg": "液化石油气",
        "coal": "煤炭",
    }
    return labels.get(normalized, normalized)


def _iter_segments(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    raw_segments: list[str] = []
    for line in normalized.split("\n"):
        raw_segments.extend(re.split(r"[。；;]", line))
    return [segment.strip() for segment in raw_segments if segment.strip()]


def _matched_alias(segment: str, aliases: tuple[str, ...]) -> str | None:
    lowered = segment.lower()
    for alias in aliases:
        if alias.lower() in lowered:
            return alias
    return None


def _find_quantities(segment: str, *, expected_unit: str) -> list[tuple[float, str]]:
    quantities: list[tuple[float, str]] = []
    for regex in (_TABLE_VALUE_UNIT_RE, _TABLE_UNIT_VALUE_RE):
        for match in regex.finditer(segment):
            unit = _canonical_unit(match.group("unit"))
            if not _is_compatible_unit(unit, expected_unit):
                continue
            value = _parse_number(match.group("value"))
            if value <= 0:
                continue
            quantities.append((value, unit))
    for regex in (_VALUE_THEN_UNIT_RE, _UNIT_THEN_VALUE_RE):
        for match in regex.finditer(segment):
            if _looks_like_emission_factor_unit(segment, match):
                continue
            unit = _canonical_unit(match.group("unit"))
            if not _is_compatible_unit(unit, expected_unit):
                continue
            value = _parse_number(match.group("value"))
            if value <= 0:
                continue
            quantities.append((value, unit))
    return list(dict.fromkeys(quantities))


def _find_any_quantities(segment: str) -> list[tuple[float, str]]:
    quantities: list[tuple[float, str]] = []
    for regex in (_TABLE_VALUE_UNIT_RE, _TABLE_UNIT_VALUE_RE):
        for match in regex.finditer(segment):
            value = _parse_number(match.group("value"))
            if value <= 0:
                continue
            quantities.append((value, _canonical_unit(match.group("unit"))))
    for regex in (_VALUE_THEN_UNIT_RE, _UNIT_THEN_VALUE_RE):
        for match in regex.finditer(segment):
            if _looks_like_emission_factor_unit(segment, match):
                continue
            value = _parse_number(match.group("value"))
            if value <= 0:
                continue
            quantities.append((value, _canonical_unit(match.group("unit"))))
    return list(dict.fromkeys(quantities))


def _looks_like_emission_factor_unit(segment: str, match: re.Match) -> bool:
    unit_end = match.end("unit")
    tail = segment[unit_end : unit_end + 8].lower()
    return tail.startswith(("co2", "co₂", "co₂e", "co2e", "二氧化碳"))


def _parse_number(value: str) -> float:
    return float(value.replace(",", ""))


def _canonical_unit(unit: str) -> str:
    normalized = unit.strip()
    lowered = normalized.lower()
    aliases = {
        "kwh": "kWh",
        "kw·h": "kWh",
        "千瓦时": "kWh",
        "度": "kWh",
        "mwh": "MWh",
        "m3": "m3",
        "m³": "m3",
        "立方米": "m3",
        "方": "m3",
        "km": "km",
        "公里": "km",
        "千米": "km",
        "人公里": "人公里",
        "人·公里": "人公里",
        "人-公里": "人公里",
        "人千米": "人公里",
        "pkm": "人公里",
        "吨公里": "吨公里",
        "吨·公里": "吨公里",
        "吨-公里": "吨公里",
        "tkm": "吨公里",
        "m2": "m2",
        "m²": "m2",
        "㎡": "m2",
        "平方米": "m2",
        "l": "L",
        "升": "L",
        "kg": "kg",
        "千克": "kg",
        "公斤": "kg",
        "t": "t",
        "吨": "t",
    }
    return aliases.get(lowered, aliases.get(normalized, normalized))


def _is_compatible_unit(unit: str, expected_unit: str) -> bool:
    if unit == expected_unit:
        return True
    compatible = {
        "kWh": {"MWh"},
        "kg": {"t"},
        "t": {"kg"},
    }
    return unit in compatible.get(expected_unit, set())


def _rank_factor_candidates(*, segment: str, unit: str, records: list[FactorRecord]) -> list[FactorMatchCandidate]:
    canonical_unit = _canonical_unit(unit)
    candidates: list[FactorMatchCandidate] = []
    for record in records:
        factor_unit = _canonical_unit(record.activity_unit)
        if not _is_compatible_unit(canonical_unit, factor_unit):
            continue
        matched_terms = _matched_factor_terms(segment, record)
        if not matched_terms:
            continue
        score = 0
        if record.activity_name in matched_terms:
            score += 80
        if any(_is_domain_alias_term(term) for term in matched_terms):
            score += 55
        score += min(len(matched_terms), 5) * 12
        score += 25 if canonical_unit == factor_unit else 12
        if record.source_type in {"official", "public_dataset"} or record.is_official:
            score += 12
        if record.source_priority:
            score += min(record.source_priority, 100) // 5
        if _is_generic_activity_name(record.activity_name):
            score -= 30
        candidates.append(FactorMatchCandidate(record=record, score=score, matched_terms=tuple(matched_terms)))
    return sorted(
        candidates,
        key=lambda item: (
            item.score,
            item.record.source_priority,
            item.record.effective_year or item.record.year or 0,
            len(item.record.activity_name),
        ),
        reverse=True,
    )


def _matched_factor_terms(segment: str, record: FactorRecord) -> list[str]:
    lowered = segment.lower()
    terms = _factor_terms(record)
    matched = []
    for term in terms:
        if term.lower() in lowered:
            matched.append(term)
    matched.extend(_domain_alias_terms(lowered, record))
    return list(dict.fromkeys(matched))


def _domain_alias_terms(lowered_segment: str, record: FactorRecord) -> list[str]:
    record_text = " ".join(
        str(item or "")
        for item in (
            record.activity_name,
            record.activity_category,
            record.applicable_industry,
            record.region_name,
            record.region,
            record.notes,
            *record.tags,
        )
    ).lower()
    matched: list[str] = []
    for triggers, targets in _DOMAIN_ALIASES:
        trigger = next((item for item in triggers if item.lower() in lowered_segment), None)
        if trigger is None:
            continue
        if any(target.lower() in record_text for target in targets):
            matched.append(trigger)
    return matched


def _is_domain_alias_term(term: str) -> bool:
    lowered = term.lower()
    return any(lowered == trigger.lower() for triggers, _ in _DOMAIN_ALIASES for trigger in triggers)


def _factor_terms(record: FactorRecord) -> list[str]:
    terms: list[str] = []
    for value in (
        record.activity_name,
        record.activity_category,
        record.applicable_industry,
        record.region_name,
        record.region,
        record.notes,
    ):
        terms.extend(_split_terms(value))
    for tag in record.tags:
        terms.extend(_split_terms(tag))
    return [term for term in dict.fromkeys(terms) if len(term) >= 2 and not _is_noise_term(term)]


def _split_terms(value: str | None) -> list[str]:
    if not value:
        return []
    raw = re.split(r"[\s,，;；/|:：()（）\[\]【】\-]+", value)
    return [item.strip() for item in raw if item.strip()]


def _is_noise_term(term: str) -> bool:
    lowered = term.lower()
    if lowered.isdigit():
        return True
    return lowered in {
        "cn",
        "scope1",
        "scope2",
        "scope3",
        "kg",
        "kwh",
        "m3",
        "km",
        "unit",
        "public",
        "dataset",
        "carbonstop",
        "ccdb",
        "公开因子",
        "中国",
        "其他",
        "通用",
    }


def _is_generic_activity_name(name: str) -> bool:
    return name.strip() in {"其他", "通用", "其他服务", "其他产品"}


def _build_activity(
    *,
    chunk: KnowledgeChunk,
    pattern: ActivityPattern,
    value: float,
    unit: str,
    alias: str,
    segment: str,
    local_factor: FactorRecord | None = None,
    local_candidate: FactorMatchCandidate | None = None,
) -> ExtractedReportActivity:
    metadata = chunk.metadata or {}
    locator = _format_locator(metadata)
    evidence_reference = f"{chunk.title}"
    if locator:
        evidence_reference += f" · {locator}"
    evidence_reference += f" · {alias}"
    activity = CarbonActivityItem(
        scope=pattern.scope,  # type: ignore[arg-type]
        activity_category=pattern.activity_category,
        activity_name=pattern.activity_name,
        activity_value=value,
        activity_unit=unit,
        region=pattern.region,
        factor_preference=pattern.factor_preference,
        scope2_method=pattern.scope2_method,
        data_quality="estimate",
        evidence_reference=evidence_reference,
        source_document_id=chunk.chunk_id,
        entry_method="file_upload",
        requested_factor_id=local_factor.factor_id if local_factor else None,
        metadata={
            "file_id": str(metadata.get("file_id") or ""),
            "chunk_id": chunk.chunk_id,
            "matched_alias": alias,
            "evidence_snippet": segment[:500],
            **(
                {
                    "matched_factor_id": local_factor.factor_id,
                    "matched_factor_source": local_factor.source_name,
                    "matched_factor_unit": local_factor.factor_unit,
                    "matched_factor_score": str(local_candidate.score if local_candidate else ""),
                    "matched_terms": "、".join((local_candidate.matched_terms if local_candidate else ())[:8]),
                    "match_method": "local_carbon_factor_database",
                }
                if local_factor
                else {}
            ),
        },
    )
    return ExtractedReportActivity(
        activity=activity,
        title=chunk.title,
        chunk_id=chunk.chunk_id,
        knowledge_item_id=chunk.knowledge_item_id,
        file_id=_optional_str(metadata.get("file_id")),
        page_number=_optional_int(metadata.get("page_number")),
        sheet_name=_optional_str(metadata.get("sheet_name")),
        slide_number=_optional_int(metadata.get("slide_number")),
        section_title=_optional_str(metadata.get("section_title")),
        snippet=segment[:500],
        confidence=0.82,
        matched_alias=alias,
    )


def _build_factor_activity(
    *,
    chunk: KnowledgeChunk,
    factor: FactorRecord,
    value: float,
    unit: str,
    segment: str,
    candidate: FactorMatchCandidate,
) -> ExtractedReportActivity:
    metadata = chunk.metadata or {}
    locator = _format_locator(metadata)
    evidence_reference = f"{chunk.title}"
    if locator:
        evidence_reference += f" · {locator}"
    evidence_reference += f" · 本地因子库匹配：{factor.activity_name}"
    confidence = min(0.95, max(0.55, candidate.score / 140))
    activity = CarbonActivityItem(
        scope=factor.scope,  # type: ignore[arg-type]
        activity_category=factor.activity_category,
        activity_name=factor.activity_name,
        activity_value=value,
        activity_unit=unit,
        region=factor.region_code or factor.region,
        year=factor.effective_year or factor.year,
        factor_preference="local_factor_database",
        data_quality="estimate",
        evidence_reference=evidence_reference,
        source_document_id=chunk.chunk_id,
        entry_method="file_upload",
        requested_factor_id=factor.factor_id,
        metadata={
            "file_id": str(metadata.get("file_id") or ""),
            "chunk_id": chunk.chunk_id,
            "matched_alias": factor.activity_name,
            "matched_factor_id": factor.factor_id,
            "matched_factor_source": factor.source_name,
            "matched_factor_unit": factor.factor_unit,
            "matched_factor_score": str(candidate.score),
            "matched_terms": "、".join(candidate.matched_terms[:8]),
            "evidence_snippet": segment[:500],
            "match_method": "local_carbon_factor_database",
        },
    )
    return ExtractedReportActivity(
        activity=activity,
        title=chunk.title,
        chunk_id=chunk.chunk_id,
        knowledge_item_id=chunk.knowledge_item_id,
        file_id=_optional_str(metadata.get("file_id")),
        page_number=_optional_int(metadata.get("page_number")),
        sheet_name=_optional_str(metadata.get("sheet_name")),
        slide_number=_optional_int(metadata.get("slide_number")),
        section_title=_optional_str(metadata.get("section_title")),
        snippet=segment[:500],
        confidence=round(confidence, 2),
        matched_alias=factor.activity_name,
    )


def _format_locator(metadata: dict) -> str | None:
    parts: list[str] = []
    page = _optional_int(metadata.get("page_number"))
    slide = _optional_int(metadata.get("slide_number"))
    sheet = _optional_str(metadata.get("sheet_name"))
    section = _optional_str(metadata.get("section_title"))
    if page:
        parts.append(f"p.{page}")
    if sheet:
        parts.append(f"sheet {sheet}")
    if slide:
        parts.append(f"slide {slide}")
    if section:
        parts.append(section)
    return " / ".join(parts) or None


def _optional_str(value) -> str | None:
    if value in (None, ""):
        return None
    normalized = str(value).strip()
    return normalized or None


def _optional_int(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
