from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.schemas import CalcCarbonRequest
from app.carbon.service import CarbonService
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import create_test_user_id


def test_carbon_inventory_summary_counts_scopes_and_factor_sources(tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    store = SQLiteSessionStore(db_path)
    session_service = SessionService(store=store)
    owner_user_id = create_test_user_id(db_path, prefix="inventory-summary")
    service = CarbonService(
        factor_loader=CarbonFactorLoader(),
        session_service=session_service,
        store=store,
    )

    result = service.calculate(
        owner_user_id=owner_user_id,
        payload=CalcCarbonRequest(
            activity_items=[
                {
                    "scope": "scope2",
                    "activity_category": "purchased_electricity",
                    "activity_name": "electricity",
                    "activity_value": 1000,
                    "activity_unit": "kWh",
                    "region": "CN",
                    "year": 2023,
                },
                {
                    "scope": "scope1",
                    "activity_category": "stationary_combustion",
                    "activity_name": "diesel",
                    "activity_value": 10,
                    "activity_unit": "L",
                    "factor_preference": "official_latest",
                },
            ]
        ),
    )

    assert result.total_kgco2e == result.total_emission_kgco2e
    assert result.scope_summary.scope2_location_kgco2e == 530.6
    assert result.scope_summary.scope1_kgco2e == 27.18
    assert result.scope_summary.scope2_market_kgco2e is None
    assert result.official_factor_count == 1
    assert result.fallback_factor_count == 1
    assert result.activity_count == 2
