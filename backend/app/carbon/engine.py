from dataclasses import dataclass, field

from app.carbon.factors.registry import FactorRegistry
from app.carbon.schemas import (
    CarbonActivityBatch,
    CarbonBreakdownItem,
    CarbonCitation,
    CarbonFactorSnapshot,
    CarbonFormulaTrace,
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

        if batch.legacy_mode:
            non_zero_legacy = [
                item.activity_name
                for item in batch.activity_items
                if item.activity_value > 0
            ]
            warnings.append(
                "Legacy calc-carbon fields were converted to activity_items[]. "
                f"Active legacy items: {', '.join(non_zero_legacy) or 'none'}."
            )

        for activity in batch.activity_items:
            if activity.scope == "scope1":
                selection, normalized_value, conversion_trace = self.scope1.prepare(activity)
                item_warnings = selection.warnings
            elif activity.scope == "scope2":
                selection, normalized_value, conversion_trace, item_warnings = self.scope2.prepare(activity)
            elif activity.scope == "scope3":
                raise ValueError("Scope 3 is reserved in V1.4.4 and is not calculated.")
            else:
                raise ValueError(f"Unsupported carbon scope: {activity.scope}")

            factor = selection.factor
            emission = _round_value(normalized_value * factor.factor_value)
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
        return CarbonEngineResult(
            total_emission_kgco2e=total,
            breakdown=breakdown,
            citations=list(citations_by_factor.values()),
            factor_snapshot=factor_snapshot,
            unit_conversion_trace=conversion_traces,
            formula_trace=formula_traces,
            source_summary=self._build_source_summary(factor_snapshot),
            warnings=list(dict.fromkeys(warnings)),
        )

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
