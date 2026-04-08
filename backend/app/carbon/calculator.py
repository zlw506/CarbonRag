from app.carbon.schemas import CarbonBreakdownItem, CarbonFactor, CalcCarbonRequest


ACTIVITY_CONFIG = {
    "electricity": ("electricity_kwh", "kWh"),
    "natural_gas": ("natural_gas_m3", "m3"),
    "diesel": ("diesel_l", "L"),
}


def _round_value(value: float) -> float:
    return round(float(value), 6)


class CarbonCalculator:
    def calculate(
        self,
        *,
        request: CalcCarbonRequest,
        factors: dict[str, CarbonFactor],
    ) -> tuple[list[CarbonBreakdownItem], float]:
        breakdown: list[CarbonBreakdownItem] = []

        for item, (field_name, activity_unit) in ACTIVITY_CONFIG.items():
            factor = factors[item]
            activity_value = float(getattr(request, field_name))
            emission = activity_value * factor.value
            breakdown.append(
                CarbonBreakdownItem(
                    item=item,
                    activity_value=_round_value(activity_value),
                    activity_unit=activity_unit,
                    factor_value=_round_value(factor.value),
                    factor_unit=factor.unit,
                    emission_kgco2e=_round_value(emission),
                    factor_id=factor.factor_id,
                )
            )

        total = _round_value(sum(item.emission_kgco2e for item in breakdown))
        return breakdown, total
