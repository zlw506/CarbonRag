from app.carbon.factors.registry import FactorRegistry
from app.carbon.factors.schema import FactorRecord
from app.carbon.engine import CarbonCalculationEngine
from app.carbon.schemas import CarbonActivityBatch, CarbonActivityItem


def test_factor_registry_prefers_official_region_and_year() -> None:
    registry = FactorRegistry(
        [
            FactorRecord(
                factor_id="demo-electricity",
                factor_version="demo",
                source_type="demo",
                source_name="Demo",
                scope="scope2",
                activity_category="purchased_electricity",
                activity_name="electricity",
                region="CN",
                year=2022,
                factor_value=0.6,
                factor_unit="kgCO2e/kWh",
                activity_unit="kWh",
            ),
            FactorRecord(
                factor_id="official-electricity-2023",
                factor_version="2023",
                source_type="official",
                source_name="MEE/NBS",
                scope="scope2",
                activity_category="purchased_electricity",
                activity_name="electricity",
                region="CN",
                year=2023,
                factor_value=0.5306,
                factor_unit="kgCO2/kWh",
                activity_unit="kWh",
                is_default=True,
            ),
        ]
    )

    selection = registry.select_factor(
        CarbonActivityItem(
            scope="scope2",
            activity_category="purchased_electricity",
            activity_name="electricity",
            activity_value=1,
            activity_unit="kWh",
            region="CN",
            year=2023,
            factor_preference="official_latest",
        )
    )

    assert selection.factor.factor_id == "official-electricity-2023"
    assert selection.factor.factor_value == 0.5306


def test_factor_registry_marks_demo_fallback_warning() -> None:
    registry = FactorRegistry(
        [
            FactorRecord(
                factor_id="demo-diesel",
                factor_version="demo",
                source_type="demo",
                source_name="Demo",
                scope="scope1",
                activity_category="stationary_combustion",
                activity_name="diesel",
                factor_value=2.63,
                factor_unit="kgCO2e/L",
                activity_unit="L",
            )
        ]
    )

    selection = registry.select_factor(
        CarbonActivityItem(
            scope="scope1",
            activity_category="stationary_combustion",
            activity_name="diesel",
            activity_value=10,
            activity_unit="L",
            factor_preference="official_latest",
        )
    )

    assert selection.factor.factor_id == "demo-diesel"
    assert any("demo" in warning for warning in selection.warnings)


def test_engine_converts_tco2e_carbonstop_result_units_to_kgco2e() -> None:
    registry = FactorRegistry(
        [
            FactorRecord(
                factor_id="carbonstop-ccdb-passenger-car",
                factor_version="2023",
                source_type="public_dataset",
                source_name="CarbonStop CCDB",
                scope="scope3",
                activity_category="陆上交通",
                activity_name="载客汽车",
                factor_value=0.00024,
                factor_unit="tCO₂e/km",
                activity_unit="km",
                result_unit="tCO₂e",
            )
        ]
    )

    result = CarbonCalculationEngine(registry=registry).calculate(
        CarbonActivityBatch(
            activity_items=[
                CarbonActivityItem(
                    scope="scope3",
                    activity_category="陆上交通",
                    activity_name="载客汽车",
                    activity_value=1000,
                    activity_unit="km",
                    requested_factor_id="carbonstop-ccdb-passenger-car",
                )
            ]
        )
    )

    assert result.total_emission_kgco2e == 240
