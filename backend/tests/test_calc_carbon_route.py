import json

from fastapi.testclient import TestClient

from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.service import CarbonService
from app.main import app
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import patch_test_auth_service, register_and_login

client = TestClient(app)


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


def build_test_service(tmp_path) -> tuple[SessionService, CarbonService]:
    store = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    session_service = SessionService(store=store)
    factor_loader = CarbonFactorLoader(build_factor_file(tmp_path))
    carbon_service = CarbonService(
        factor_loader=factor_loader,
        session_service=session_service,
        store=store,
    )
    return session_service, carbon_service


def test_calc_carbon_route_returns_breakdown_and_citations(monkeypatch, tmp_path) -> None:
    session_service, carbon_service = build_test_service(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.calc_carbon.get_carbon_service", lambda: carbon_service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    register_and_login(client, prefix="calc-ok")
    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]
    response = client.post(
        "/api/v1/calc-carbon",
        json={
            "session_id": session_id,
            "period_label": "2026-Q1",
            "electricity_kwh": 12000,
            "natural_gas_m3": 800,
            "diesel_l": 120,
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["trace_id"].startswith("calc-")
    assert len(payload["breakdown"]) == 3
    assert len(payload["citations"]) == 3


def test_calc_carbon_route_accepts_activity_items_v2(monkeypatch, tmp_path) -> None:
    store = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    session_service = SessionService(store=store)
    carbon_service = CarbonService(
        factor_loader=CarbonFactorLoader("data/factors/carbon_v2_seed.json"),
        session_service=session_service,
        store=store,
    )
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.calc_carbon.get_carbon_service", lambda: carbon_service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    register_and_login(client, prefix="calc-v2")
    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]
    response = client.post(
        "/api/v1/calc-carbon",
        json={
            "session_id": session_id,
            "organization_id": "org_demo",
            "facility_id": "facility_demo",
            "period_start": "2026-01-01",
            "period_end": "2026-03-31",
            "activity_items": [
                {
                    "scope": "scope2",
                    "activity_category": "purchased_electricity",
                    "activity_name": "electricity",
                    "activity_value": 1000,
                    "activity_unit": "kWh",
                    "region": "CN",
                    "year": 2023,
                }
            ],
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["total_emission_kgco2e"] == 530.6
    assert payload["factor_snapshot"][0]["factor_value"] == 0.5306
    assert payload["unit_conversion_trace"][0]["normalized_unit"] == "kWh"
    assert payload["formula_trace"][0]["emission_kgco2e"] == 530.6


def test_calc_carbon_route_rejects_unknown_session(monkeypatch, tmp_path) -> None:
    _, carbon_service = build_test_service(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.calc_carbon.get_carbon_service", lambda: carbon_service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    register_and_login(client, prefix="calc-missing")
    response = client.post(
        "/api/v1/calc-carbon",
        json={
            "session_id": "session-missing",
            "electricity_kwh": 100,
        },
    )

    assert response.status_code == 404


def test_calc_carbon_route_rejects_all_zero_activity(monkeypatch, tmp_path) -> None:
    _, carbon_service = build_test_service(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.calc_carbon.get_carbon_service", lambda: carbon_service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    register_and_login(client, prefix="calc-zero")
    response = client.post(
        "/api/v1/calc-carbon",
        json={
            "electricity_kwh": 0,
            "natural_gas_m3": 0,
            "diesel_l": 0,
        },
    )

    assert response.status_code == 422
