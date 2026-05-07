from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.engine import CarbonCalculationEngine
from app.carbon.schemas import CalcCarbonRequest


def test_scope2_location_based_electricity_uses_official_cn_2023_factor() -> None:
    registry = CarbonFactorLoader("data/factors/carbon_v2_seed.json").load_registry()
    request = CalcCarbonRequest(
        activity_items=[
            {
                "scope": "scope2",
                "activity_category": "purchased_electricity",
                "activity_name": "electricity",
                "activity_value": 1000,
                "activity_unit": "kWh",
                "region": "CN",
                "year": 2023,
                "factor_preference": "official_latest",
            }
        ]
    )

    result = CarbonCalculationEngine(registry=registry).calculate(request.to_activity_batch())

    assert result.total_emission_kgco2e == 530.6
    assert result.factor_snapshot[0].factor_id == "factor-cn-electricity-national-2023-mee-nbs"
    assert result.factor_snapshot[0].source_type == "official"


def test_scope2_market_based_is_reserved_and_does_not_zero_green_power() -> None:
    registry = CarbonFactorLoader("data/factors/carbon_v2_seed.json").load_registry()
    request = CalcCarbonRequest(
        activity_items=[
            {
                "scope": "scope2",
                "activity_category": "purchased_electricity",
                "activity_name": "electricity",
                "activity_value": 1000,
                "activity_unit": "kWh",
                "region": "CN",
                "year": 2023,
                "scope2_method": "market_based",
                "certified_green_kwh": 500,
            }
        ]
    )

    result = CarbonCalculationEngine(registry=registry).calculate(request.to_activity_batch())

    assert result.total_emission_kgco2e == 530.6
    assert any("market-based" in warning for warning in result.warnings)
