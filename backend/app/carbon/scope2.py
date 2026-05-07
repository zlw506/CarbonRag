from app.carbon.schemas import CarbonActivityItem
from app.carbon.factors.registry import FactorRegistry
from app.carbon.units import UnitConverter


class Scope2Calculator:
    def __init__(self, *, registry: FactorRegistry, unit_converter: UnitConverter) -> None:
        self.registry = registry
        self.unit_converter = unit_converter

    def prepare(self, activity: CarbonActivityItem):
        if activity.activity_category != "purchased_electricity":
            raise ValueError(f"Unsupported Scope 2 category: {activity.activity_category}")
        selection = self.registry.select_factor(activity)
        normalized_value, conversion_trace = self.unit_converter.normalize(
            activity_name=activity.activity_name,
            value=activity.activity_value,
            from_unit=activity.activity_unit,
            to_unit=selection.factor.activity_unit,
        )
        warnings = list(selection.warnings)
        if activity.scope2_method != "location_based":
            warnings.append(
                "Scope 2 market-based / green power calculation is reserved in V1.4.5; "
                "location-based calculation was used and certified green power was not zeroed."
            )
        return selection, normalized_value, conversion_trace, warnings
