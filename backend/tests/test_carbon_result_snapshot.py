from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.service import CarbonService
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import create_test_user_id
from app.carbon.schemas import CalcCarbonRequest


def test_carbon_result_snapshot_is_persisted(tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    store = SQLiteSessionStore(db_path)
    session_service = SessionService(store=store)
    owner_user_id = create_test_user_id(db_path, prefix="calc-snapshot")
    session = session_service.create_session(owner_user_id=owner_user_id)
    service = CarbonService(
        factor_loader=CarbonFactorLoader("data/factors/carbon_v2_seed.json"),
        session_service=session_service,
        store=store,
    )

    result = service.calculate(
        owner_user_id=owner_user_id,
        payload=CalcCarbonRequest(
            session_id=session.session_id,
            activity_items=[
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
        ),
    )
    stored = service.get_stored_calculation(owner_user_id=owner_user_id, trace_id=result.trace_id)

    assert stored is not None
    assert stored.factor_snapshot[0].factor_value == 0.5306
    assert stored.unit_conversion_trace[0].normalized_unit == "kWh"
    assert stored.formula_trace[0].emission_kgco2e == 530.6
    assert stored.source_summary[0].factor_count == 1
