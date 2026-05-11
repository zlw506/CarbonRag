from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from app.carbon.schemas import CalcCarbonRequest, CalcCarbonResponse, CarbonActivityItem
from app.carbon.service import CarbonService, get_carbon_service
from app.knowledge.schemas import KnowledgeChunk


_NUMBER = r"(?P<value>\d+(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)"
_UNIT = r"(?P<unit>kWh|kw·h|千瓦时|度|MWh|m3|m³|立方米|方|L|l|升|kg|千克|公斤|t|吨)"
_VALUE_THEN_UNIT_RE = re.compile(_NUMBER + r"\s*" + _UNIT, re.IGNORECASE)
_UNIT_THEN_VALUE_RE = re.compile(_UNIT + r"[\s:：）\)]{0,8}" + _NUMBER, re.IGNORECASE)


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
            "warnings": self.warnings,
        }


REPORT_ACTIVITY_PATTERNS: tuple[ActivityPattern, ...] = (
    ActivityPattern(
        scope="scope2",
        activity_category="purchased_electricity",
        activity_name="electricity",
        canonical_unit="kWh",
        aliases=("用电量", "外购电力", "购电量", "电量", "耗电量", "electricity", "power consumption"),
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


class ReportCarbonActivityExtractor:
    """Extract carbon activity quantities from parsed upload chunks.

    This consumes the repository's parsed chunk representation. Text, tables,
    and OCR output are expected to be normalized by the existing document
    parser before this extractor runs.
    """

    def extract(self, chunks: Iterable[KnowledgeChunk]) -> ReportCarbonExtractionResult:
        extracted: list[ExtractedReportActivity] = []
        warnings: list[str] = []
        seen: set[tuple[str, str, float, str, str]] = set()

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
                        seen.add(key)
                        extracted.append(_build_activity(chunk=chunk, pattern=pattern, value=value, unit=unit, alias=alias, segment=segment))

        if not extracted:
            warnings.append(
                "未在已选上传报告片段中识别到受支持的活动数据。当前只支持用电、天然气、柴油、汽油、LPG、煤等常见活动量。"
            )
        return ReportCarbonExtractionResult(extracted_activities=extracted, warnings=warnings)


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
    for regex in (_VALUE_THEN_UNIT_RE, _UNIT_THEN_VALUE_RE):
        for match in regex.finditer(segment):
            unit = _canonical_unit(match.group("unit"))
            if not _is_compatible_unit(unit, expected_unit):
                continue
            value = _parse_number(match.group("value"))
            if value <= 0:
                continue
            quantities.append((value, unit))
    return list(dict.fromkeys(quantities))


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


def _build_activity(
    *,
    chunk: KnowledgeChunk,
    pattern: ActivityPattern,
    value: float,
    unit: str,
    alias: str,
    segment: str,
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
        metadata={
            "file_id": str(metadata.get("file_id") or ""),
            "chunk_id": chunk.chunk_id,
            "matched_alias": alias,
            "evidence_snippet": segment[:500],
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
