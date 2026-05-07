import pytest
from pydantic import ValidationError

from app.carbon.schemas import CalcCarbonRequest


def test_calc_request_accepts_activity_items_v2() -> None:
    request = CalcCarbonRequest(
        organization_id="org_demo",
        facility_id="facility_demo",
        period_start="2026-01-01",
        period_end="2026-03-31",
        activity_items=[
            {
                "scope": "scope2",
                "activity_category": "purchased_electricity",
                "activity_name": "electricity",
                "activity_value": 12000,
                "activity_unit": "kWh",
                "region": "CN",
                "province": "CN-BJ",
                "year": 2023,
                "data_quality": "invoice",
                "entry_method": "manual",
                "evidence_reference": "invoice-2026-q1",
                "source_document_id": "doc-electricity-001",
            }
        ],
    )

    batch = request.to_activity_batch()

    assert batch.legacy_mode is False
    assert batch.organization_id == "org_demo"
    assert batch.activity_items[0].activity_name == "electricity"
    assert batch.activity_items[0].province == "CN-BJ"
    assert batch.activity_items[0].data_quality == "invoice"
    assert batch.activity_items[0].source_document_id == "doc-electricity-001"


def test_calc_request_converts_legacy_fields_to_activity_items() -> None:
    request = CalcCarbonRequest(electricity_kwh=100, natural_gas_m3=10, diesel_l=5)

    batch = request.to_activity_batch()

    assert batch.legacy_mode is True
    assert [item.activity_name for item in batch.activity_items] == [
        "electricity",
        "natural_gas",
        "diesel",
    ]


def test_legacy_zero_fields_are_not_converted_to_activity_items() -> None:
    request = CalcCarbonRequest(electricity_kwh=100)

    batch = request.to_activity_batch()

    assert batch.legacy_mode is True
    assert [item.activity_name for item in batch.activity_items] == ["electricity"]


def test_calc_request_rejects_empty_activity_payload() -> None:
    with pytest.raises(ValidationError):
        CalcCarbonRequest(activity_items=[])
