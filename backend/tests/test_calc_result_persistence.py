import json

from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.service import CarbonService
from app.carbon.schemas import CalcCarbonRequest
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService


def build_factor_file(tmp_path):
    payload = {
        "version": "v0.1.9a",
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
                "version": "v0.1.9a",
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
                "version": "v0.1.9a",
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
                "version": "v0.1.9a",
            },
        ],
    }
    factor_file = tmp_path / "factors.json"
    factor_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return factor_file


def test_calc_result_is_persisted_to_runtime_database(tmp_path) -> None:
    store = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    session_service = SessionService(store=store)
    session = session_service.create_session()
    service = CarbonService(
        factor_loader=CarbonFactorLoader(build_factor_file(tmp_path)),
        session_service=session_service,
        store=store,
    )

    result = service.calculate(
        CalcCarbonRequest(
            session_id=session.session_id,
            period_label="2026-Q1",
            electricity_kwh=12000,
            natural_gas_m3=800,
            diesel_l=120,
        )
    )
    stored = service.get_stored_calculation(result.trace_id)

    assert stored is not None
    assert stored.session_id == session.session_id
    assert stored.total_emission_kgco2e == result.total_emission_kgco2e
    assert len(stored.breakdown) == 3
    assert len(stored.citations) == 3
