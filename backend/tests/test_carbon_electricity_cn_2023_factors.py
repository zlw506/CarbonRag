from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.schemas import CarbonActivityItem


def _activity(**overrides):
    payload = {
        "scope": "scope2",
        "activity_category": "purchased_electricity",
        "activity_name": "electricity",
        "activity_value": 1,
        "activity_unit": "kWh",
        "region": "CN",
        "year": 2023,
    }
    payload.update(overrides)
    return CarbonActivityItem(**payload)


def test_electricity_factor_selects_national_grid_region_and_province() -> None:
    registry = CarbonFactorLoader().load_registry()

    national = registry.select_factor(_activity(region="CN"))
    grid_region = registry.select_factor(_activity(region="CN-NORTH"))
    province = registry.select_factor(_activity(region="CN-NORTH", province="CN-BJ"))

    assert national.factor.factor_value == 0.5306
    assert national.factor.region_level == "national"
    assert grid_region.factor.factor_value == 0.6361
    assert grid_region.factor.region_level == "grid_region"
    assert province.factor.factor_value == 0.5554
    assert province.factor.region_code == "CN-BJ"


def test_electricity_factor_selects_market_based_residual_method() -> None:
    registry = CarbonFactorLoader().load_registry()

    selection = registry.select_factor(_activity(scope2_method="market_based_residual"))

    assert selection.factor.factor_id == "factor-cn-electricity-national-residual-2023-mee-nbs"
    assert selection.factor.factor_value == 0.6096
    assert selection.factor.method_type == "market_based_residual"
