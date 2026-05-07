from app.carbon.factors.registry import FactorRegistry
from app.carbon.factors.schema import FactorRecord
from app.carbon.schemas import CarbonActivityItem


def _factor(factor_id: str, source_type: str, value: float, **overrides) -> FactorRecord:
    payload = {
        "factor_id": factor_id,
        "factor_version": "v1",
        "source_type": source_type,
        "source_name": source_type,
        "scope": "scope2",
        "activity_category": "purchased_electricity",
        "activity_name": "electricity",
        "region": "CN",
        "region_level": "national",
        "region_code": "CN",
        "year": 2023,
        "method_type": "location_based",
        "factor_value": value,
        "factor_unit": "kgCO2/kWh",
        "activity_unit": "kWh",
        "is_official": source_type == "official",
    }
    payload.update(overrides)
    return FactorRecord(**payload)


def _activity(**overrides) -> CarbonActivityItem:
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


def test_requested_factor_id_overrides_default_priority() -> None:
    registry = FactorRegistry(
        [
            _factor("official-default", "official", 0.5, is_default=True),
            _factor("requested-demo", "demo", 0.9),
        ]
    )

    selection = registry.select_factor(_activity(requested_factor_id="requested-demo"))

    assert selection.factor.factor_id == "requested-demo"


def test_region_year_priority_falls_back_to_national_official_before_guidance() -> None:
    registry = FactorRegistry(
        [
            _factor(
                "official-national",
                "official",
                0.53,
                region="CN",
                region_level="national",
                region_code="CN",
            ),
            _factor(
                "guidance-province",
                "guidance_default",
                0.7,
                region="CN-NORTH",
                region_level="province",
                region_code="CN-BJ",
            ),
        ]
    )

    selection = registry.select_factor(_activity(region="CN-NORTH", province="CN-SH"))

    assert selection.factor.factor_id == "official-national"
    assert any("未命中请求地区" in warning for warning in selection.warnings)
