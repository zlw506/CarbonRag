import json
from functools import lru_cache
from pathlib import Path

from app.carbon.schemas import CarbonFactor
from app.carbon.factors.registry import FactorRegistry
from app.carbon.factors.schema import FactorRecord
from app.core.config import REPO_ROOT, get_settings


def resolve_factor_file(factor_file: Path | str | None = None) -> Path:
    if factor_file is not None:
        path = Path(factor_file)
        return path if path.is_absolute() else REPO_ROOT / path

    factor_dir = Path(get_settings().factor_data_dir)
    resolved_dir = factor_dir if factor_dir.is_absolute() else REPO_ROOT / factor_dir
    return resolved_dir / "carbon_factors_v0_1_9a.json"


def resolve_v2_factor_file(factor_file: Path | str | None = None) -> Path:
    if factor_file is not None:
        path = Path(factor_file)
        return path if path.is_absolute() else REPO_ROOT / path

    factor_dir = Path(get_settings().factor_data_dir)
    resolved_dir = factor_dir if factor_dir.is_absolute() else REPO_ROOT / factor_dir
    return resolved_dir / "carbon_v2_seed.json"


def resolve_v2_factor_files(factor_file: Path | str | None = None) -> list[Path]:
    if factor_file is not None:
        return [resolve_v2_factor_file(factor_file)]

    factor_dir = Path(get_settings().factor_data_dir)
    resolved_dir = factor_dir if factor_dir.is_absolute() else REPO_ROOT / factor_dir
    return [
        resolved_dir / "carbon_v2_seed.json",
        resolved_dir / "electricity_cn_2023_official.json",
        resolved_dir / "fuel_combustion_cn_guidance_seed.json",
        resolved_dir / "carbonstop_calculator_public_seed.json",
    ]


class FactorLoadError(RuntimeError):
    """Raised when factor data cannot be loaded or validated."""


