from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from app.carbon.factors.schema import FactorRecord

CARBONSTOP_CCDB_URL = "https://www.carbonstop.com/ccdb"
CARBONSTOP_GATEWAY_URL = "https://gateway.carbonstop.com/management/system/website/queryFactorListWebsite_classify"
CARBONSTOP_AES_KEY = b"carbon@stp2060ja"
CARBONSTOP_SEED_PATH = Path(__file__).resolve().parents[3] / "data" / "factors" / "carbonstop_ccdb_public_seed.json"
CARBONSTOP_MAPPING_VERSION = "carbonstop-public-catalog-v3"


@dataclass(frozen=True)
class CarbonStopFactorRow:
    source: dict[str, Any]
    record: FactorRecord
    raw: dict[str, Any]


@dataclass(frozen=True)
class CarbonStopCatalogRow:
    entry_id: str
    name: str
    category: str
    industry: str | None
    region: str | None
    year: int | None
    factor_unit: str | None
    activity_unit: str | None
    raw_value: str | None
    factor_value: float | None
    value_status: str
    is_calculation_ready: bool
    source_title: str
    publisher: str
    source_url: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class CarbonStopImportPayload:
    rows: list[CarbonStopFactorRow]
    catalog_rows: list[CarbonStopCatalogRow]
    skipped_rows: list[dict[str, Any]]
    categories: list[dict[str, Any]]
    origin: str = CARBONSTOP_CCDB_URL


