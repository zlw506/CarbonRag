import json

from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.schemas import CalcCarbonRequest
from app.carbon.service import CarbonService
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import create_test_user_id


def test_legacy_three_field_payload_still_calculates(tmp_path) -> None:
    factor_file = tmp_path / "legacy_factors.json"
    factor_file.write_text(
        json.dumps(
            {
                "version": "legacy",
                "factors": [
                    {
                        "factor_id": "factor-electricity",
                        "item": "electricity",
                        "name": "Electricity Demo Factor",
                        "unit": "kgCO2e/kWh",
                        "value": 0.57,
                        "source": "Demo Source",
                        "source_url": "https://example.com/electricity",
                        "note": "demo",
                        "version": "legacy",
                    },
                    {
                        "factor_id": "factor-natural-gas",
                        "item": "natural_gas",
                        "name": "Natural Gas Demo Factor",
                        "unit": "kgCO2e/m3",
                        "value": 2.162,
                        "source": "Demo Source",
                        "source_url": "https://example.com/gas",
                        "note": "demo",
                        "version": "legacy",
                    },
                    {
                        "factor_id": "factor-diesel",
                        "item": "diesel",
                        "name": "Diesel Demo Factor",
                        "unit": "kgCO2e/L",
                        "value": 2.63,
                        "source": "Demo Source",
                        "source_url": "https://example.com/diesel",
                        "note": "demo",
                        "version": "legacy",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    db_path = tmp_path / "carbonrag.sqlite3"
    store = SQLiteSessionStore(db_path)
    session_service = SessionService(store=store)
    owner_user_id = create_test_user_id(db_path, prefix="legacy-calc")
    service = CarbonService(
        factor_loader=CarbonFactorLoader(factor_file),
        session_service=session_service,
        store=store,
    )

    result = service.calculate(
        owner_user_id=owner_user_id,
        payload=CalcCarbonRequest(electricity_kwh=100, natural_gas_m3=50, diesel_l=10),
    )

    assert result.total_emission_kgco2e == round((100 * 0.57) + (50 * 2.162) + (10 * 2.63), 6)
    assert len(result.breakdown) == 3
    assert len(result.factor_snapshot) == 3
    assert any("Legacy calc-carbon fields" in warning for warning in result.warnings)
