from app.carbon.calculator import CarbonCalculator
from app.carbon.schemas import CarbonFactor, CalcCarbonRequest


def build_factors() -> dict[str, CarbonFactor]:
    return {
        "electricity": CarbonFactor(
            factor_id="factor-electricity",
            item="electricity",
            name="Electricity Demo Factor",
            unit="kgCO2e/kWh",
            value=0.57,
            source="Demo Source",
            source_url="https://example.com/electricity",
            note="demo",
            version="v0.1.9a",
        ),
        "natural_gas": CarbonFactor(
            factor_id="factor-natural-gas",
            item="natural_gas",
            name="Natural Gas Demo Factor",
            unit="kgCO2e/m3",
            value=2.162,
            source="Demo Source",
            source_url="https://example.com/gas",
            note="demo",
            version="v0.1.9a",
        ),
        "diesel": CarbonFactor(
            factor_id="factor-diesel",
            item="diesel",
            name="Diesel Demo Factor",
            unit="kgCO2e/L",
            value=2.63,
            source="Demo Source",
            source_url="https://example.com/diesel",
            note="demo",
            version="v0.1.9a",
        ),
    }


def test_carbon_calculator_handles_single_activity_input() -> None:
    request = CalcCarbonRequest(electricity_kwh=1000)
    breakdown, total = CarbonCalculator().calculate(request=request, factors=build_factors())

    assert total == 570.0
    assert breakdown[0].emission_kgco2e == 570.0
    assert breakdown[1].emission_kgco2e == 0.0
    assert breakdown[2].emission_kgco2e == 0.0


def test_carbon_calculator_handles_multiple_activity_inputs() -> None:
    request = CalcCarbonRequest(electricity_kwh=100, natural_gas_m3=50, diesel_l=10)
    breakdown, total = CarbonCalculator().calculate(request=request, factors=build_factors())

    expected_total = round((100 * 0.57) + (50 * 2.162) + (10 * 2.63), 6)
    assert total == expected_total
    assert len(breakdown) == 3
