from app.carbon.units import UnitConverter


def test_unit_converter_normalizes_mwh_to_kwh() -> None:
    value, trace = UnitConverter().normalize(
        activity_name="electricity",
        value=1.5,
        from_unit="MWh",
        to_unit="kWh",
    )

    assert value == 1500
    assert trace.conversion_factor == 1000
    assert trace.normalized_unit == "kWh"


def test_unit_converter_normalizes_tonne_to_kg() -> None:
    value, trace = UnitConverter().normalize(
        activity_name="coal",
        value=2,
        from_unit="t",
        to_unit="kg",
    )

    assert value == 2000
    assert trace.normalized_unit == "kg"


def test_unit_converter_normalizes_report_activity_units() -> None:
    value, trace = UnitConverter().normalize(
        activity_name="载客汽车",
        value=12,
        from_unit="公里",
        to_unit="km",
    )

    assert value == 12
    assert trace.normalized_unit == "km"

    area, area_trace = UnitConverter().normalize(
        activity_name="建筑面积",
        value=300,
        from_unit="平方米",
        to_unit="m2",
    )
    assert area == 300
    assert area_trace.normalized_unit == "m2"