def md5_sign(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def decrypt_response_data(response_data: str) -> str:
    decryptor = Cipher(algorithms.AES(CARBONSTOP_AES_KEY), modes.ECB()).decryptor()
    padded = decryptor.update(_b64decode(response_data)) + decryptor.finalize()
    unpadder = PKCS7(128).unpadder()
    data = unpadder.update(padded) + unpadder.finalize()
    return data.decode("utf-8")


def _b64decode(value: str) -> bytes:
    import base64

    return base64.b64decode(value.encode("utf-8"))


class CarbonStopPublicAdapter:
    """Adapter for CarbonStop CCDB public page/gateway data.

    The adapter only reads fields exposed by the public website runtime. Rows whose
    values are marked as encrypted/commercial are kept in the import summary but
    not converted into calculation-ready factor records.
    """

    def __init__(self, *, seed_path: Path | None = None, timeout_seconds: float = 20.0) -> None:
        self.seed_path = seed_path or CARBONSTOP_SEED_PATH
        self.timeout_seconds = timeout_seconds

    def load_seed_payload(self) -> CarbonStopImportPayload:
        payload = json.loads(self.seed_path.read_text(encoding="utf-8"))
        return self.normalize_snapshot(payload)

    def fetch_public_payload(self) -> CarbonStopImportPayload:
        with httpx.Client(timeout=self.timeout_seconds, headers={"User-Agent": "CarbonRag-v1.4.8-public-ccdb-sync"}) as client:
            html = client.get(CARBONSTOP_CCDB_URL).text
            industry = self._extract_industry_payload(html)
            rows: list[dict[str, Any]] = []
            categories: list[dict[str, Any]] = []
            for group in industry.get("ins") or []:
                for item in group.get("enumList") or []:
                    body = {
                        "lang": "zh",
                        "classify": item.get("dictValue"),
                        "industry": group.get("dictValue"),
                        "sign": md5_sign(f"website_ccdb{item.get('dictValue')}{group.get('dictValue')}"),
                    }
                    response = client.post(CARBONSTOP_GATEWAY_URL, json=body).json()
                    decoded = json.loads(decrypt_response_data(response["responseData"]))
                    category_count = len(decoded.get("rows") or [])
                    categories.append(
                        {
                            "groupLabel": group.get("dictLabel"),
                            "groupValue": group.get("dictValue"),
                            "classifyLabel": item.get("dictLabel"),
                            "classifyValue": item.get("dictValue"),
                            "count": category_count,
                        }
                    )
                    for row in decoded.get("rows") or []:
                        rows.append(
                            {
                                **row,
                                "ccdbGroupLabel": group.get("dictLabel"),
                                "ccdbGroupValue": group.get("dictValue"),
                                "ccdbClassifyLabel": item.get("dictLabel"),
                                "ccdbClassifyValue": item.get("dictValue"),
                            }
                        )
        return self.normalize_snapshot(
            {
                "origin": CARBONSTOP_CCDB_URL,
                "keys": industry.get("keys") or [],
                "categories": categories,
                "rows": rows,
            }
        )

    def normalize_snapshot(self, payload: dict[str, Any]) -> CarbonStopImportPayload:
        records: list[CarbonStopFactorRow] = []
        catalog_rows: list[CarbonStopCatalogRow] = []
        skipped: list[dict[str, Any]] = []
        for row in payload.get("rows") or []:
            catalog_rows.append(self._row_to_catalog(row))
            normalized = self._row_to_factor(row)
            if normalized is None:
                skipped.append(
                    {
                        "id": row.get("id"),
                        "name": row.get("name"),
                        "industry": row.get("ccdbGroupLabel"),
                        "category": row.get("ccdbClassifyLabel") or row.get("business"),
                        "reason": "公开页面未展示可计算数值",
                        "raw_value": row.get("cValue"),
                        "institution": row.get("institution"),
                        "source": row.get("source"),
                    }
                )
                continue
            records.append(normalized)
        return CarbonStopImportPayload(
            rows=records,
            catalog_rows=catalog_rows,
            skipped_rows=skipped,
            categories=payload.get("categories") or [],
            origin=payload.get("origin") or CARBONSTOP_CCDB_URL,
        )

    def _row_to_catalog(self, row: dict[str, Any]) -> CarbonStopCatalogRow:
        row_id = _normalize_text(row.get("id")) or _stable_row_id(row)
        raw_value = _normalize_text(row.get("cValue"))
        factor_value = _parse_factor_value(raw_value)
        unit = _normalize_text(row.get("unit"))
        _, activity_unit = _split_unit(unit or "kgCO2e/unit")
        source_title = _normalize_text(row.get("source")) or "CarbonStop CCDB 公开因子"
        publisher = _normalize_text(row.get("institution")) or "CarbonStop CCDB"
        category = _normalize_text(row.get("ccdbClassifyLabel") or row.get("business")) or "未分类"
        industry = _normalize_text(row.get("ccdbGroupLabel"))
        year = _parse_int(row.get("year") or row.get("applyYear"))
        value_status = "calculation_ready" if factor_value is not None else "encrypted"
        metadata = {
            "source_platform": "CarbonStop CCDB 中国碳数据库",
            "source_platform_url": CARBONSTOP_CCDB_URL,
            "ccdb_row_id": row.get("id"),
            "ccdb_source_id": row.get("sourceId"),
            "ccdb_group_label": industry,
            "ccdb_group_value": row.get("ccdbGroupValue"),
            "ccdb_classify_label": category,
            "ccdb_classify_value": row.get("ccdbClassifyValue") or row.get("factorClassify"),
            "source_level": row.get("sourceLevel"),
            "document_type": row.get("documentType"),
            "original_source": source_title,
            "institution": publisher,
            "specification": row.get("specification"),
            "description": row.get("description"),
            "business": row.get("business"),
            "apply_year": row.get("applyYear"),
            "apply_year_end": row.get("applyYearEnd"),
            "raw_row": row,
        }
        return CarbonStopCatalogRow(
            entry_id=f"carbonstop-ccdb-{row_id}",
            name=_normalize_text(row.get("name")) or _normalize_text(row.get("nameEn")) or row_id,
            category=category,
            industry=industry,
            region=_normalize_text(row.get("countries") or row.get("area")),
            year=year,
            factor_unit=unit,
            activity_unit=activity_unit,
            raw_value=raw_value,
            factor_value=factor_value,
            value_status=value_status,
            is_calculation_ready=factor_value is not None,
            source_title=source_title,
            publisher=publisher,
            source_url=CARBONSTOP_CCDB_URL,
            metadata=metadata,
        )

    def _row_to_factor(self, row: dict[str, Any]) -> CarbonStopFactorRow | None:
        value = _parse_factor_value(row.get("cValue"))
        if value is None:
            return None
        unit = _normalize_text(row.get("unit")) or "kgCO2e/unit"
        result_unit, activity_unit = _split_unit(unit)
        row_id = _normalize_text(row.get("id")) or _stable_row_id(row)
        year = _parse_int(row.get("year") or row.get("applyYear"))
        source_title = _normalize_text(row.get("source")) or "CarbonStop CCDB 公开因子"
        institution = _normalize_text(row.get("institution")) or "CarbonStop CCDB"
        category = _normalize_text(row.get("ccdbClassifyLabel") or row.get("business")) or "未分类"
        group_label = _normalize_text(row.get("ccdbGroupLabel"))
        name = _normalize_text(row.get("name")) or _normalize_text(row.get("nameEn")) or row_id
        metadata = {
            "source_platform": "CarbonStop CCDB 中国碳数据库",
            "source_platform_url": CARBONSTOP_CCDB_URL,
            "ccdb_row_id": row.get("id"),
            "ccdb_source_id": row.get("sourceId"),
            "ccdb_group_label": group_label,
            "ccdb_group_value": row.get("ccdbGroupValue"),
            "ccdb_classify_label": category,
            "ccdb_classify_value": row.get("ccdbClassifyValue") or row.get("factorClassify"),
            "source_level": row.get("sourceLevel"),
            "document_type": row.get("documentType"),
            "original_source": source_title,
            "institution": institution,
            "specification": row.get("specification"),
            "description": row.get("description"),
            "business": row.get("business"),
            "apply_year": row.get("applyYear"),
            "apply_year_end": row.get("applyYearEnd"),
            "raw_row": row,
        }
        tags = [
            "CarbonStop CCDB",
            "公开因子",
            *(item for item in [category, group_label, row.get("business"), row.get("countries"), row.get("specification")] if item),
        ]
        record = FactorRecord(
            factor_id=f"carbonstop-ccdb-{row_id}",
            factor_version=f"carbonstop-public-{year or 'unknown'}",
            source_type="public_dataset",
            source_name=f"CarbonStop CCDB / {institution} / {source_title}",
            source_url=CARBONSTOP_CCDB_URL,
            scope="scope3",
            activity_category=category,
            activity_name=name,
            region=_normalize_text(row.get("countries") or row.get("area")),
            region_level=_normalize_text(row.get("sourceLevel")),
            region_code=None,
            region_name=_normalize_text(row.get("countries") or row.get("area")),
            year=year,
            effective_year=_parse_int(row.get("applyYear")),
            method_type=_normalize_text(row.get("factorPattern")),
            source_priority=80,
            applicable_industry=group_label or _normalize_text(row.get("business")),
            applicable_standard=source_title,
            quality_level="public_ccdb",
            is_official=False,
            factor_value=value,
            factor_unit=unit,
            activity_unit=activity_unit,
            result_unit=result_unit,
            valid_from=str(row.get("applyYear")) if row.get("applyYear") else None,
            valid_to=None if row.get("applyYearEnd") in (None, "", "不限") else str(row.get("applyYearEnd")),
            is_default=False,
            is_deprecated=False,
            notes=f"来源于 CarbonStop CCDB 公开页面，原始机构：{institution}；原始来源：{source_title}。",
            tags=list(dict.fromkeys(tags)),
        )
        source = {
            "title": source_title,
            "publisher": institution,
            "source_url": CARBONSTOP_CCDB_URL,
            "license": "CarbonStop CCDB public web listing; cite original institution/source.",
            "published_year": year,
            "source_type": "public_dataset",
        }
        # Store metadata through FactorRecord notes/tags and source fields; the store
        # enriches metadata from this raw snapshot when importing CarbonStop rows.
        return CarbonStopFactorRow(source=source, record=record, raw=metadata)

    @staticmethod
    def _extract_industry_payload(html: str) -> dict[str, Any]:
        marker = '\\"industry\\":'
        start = html.find(marker)
        if start < 0:
            raise ValueError("CarbonStop CCDB industry payload not found.")
        object_start = start + len(marker)
        depth = 0
        end = -1
        for index, char in enumerate(html[object_start:], object_start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end < 0:
            raise ValueError("CarbonStop CCDB industry payload is incomplete.")
        return json.loads(html[object_start:end].replace('\\"', '"'))


def _parse_factor_value(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text):
        return None
    return float(text)


def _parse_int(value: Any) -> int | None:
    if value is None:
        return None
    match = re.search(r"\d{4}", str(value))
    if not match:
        return None
    return int(match.group(0))


def _split_unit(unit: str) -> tuple[str, str]:
    normalized = unit.replace("₂", "2")
    if "/" not in normalized:
        return normalized, "unit"
    result_unit, activity_unit = normalized.split("/", 1)
    return result_unit.strip() or "kgCO2e", activity_unit.strip() or "unit"


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _stable_row_id(row: dict[str, Any]) -> str:
    raw = "|".join(str(row.get(key) or "") for key in ("name", "source", "unit", "cValue", "year"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
