import sqlite3

from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.schemas import CalcCarbonRequest
from app.carbon.service import CarbonService
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import create_test_user_id


def test_activity_evidence_fields_are_persisted(tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    store = SQLiteSessionStore(db_path)
    session_service = SessionService(store=store)
    owner_user_id = create_test_user_id(db_path, prefix="evidence-fields")
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
                    "activity_value": 100,
                    "activity_unit": "kWh",
                    "region": "CN-NORTH",
                    "province": "CN-BJ",
                    "year": 2023,
                    "data_quality": "invoice",
                    "evidence_reference": "invoice-no-001",
                    "source_document_id": "doc-001",
                    "entry_method": "manual",
                }
            ],
        ),
    )

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        activity = connection.execute(
            "SELECT * FROM carbon_activity_items WHERE inventory_id = ?",
            (result.inventory_id,),
        ).fetchone()
        evidence = connection.execute(
            "SELECT * FROM carbon_evidence_references WHERE inventory_id = ?",
            (result.inventory_id,),
        ).fetchone()
    finally:
        connection.close()

    assert activity["province"] == "CN-BJ"
    assert activity["data_quality"] == "invoice"
    assert activity["source_document_id"] == "doc-001"
    assert evidence["evidence_reference"] == "invoice-no-001"
    assert evidence["entry_method"] == "manual"
