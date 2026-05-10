import sqlite3

from app.carbon.engine import CarbonCalculationEngine
from app.carbon.factor_loader import CarbonFactorLoader
from app.carbon.schemas import CalcCarbonRequest, CarbonActivityItem
from app.carbon.factors.registry import FactorRegistry
from app.carbon_factors.carbonstop import CarbonStopPublicAdapter
from app.carbon_factors.service import CarbonFactorDatabaseService
from app.carbon_factors.store import CarbonFactorStore


def build_service(tmp_path) -> CarbonFactorDatabaseService:
    store = CarbonFactorStore(sqlite_db_path=tmp_path / "runtime.sqlite3")
    return CarbonFactorDatabaseService(store=store, carbonstop_adapter=CarbonStopPublicAdapter())


def test_carbonstop_seed_imports_public_calculation_ready_rows(tmp_path) -> None:
    service = build_service(tmp_path)

    job = service.import_carbonstop_seed(owner_user_id="tester")
    result = service.search(q="载货汽车", page_size=10)
    facets = service.facets()

    assert job.summary["catalog_count"] >= job.summary["accepted_count"]
    assert job.summary["accepted_count"] > 200
    assert job.summary["skipped_count"] > 0
    assert result.total >= 1
    assert result.items[0].source is not None
    assert "carbonstop.com/ccdb" in (result.items[0].source.source_url or "")
    assert any(node["label"] == "交通" for node in facets.category_tree)


def test_carbonstop_public_catalog_keeps_encrypted_rows_visible(tmp_path) -> None:
    service = build_service(tmp_path)
    service.import_carbonstop_seed(owner_user_id="tester")

    catalog = service.search_catalog(industry="交通", category="陆上交通", page_size=30)
    calculation_ready = service.search(industry="交通", category="陆上交通", page_size=30)
    encrypted = service.search_catalog(industry="交通", category="陆上交通", value_status="encrypted", page_size=30)

    assert catalog.total == 18
    assert calculation_ready.total == 12
    assert encrypted.total == 6
    assert any(not item.is_calculation_ready for item in catalog.items)
    assert any(item.raw_value for item in catalog.items)


def test_carbonstop_category_tree_matches_parent_and_child_filters(tmp_path) -> None:
    service = build_service(tmp_path)
    service.import_carbonstop_seed(owner_user_id="tester")

    result = service.search(industry="交通", category="陆上交通", page_size=20)
    facets = service.facets()
    traffic = next(node for node in facets.category_tree if node["label"] == "交通")
    land = next(child for child in traffic["children"] if child["label"] == "陆上交通")

    assert result.total == land["count"]
    assert result.total > 0
    assert all(item.industry == "交通" for item in result.items)
    assert all(item.category == "陆上交通" for item in result.items)


def test_carbon_factor_detail_preserves_raw_source_snapshot(tmp_path) -> None:
    service = build_service(tmp_path)
    service.import_carbonstop_seed(owner_user_id="tester")
    result = service.search(q="载客汽车", page_size=1)

    detail = service.get_factor(factor_id=result.items[0].factor_id)

    assert detail is not None
    assert detail.metadata["source_platform"] == "CarbonStop CCDB 中国碳数据库"
    assert detail.metadata["raw_row"]["name"] == detail.name
    assert detail.factor_value > 0


def test_factor_registry_reads_runtime_db_before_file_seed(tmp_path) -> None:
    service = build_service(tmp_path)
    service.import_carbonstop_seed(owner_user_id="tester")

    records = service.store.list_enabled_factor_records()
    registry = FactorRegistry(records)
    selected = registry.select_factor(
        CarbonActivityItem(
            scope="scope3",
            activity_category="陆上交通",
            activity_name="载货汽车（含挂车）",
            activity_value=1,
            activity_unit="km",
        )
    )

    assert selected.factor.factor_id.startswith("carbonstop-ccdb-")


def test_carbonstop_public_factor_can_drive_scope3_calculation(tmp_path) -> None:
    service = build_service(tmp_path)
    service.import_carbonstop_seed(owner_user_id="tester")

    records = service.store.list_enabled_factor_records()
    registry = FactorRegistry(records)
    result = CarbonCalculationEngine(registry=registry).calculate(
        CalcCarbonRequest(
            activity_items=[
                {
                    "scope": "scope3",
                    "activity_category": "陆上交通",
                    "activity_name": "载客汽车",
                    "activity_value": 10,
                    "activity_unit": "km",
                    "requested_factor_id": "carbonstop-ccdb-1704587623764736",
                }
            ]
        ).to_activity_batch()
    )

    assert result.breakdown[0].factor_id == "carbonstop-ccdb-1704587623764736"
    assert result.total_emission_kgco2e == 2.4


def test_carbonstop_calculator_seed_contains_public_lifestyle_catalog() -> None:
    records = [
        record
        for record in CarbonFactorLoader().load_records()
        if "carbonstop_calculator" in record.tags
    ]

    assert len(records) == 42
    assert {record.activity_name for record in records} >= {"涤纶织物", "纯棉T恤", "用电", "飞机", "城市垃圾"}
    assert {record.activity_category for record in records} == {
        "personal_calculator_clothes",
        "personal_calculator_food",
        "personal_calculator_home",
        "personal_calculator_travel",
        "personal_calculator_daily",
    }


def test_carbonstop_calculator_seed_can_drive_lifestyle_calculation() -> None:
    registry = CarbonFactorLoader().load_registry()

    result = CarbonCalculationEngine(registry=registry).calculate(
        CalcCarbonRequest(
            activity_items=[
                {
                    "scope": "scope3",
                    "activity_category": "personal_calculator_clothes",
                    "activity_name": "纯棉T恤",
                    "activity_value": 2,
                    "activity_unit": "件",
                    "factor_preference": "public_calculator",
                    "requested_factor_id": "carbonstop-calculator-02",
                }
            ]
        ).to_activity_batch()
    )

    assert result.breakdown[0].factor_id == "carbonstop-calculator-02"
    assert result.total_emission_kgco2e == 14


def test_runtime_factor_loader_keeps_seed_fallback_when_db_unavailable(monkeypatch) -> None:
    loader = CarbonFactorLoader()
    monkeypatch.setattr("app.carbon_factors.store.get_carbon_factor_store", lambda: (_ for _ in ()).throw(RuntimeError("db down")))

    registry = loader.load_registry()

    selected = registry.select_factor(
        CarbonActivityItem(
            scope="scope2",
            activity_category="purchased_electricity",
            activity_name="electricity",
            activity_value=1,
            activity_unit="kWh",
        )
    )
    assert selected.factor.factor_id


def test_sqlite_factor_tables_are_queryable_after_seed(tmp_path) -> None:
    service = build_service(tmp_path)
    service.ensure_seeded()
    connection = sqlite3.connect(tmp_path / "runtime.sqlite3")
    try:
        count = connection.execute("SELECT COUNT(*) FROM carbon_factor_records").fetchone()[0]
        catalog_count = connection.execute("SELECT COUNT(*) FROM carbon_factor_catalog_entries").fetchone()[0]
        source_count = connection.execute("SELECT COUNT(*) FROM carbon_factor_sources").fetchone()[0]
    finally:
        connection.close()

    assert count > 200
    assert catalog_count > count
    assert source_count > 0