class CarbonFactorLoader:
    def __init__(self, factor_file: Path | str | None = None) -> None:
        self.factor_file = resolve_factor_file(factor_file)
        self.factor_files = resolve_v2_factor_files(factor_file)

    def _load_payload(self) -> dict:
        if not self.factor_file.exists():
            raise FactorLoadError(f"Factor file not found: {self.factor_file}")

        try:
            return json.loads(self.factor_file.read_text(encoding="utf-8"))
        except UnicodeDecodeError as exc:
            raise FactorLoadError(f"Unable to decode factor file: {self.factor_file}") from exc
        except json.JSONDecodeError as exc:
            raise FactorLoadError(f"Factor file is not valid JSON: {self.factor_file}") from exc

    def load(self) -> dict[str, CarbonFactor]:
        payload = self._load_payload()

        raw_factors = payload.get("factors")
        if not isinstance(raw_factors, list) or not raw_factors:
            records = self.load_records()
            return self._records_to_legacy_factors(records)

        factors: dict[str, CarbonFactor] = {}
        for raw_factor in raw_factors:
            try:
                factor = CarbonFactor.model_validate(raw_factor)
            except Exception as exc:  # pragma: no cover - pydantic specifics are covered by tests
                raise FactorLoadError("Factor payload validation failed.") from exc
            factors[factor.item] = factor

        required_items = {"electricity", "natural_gas", "diesel"}
        missing = required_items.difference(factors)
        if missing:
            raise FactorLoadError(f"Factor file is missing required items: {sorted(missing)}")

        return factors

    def load_records(self) -> list[FactorRecord]:
        if len(self.factor_files) > 1:
            records_by_id: dict[str, FactorRecord] = {}
            loaded_any = False
            for path in self.factor_files:
                if not path.exists():
                    continue
                loaded_any = True
                payload = self._load_payload_from(path)
                raw_v2 = payload.get("factor_records") or payload.get("factors_v2")
                if isinstance(raw_v2, list) and raw_v2:
                    try:
                        for item in raw_v2:
                            record = FactorRecord.model_validate(item)
                            records_by_id[record.factor_id] = record
                    except Exception as exc:  # pragma: no cover - pydantic internals are tested through callers
                        raise FactorLoadError(f"V2 factor payload validation failed: {path}") from exc
                else:
                    raw_calculator = payload.get("calculator_items")
                    if isinstance(raw_calculator, list) and raw_calculator:
                        try:
                            for item in raw_calculator:
                                record = self._calculator_item_to_record(item, payload)
                                records_by_id[record.factor_id] = record
                        except Exception as exc:  # pragma: no cover - defensive validation
                            raise FactorLoadError(f"Calculator factor payload validation failed: {path}") from exc
            if records_by_id:
                return list(records_by_id.values())
            if not loaded_any:
                raise FactorLoadError(f"No V2 factor files found: {self.factor_files}")

        payload = self._load_payload()
        raw_v2 = payload.get("factor_records") or payload.get("factors_v2")
        if isinstance(raw_v2, list) and raw_v2:
            try:
                return [FactorRecord.model_validate(item) for item in raw_v2]
            except Exception as exc:  # pragma: no cover - pydantic internals are tested through callers
                raise FactorLoadError("V2 factor payload validation failed.") from exc

        raw_calculator = payload.get("calculator_items")
        if isinstance(raw_calculator, list) and raw_calculator:
            try:
                return [self._calculator_item_to_record(item, payload) for item in raw_calculator]
            except Exception as exc:  # pragma: no cover - defensive validation
                raise FactorLoadError("Calculator factor payload validation failed.") from exc

        raw_factors = payload.get("factors")
        if isinstance(raw_factors, list) and raw_factors:
            return [self._legacy_factor_to_record(CarbonFactor.model_validate(item)) for item in raw_factors]

        raise FactorLoadError("Factor file must contain 'factor_records' or legacy 'factors'.")

    @staticmethod
    def _load_payload_from(path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError as exc:
            raise FactorLoadError(f"Unable to decode factor file: {path}") from exc
        except json.JSONDecodeError as exc:
            raise FactorLoadError(f"Factor file is not valid JSON: {path}") from exc

    def load_registry(self) -> FactorRegistry:
        records_by_id: dict[str, FactorRecord] = {record.factor_id: record for record in self.load_records()}
        try:
            from app.carbon_factors.service import get_carbon_factor_database_service

            get_carbon_factor_database_service().ensure_seeded()
        except Exception:
            # Runtime factor seeding is best effort for calc-carbon. If the
            # database is unavailable in isolated tests, file seeds remain the
            # deterministic fallback.
            pass
        try:
            from app.carbon_factors.store import get_carbon_factor_store

            for record in get_carbon_factor_store().list_enabled_factor_records():
                records_by_id[record.factor_id] = record
        except Exception:
            # Runtime factor DB is an enhancement over file seeds. If the runtime
            # store is unavailable during bootstrap or tests, keep the existing
            # seed fallback behavior rather than breaking calc-carbon.
            pass
        return FactorRegistry(list(records_by_id.values()))

    @staticmethod
    def _legacy_factor_to_record(factor: CarbonFactor) -> FactorRecord:
        legacy_map = {
            "electricity": ("scope2", "purchased_electricity", "kWh", "CN"),
            "natural_gas": ("scope1", "stationary_combustion", "m3", None),
            "diesel": ("scope1", "stationary_combustion", "L", None),
        }
        scope, category, activity_unit, region = legacy_map[factor.item]
        return FactorRecord(
            factor_id=factor.factor_id,
            factor_version=factor.version,
            source_type="demo",
            source_name=factor.source,
            source_url=factor.source_url,
            scope=scope,
            activity_category=category,
            activity_name=factor.item,
            region=region,
            year=None,
            factor_value=factor.value,
            factor_unit=factor.unit,
            activity_unit=activity_unit,
            result_unit="kgCO2e",
            is_default=True,
            notes=factor.note,
        )

    @staticmethod
    def _calculator_item_to_record(item: dict, payload: dict) -> FactorRecord:
        source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
        item_id = int(item["id"])
        group_key = str(item["group_key"])
        group_label = str(item["group_label"])
        name = str(item["name"])
        activity_unit = str(item["unit"])
        source_name = str(source.get("source_name") or "CarbonStop 中国碳数据库公开碳计算器")
        source_url = source.get("source_url") or "https://www.carbonstop.com/carboncalculators"
        source_type = str(source.get("source_type") or "public_calculator")
        return FactorRecord(
            factor_id=f"carbonstop-calculator-{item_id:02d}",
            factor_version=str(payload.get("version") or "public-calculator-v1"),
            source_type=source_type,
            source_name=source_name,
            source_url=source_url,
            scope="scope3",
            activity_category=f"personal_calculator_{group_key}",
            activity_name=name,
            region="CN",
            region_level="national",
            region_name="中国",
            source_priority=20,
            applicable_industry="个人生活碳计算器",
            applicable_standard="CarbonStop 公开碳计算器",
            quality_level="public_calculator",
            factor_value=float(item["factor_value"]),
            factor_unit=f"kgCO2e/{activity_unit}",
            activity_unit=activity_unit,
            result_unit="kgCO2e",
            is_default=True,
            notes=str(item.get("tip") or ""),
            tags=[
                "carbonstop_calculator",
                f"calculator_group:{group_key}",
                f"calculator_group_label:{group_label}",
                f"calculator_order:{item_id:02d}",
            ],
        )

    @staticmethod
    def _records_to_legacy_factors(records: list[FactorRecord]) -> dict[str, CarbonFactor]:
        legacy_targets = {
            "electricity": ("scope2", "purchased_electricity", "electricity"),
            "natural_gas": ("scope1", "stationary_combustion", "natural_gas"),
            "diesel": ("scope1", "stationary_combustion", "diesel"),
        }
        factors: dict[str, CarbonFactor] = {}
        for item, target in legacy_targets.items():
            candidates = [
                record
                for record in records
                if (record.scope, record.activity_category, record.activity_name) == target
            ]
            if not candidates:
                continue
            selected = sorted(
                candidates,
                key=lambda record: (
                    int(record.source_type == "official"),
                    record.year or 0,
                    int(record.is_default),
                ),
                reverse=True,
            )[0]
            factors[item] = CarbonFactor(
                factor_id=selected.factor_id,
                item=item,
                name=selected.activity_name,
                unit=selected.factor_unit,
                value=selected.factor_value,
                source=selected.source_name,
                source_url=selected.source_url or "",
                note=selected.notes or "",
                version=selected.factor_version,
            )

        required_items = {"electricity", "natural_gas", "diesel"}
        missing = required_items.difference(factors)
        if missing:
            raise FactorLoadError(f"Factor file is missing required legacy items: {sorted(missing)}")
        return factors


@lru_cache(maxsize=1)
def get_factor_loader() -> CarbonFactorLoader:
    v2_file = resolve_v2_factor_file()
    if v2_file.exists():
        return CarbonFactorLoader()
    return CarbonFactorLoader()
