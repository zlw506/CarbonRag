from dataclasses import dataclass, field

from app.carbon.factors.registry import FactorRegistry
from app.carbon.schemas import (
    CarbonActivityBatch,
    CarbonActivityItem,
    CarbonBreakdownItem,
    CarbonCitation,
    CarbonFactorSnapshot,
    CarbonFormulaTrace,
    CarbonScopeSummary,
    CarbonSourceSummaryItem,
    CarbonUnitConversionTrace,
)
from app.carbon.scope1 import Scope1Calculator
from app.carbon.scope2 import Scope2Calculator
from app.carbon.units import UnitConverter


def _round_value(value: float) -> float:
    return round(float(value), 6)


@dataclass
class CarbonEngineResult:
    total_emission_kgco2e: float
    breakdown: list[CarbonBreakdownItem]
    citations: list[CarbonCitation]
    factor_snapshot: list[CarbonFactorSnapshot]
    unit_conversion_trace: list[CarbonUnitConversionTrace]
    formula_trace: list[CarbonFormulaTrace]
    source_summary: list[CarbonSourceSummaryItem]
    scope_summary: CarbonScopeSummary
    activity_count: int
    official_factor_count: int
    fallback_factor_count: int
    warnings: list[str] = field(default_factory=list)


class CarbonCalculationEngine:
    def __init__(
        self,
        *,
        registry: FactorRegistry,
        unit_converter: UnitConverter | None = None,
    ) -> None:
        self.registry = registry
        self.unit_converter = unit_converter or UnitConverter()
        self.scope1 = Scope1Calculator(registry=registry, unit_converter=self.unit_converter)
        self.scope2 = Scope2Calculator(registry=registry, unit_converter=self.unit_converter)

    def calculate(self, batch: CarbonActivityBatch) -> CarbonEngineResult:
        breakdown: list[CarbonBreakdownItem] = []
        citations_by_factor: dict[str, CarbonCitation] = {}
        snapshots_by_factor: dict[str, CarbonFactorSnapshot] = {}
        conversion_traces: list[CarbonUnitConversionTrace] = []
        formula_traces: list[CarbonFormulaTrace] = []
        warnings: list[str] = []

        active_items = [item for item in batch.activity_items if item.activity_value > 0]

        if batch.legacy_mode:
            non_zero_legacy = [
                item.activity_name
                for item in active_items
            ]
            warnings.append(
                "Legacy calc-carbon fields were converted to activity_items[]. "
                f"Active legacy items: {', '.join(non_zero_legacy) or 'none'}."
            )

        for activity in active_items:
            if activity.scope == "scope1":
                selection, normalized_value, conversion_trace = self.scope1.prepare(activity)
                item_warnings = selection.warnings
            elif activity.scope == "scope2":
                selection, normalized_value, conversion_trace, item_warnings = self.scope2.prepare(activity)
            elif activity.scope == "scope3":
                selection, normalized_value, conversion_trace, item_warnings = self._prepare_generic(activity)
            else:
                raise ValueError(f"Unsupported carbon scope: {activity.scope}")

            factor = selection.factor
            emission = _round_value(
                normalized_value
                * factor.factor_value
                * self._result_unit_to_kgco2e_multiplier(factor.result_unit or factor.factor_unit)
            )
            item = CarbonBreakdownItem(
                item=activity.activity_name,
                scope=activity.scope,
                activity_category=activity.activity_category,
                activity_name=activity.activity_name,
                activity_value=_round_value(activity.activity_value),
                activity_unit=activity.activity_unit,
                normalized_activity_value=normalized_value,
                normalized_activity_unit=factor.activity_unit,
                factor_value=_round_value(factor.factor_value),
                factor_unit=factor.factor_unit,
                emission_kgco2e=emission,
                factor_id=factor.factor_id,
            )
            breakdown.append(item)
            conversion_traces.append(conversion_trace)
            formula_traces.append(
                CarbonFormulaTrace(
                    activity_name=activity.activity_name,
                    formula=f"{normalized_value} {factor.activity_unit} × {factor.factor_value} {factor.factor_unit}",
                    normalized_activity_value=normalized_value,
                    activity_unit=factor.activity_unit,
                    factor_value=_round_value(factor.factor_value),
                    factor_unit=factor.factor_unit,
                    emission_kgco2e=emission,
                )
            )
            snapshots_by_factor[factor.factor_id] = factor.to_snapshot()
            citations_by_factor[factor.factor_id] = CarbonCitation(
                factor_id=factor.factor_id,
                source=factor.source_name,
                source_url=factor.source_url,
            )
            warnings.extend(item_warnings)

        total = _round_value(sum(item.emission_kgco2e for item in breakdown))
        factor_snapshot = list(snapshots_by_factor.values())
        scope_summary = self._build_scope_summary(breakdown)
        official_factor_count = sum(
            1
            for snapshot in factor_snapshot
            if snapshot.is_official or snapshot.source_type == "official"
        )
        fallback_factor_count = len(factor_snapshot) - official_factor_count
        return CarbonEngineResult(
            total_emission_kgco2e=total,
            breakdown=breakdown,
            citations=list(citations_by_factor.values()),
            factor_snapshot=factor_snapshot,
            unit_conversion_trace=conversion_traces,
            formula_trace=formula_traces,
            source_summary=self._build_source_summary(factor_snapshot),
            scope_summary=scope_summary,
            activity_count=len(active_items),
            official_factor_count=official_factor_count,
            fallback_factor_count=fallback_factor_count,
            warnings=list(dict.fromkeys(warnings)),
        )

    def _prepare_generic(self, activity: CarbonActivityItem):
        selection = self.registry.select_factor(activity)
        normalized_value, conversion_trace = self.unit_converter.normalize(
            activity_name=activity.activity_name,
            value=activity.activity_value,
            from_unit=activity.activity_unit,
            to_unit=selection.factor.activity_unit,
        )
        return selection, normalized_value, conversion_trace, list(selection.warnings)

    @staticmethod
    def _result_unit_to_kgco2e_multiplier(unit: str) -> float:
        normalized = (
            unit.strip()
            .replace("₂", "2")
            .replace("二氧化碳当量", "CO2e")
            .replace("千克", "kg")
            .replace("吨", "t")
        )
        if "/" in normalized:
            normalized = normalized.split("/", 1)[0].strip()
        normalized_lower = normalized.lower()
        if normalized_lower in {"kgco2e", "kg co2e", "kg-co2e", "kgco₂e"}:
            return 1.0
        if normalized_lower in {"tco2e", "tonco2e", "tonneco2e", "t co2e", "t-co2e"}:
            return 1000.0
        if normalized_lower in {"gco2e", "g co2e", "g-co2e"}:
            return 0.001
        return 1.0

    @staticmethod
    def _build_source_summary(
        snapshots: list[CarbonFactorSnapshot],
    ) -> list[CarbonSourceSummaryItem]:
        grouped: dict[tuple[str, str, str | None], int] = {}
        for snapshot in snapshots:
            key = (snapshot.source_type, snapshot.source_name, snapshot.source_url)
            grouped[key] = grouped.get(key, 0) + 1
        return [
            CarbonSourceSummaryItem(
                source_type=source_type,
                source_name=source_name,
                source_url=source_url,
                factor_count=count,
            )
            for (source_type, source_name, source_url), count in grouped.items()
        ]

    @staticmethod
    def _build_scope_summary(breakdown: list[CarbonBreakdownItem]) -> CarbonScopeSummary:
        scope1 = 0.0
        scope2_location = 0.0
        for item in breakdown:
            if item.scope == "scope1":
                scope1 += item.emission_kgco2e
            elif item.scope == "scope2" and item.activity_category == "purchased_electricity":
                scope2_location += item.emission_kgco2e
        return CarbonScopeSummary(
            scope1_kgco2e=_round_value(scope1),
            scope2_location_kgco2e=_round_value(scope2_location),
            scope2_market_kgco2e=None,
            scope3_reserved_kgco2e=None,
        )
