import json
import sqlite3

from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.schemas import CalcCarbonRequest
from app.carbon.service import CarbonService
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import create_test_user_id


def test_inventory_persistence_keeps_raw_request_and_activity_items(tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    store = SQLiteSessionStore(db_path)
    session_service = SessionService(store=store)
    owner_user_id = create_test_user_id(db_path, prefix="inventory-persistence")
    service = CarbonService(
        factor_loader=CarbonFactorLoader(),
        session_service=session_service,
        store=store,
    )

    result = service.calculate(
        owner_user_id=owner_user_id,
        payload=CalcCarbonRequest(
            organization_id="org_demo",
            facility_id="facility_demo",
            period_start="2026-01-01",
            period_end="2026-03-31",
            inventory_standard="org_basic_v1",
            activity_items=[
                {
                    "scope": "scope2",
                    "activity_category": "purchased_electricity",
                    "activity_name": "electricity",
                    "activity_value": 12000,
                    "activity_unit": "kWh",
                    "region": "CN",
                    "year": 2023,
                }
            ],
        ),
    )

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        inventory = connection.execute(
            "SELECT * FROM carbon_inventories WHERE inventory_id = ?",
            (result.inventory_id,),
        ).fetchone()
        activities = connection.execute(
            "SELECT * FROM carbon_activity_items WHERE inventory_id = ? ORDER BY order_index",
            (result.inventory_id,),
        ).fetchall()
        lines = connection.execute(
            "SELECT * FROM carbon_calculation_lines WHERE inventory_id = ?",
            (result.inventory_id,),
        ).fetchall()
        snapshots = connection.execute(
            "SELECT * FROM carbon_factor_snapshots WHERE inventory_id = ?",
            (result.inventory_id,),
        ).fetchall()
    finally:
        connection.close()

    assert inventory is not None
    assert inventory["organization_id"] == "org_demo"
    assert inventory["facility_id"] == "facility_demo"
    assert json.loads(inventory["raw_payload_json"])["organization_id"] == "org_demo"
    assert json.loads(inventory["activity_items_raw_json"])[0]["activity_name"] == "electricity"
    assert len(activities) == 1
    assert len(lines) == 1
    assert len(snapshots) == 1
    assert json.loads(snapshots[0]["snapshot_json"])["factor_value"] == 0.5306
