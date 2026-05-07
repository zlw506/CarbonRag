from app.carbon.schemas import CarbonActivityItem
from app.carbon.factors.registry import FactorRegistry
from app.carbon.units import UnitConverter


class Scope1Calculator:
    SUPPORTED_CATEGORIES = {"stationary_combustion", "mobile_combustion"}

    def __init__(self, *, registry: FactorRegistry, unit_converter: UnitConverter) -> None:
        self.registry = registry
        self.unit_converter = unit_converter

    def prepare(self, activity: CarbonActivityItem):
        if activity.activity_category not in self.SUPPORTED_CATEGORIES:
            raise ValueError(f"Unsupported Scope 1 category: {activity.activity_category}")
        selection = self.registry.select_factor(activity)
        normalized_value, conversion_trace = self.unit_converter.normalize(
            activity_name=activity.activity_name,
            value=activity.activity_value,
            from_unit=activity.activity_unit,
            to_unit=selection.factor.activity_unit,
        )
        return selection, normalized_value, conversion_trace
