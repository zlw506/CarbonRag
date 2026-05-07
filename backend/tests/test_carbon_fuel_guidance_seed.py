from app.carbon.engine import CarbonCalculationEngine
from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.schemas import CalcCarbonRequest


def test_fuel_guidance_default_seed_calculates_with_warning() -> None:
    registry = CarbonFactorLoader().load_registry()
    request = CalcCarbonRequest(
        activity_items=[
            {
                "scope": "scope1",
                "activity_category": "stationary_combustion",
                "activity_name": "natural_gas",
                "activity_value": 10,
                "activity_unit": "m3",
                "factor_preference": "official_latest",
            }
        ]
    )

    result = CarbonCalculationEngine(registry=registry).calculate(request.to_activity_batch())

    assert result.total_emission_kgco2e == 21.84
    assert result.factor_snapshot[0].source_type == "guidance_default"
    assert result.fallback_factor_count == 1
    assert any("guidance_default" in warning for warning in result.warnings)
