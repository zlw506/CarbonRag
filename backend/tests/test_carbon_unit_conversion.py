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
