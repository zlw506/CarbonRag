from app.carbon.engine import CarbonCalculationEngine
from app.carbon.factors.registry import FactorRegistry
from app.carbon.factors.schema import FactorRecord
from app.carbon.schemas import CalcCarbonRequest


def test_scope1_stationary_combustion_calculates_multiple_fuels() -> None:
    registry = FactorRegistry(
        [
            FactorRecord(
                factor_id="demo-natural-gas",
                factor_version="demo",
                source_type="demo",
                source_name="Demo",
                scope="scope1",
                activity_category="stationary_combustion",
                activity_name="natural_gas",
                factor_value=2.162,
                factor_unit="kgCO2e/m3",
                activity_unit="m3",
            ),
            FactorRecord(
                factor_id="demo-gasoline",
                factor_version="demo",
                source_type="demo",
                source_name="Demo",
                scope="scope1",
                activity_category="stationary_combustion",
                activity_name="gasoline",
                factor_value=2.32,
                factor_unit="kgCO2e/L",
                activity_unit="L",
            ),
        ]
    )
    request = CalcCarbonRequest(
        activity_items=[
            {
                "scope": "scope1",
                "activity_category": "stationary_combustion",
                "activity_name": "natural_gas",
                "activity_value": 10,
                "activity_unit": "m3",
                "factor_preference": "demo_allowed",
            },
            {
                "scope": "scope1",
                "activity_category": "stationary_combustion",
                "activity_name": "gasoline",
                "activity_value": 5,
                "activity_unit": "L",
                "factor_preference": "demo_allowed",
            },
        ]
    )

    result = CarbonCalculationEngine(registry=registry).calculate(request.to_activity_batch())

    assert result.total_emission_kgco2e == 33.22
    assert len(result.factor_snapshot) == 2
    assert result.warnings


def test_scope1_mobile_combustion_minimal_vehicle_support() -> None:
    registry = FactorRegistry(
        [
            FactorRecord(
                factor_id="demo-diesel-vehicle",
                factor_version="demo",
                source_type="demo",
                source_name="Demo",
                scope="scope1",
                activity_category="mobile_combustion",
                activity_name="diesel_vehicle",
                factor_value=2.63,
                factor_unit="kgCO2e/L",
                activity_unit="L",
            )
        ]
    )
    request = CalcCarbonRequest(
        activity_items=[
            {
                "scope": "scope1",
                "activity_category": "mobile_combustion",
                "activity_name": "diesel_vehicle",
                "activity_value": 20,
                "activity_unit": "L",
                "factor_preference": "demo_allowed",
            }
        ]
    )

    result = CarbonCalculationEngine(registry=registry).calculate(request.to_activity_batch())

    assert result.total_emission_kgco2e == 52.6
    assert result.breakdown[0].activity_category == "mobile_combustion"
