from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.schemas import CalcCarbonRequest
from app.carbon.service import CarbonService
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import create_test_user_id


def test_legacy_payload_filters_zero_values_and_warnings(tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    store = SQLiteSessionStore(db_path)
    session_service = SessionService(store=store)
    owner_user_id = create_test_user_id(db_path, prefix="legacy-zero")
    service = CarbonService(
        factor_loader=CarbonFactorLoader(),
        session_service=session_service,
        store=store,
    )

    result = service.calculate(
        owner_user_id=owner_user_id,
        payload=CalcCarbonRequest(electricity_kwh=100),
    )

    assert [item.activity_name for item in result.breakdown] == ["electricity"]
    assert result.activity_count == 1
    assert not any("natural_gas" in warning or "diesel" in warning for warning in result.warnings)
