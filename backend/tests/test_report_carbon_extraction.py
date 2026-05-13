from datetime import datetime, timezone

from app.ai_runtime.modes import resolve_mode
from app.ai_runtime.runtime.context_builder import build_context_bundle
from app.ai_runtime.schemas.chat import ChatRequest
from app.ai_runtime.schemas.tool import ToolResult
from app.carbon.report_extraction import ReportCarbonActivityExtractor, ReportCarbonCalculationService
from app.carbon.factors.registry import FactorRegistry
from app.carbon.factors.schema import FactorRecord
from app.carbon.schemas import (
    CalcCarbonResponse,
    CarbonBreakdownItem,
    CarbonCitation,
    CarbonScopeSummary,
)
from app.knowledge.schemas import KnowledgeChunk


def _chunk(snippet: str) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id="chunk-report-1",
        knowledge_item_id="ki-report-1",
        owner_user_id="user-1",
        title="企业碳排放报告.pdf",
        source_type="private_upload",
        library_scope="personal",
        source="用户上传报告",
        snippet=snippet,
        order_index=1,
        metadata={
            "file_id": "file-report-1",
            "page_number": 3,
            "section_title": "能源消耗明细",
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def test_report_carbon_extractor_reads_common_activity_quantities() -> None:
    result = ReportCarbonActivityExtractor().extract(
        [
            _chunk(
                "能源消耗明细：外购电力用电量 12,000 kWh；天然气消耗量 800 m3；柴油 120 L。"
            )
        ]
    )

    activities = {item.activity.activity_name: item.activity for item in result.extracted_activities}

    assert activities["electricity"].activity_value == 12000
    assert activities["electricity"].activity_unit == "kWh"
    assert activities["natural_gas"].activity_value == 800
    assert activities["diesel"].activity_value == 120
    assert activities["electricity"].entry_method == "file_upload"
    assert activities["electricity"].source_document_id == "chunk-report-1"


def test_report_carbon_extractor_reads_table_value_unit_pairs() -> None:
    result = ReportCarbonActivityExtractor().extract(
        [
            _chunk(
                "[Table docx row 1]\n指标=外购电力 | 数值=7800 | 单位=MWh | 占比=65%\n"
                "[Table docx row 2]\n指标=天然气 | 单位=m3 | 数量=3200"
            )
        ]
    )

    activities = {item.activity.activity_name: item.activity for item in result.extracted_activities}

    assert activities["electricity"].activity_value == 7800
    assert activities["electricity"].activity_unit == "MWh"
    assert activities["natural_gas"].activity_value == 3200
    assert activities["natural_gas"].activity_unit == "m3"


class _FakeFactorLoader:
    def __init__(self, records: list[FactorRecord]) -> None:
        self.records = records

    def load_registry(self) -> FactorRegistry:
        return FactorRegistry(self.records)


def test_report_carbon_extractor_matches_local_factor_database_records() -> None:
    factor = FactorRecord(
        factor_id="carbonstop-ccdb-passenger-car",
        factor_version="carbonstop-public-2023",
        source_type="public_dataset",
        source_name="CarbonStop CCDB / 北京生态环境局 / 北京普惠型资源碳减排项目要求",
        source_url="https://www.carbonstop.com/ccdb",
        scope="scope3",
        activity_category="陆上交通",
        activity_name="载客汽车",
        region="中国",
        region_level="区域排放因子",
        region_name="中国",
        year=2023,
        effective_year=2023,
        source_priority=80,
        applicable_industry="交通",
        quality_level="public_ccdb",
        factor_value=0.00024,
        factor_unit="tCO₂e/km",
        activity_unit="km",
        result_unit="tCO₂e",
        tags=["CarbonStop CCDB", "交通", "陆上交通", "0~6m"],
    )
    extractor = ReportCarbonActivityExtractor(factor_loader=_FakeFactorLoader([factor]))  # type: ignore[arg-type]

    result = extractor.extract([_chunk("差旅明细：载客汽车行驶 1,200 km，用于客户现场调研。")])

    assert len(result.extracted_activities) == 1
    activity = result.extracted_activities[0].activity
    assert activity.activity_name == "载客汽车"
    assert activity.activity_category == "陆上交通"
    assert activity.activity_value == 1200
    assert activity.activity_unit == "km"
    assert activity.requested_factor_id == "carbonstop-ccdb-passenger-car"
    assert activity.metadata["match_method"] == "local_carbon_factor_database"


def test_report_carbon_extractor_maps_common_business_alias_to_factor() -> None:
    factor = FactorRecord(
        factor_id="carbonstop-ccdb-truck",
        factor_version="carbonstop-public-2023",
        source_type="public_dataset",
        source_name="CarbonStop CCDB / 北京生态环境局",
        scope="scope3",
        activity_category="陆上交通",
        activity_name="载货汽车（含挂车）",
        source_priority=80,
        factor_value=0.000324,
        factor_unit="tCO₂e/km",
        activity_unit="km",
        result_unit="tCO₂e",
        tags=["交通", "陆上交通"],
    )
    extractor = ReportCarbonActivityExtractor(factor_loader=_FakeFactorLoader([factor]))  # type: ignore[arg-type]

    result = extractor.extract([_chunk("物流运输：货车配送距离 560 公里。")])

    assert len(result.extracted_activities) == 1
    activity = result.extracted_activities[0].activity
    assert activity.activity_name == "载货汽车（含挂车）"
    assert activity.activity_value == 560
    assert activity.activity_unit == "km"
    assert activity.requested_factor_id == "carbonstop-ccdb-truck"


def test_report_carbon_extractor_ignores_factor_values_as_activity_data() -> None:
    factor = FactorRecord(
        factor_id="carbonstop-ccdb-passenger-car",
        factor_version="carbonstop-public-2023",
        source_type="public_dataset",
        source_name="CarbonStop CCDB",
        scope="scope3",
        activity_category="陆上交通",
        activity_name="载客汽车",
        factor_value=0.00024,
        factor_unit="tCO₂e/km",
        activity_unit="km",
        result_unit="tCO₂e",
    )
    extractor = ReportCarbonActivityExtractor(factor_loader=_FakeFactorLoader([factor]))  # type: ignore[arg-type]

    result = extractor.extract([_chunk("因子表：载客汽车 0.00024 tCO₂e/km。")])

    assert result.extracted_activities == []


class _FakeCarbonService:
    def __init__(self) -> None:
        self.payload = None

    def calculate(self, *, owner_user_id: str, payload):
        self.payload = payload
        assert owner_user_id == "user-1"
        return CalcCarbonResponse(
            status="ok",
            trace_id="calc-report-1",
            inventory_id="inv-report-1",
            total_emission_kgco2e=6360,
            total_kgco2e=6360,
            breakdown=[
                CarbonBreakdownItem(
                    item="electricity",
                    scope="scope2",
                    activity_category="purchased_electricity",
                    activity_name="electricity",
                    activity_value=12000,
                    activity_unit="kWh",
                    normalized_activity_value=12000,
                    normalized_activity_unit="kWh",
                    factor_value=0.53,
                    factor_unit="kgCO2/kWh",
                    emission_kgco2e=6360,
                    factor_id="factor-electricity",
                )
            ],
            formula_summary="排放量 = 活动数据 × 排放因子",
            citations=[CarbonCitation(factor_id="factor-electricity", source="官方电力因子")],
            scope_summary=CarbonScopeSummary(scope2_location_kgco2e=6360),
        )


def test_report_carbon_calculation_service_calls_existing_carbon_engine() -> None:
    fake = _FakeCarbonService()
    service = ReportCarbonCalculationService(carbon_service=fake)  # type: ignore[arg-type]

    result = service.extract_and_calculate(
        owner_user_id="user-1",
        session_id="session-1",
        chunks=[_chunk("外购电力用电量 12,000 kWh。")],
    )

    assert result.calculation is not None
    assert result.calculation.trace_id == "calc-report-1"
    assert fake.payload.session_id == "session-1"
    assert fake.payload.activity_items[0].activity_name == "electricity"


def test_context_builder_injects_report_carbon_calculation_result() -> None:
    request = ChatRequest(
        mode="ask",
        user_input="根据报告核算碳排放。",
        payload={
            "knowledge_scope_requested": "public",
            "knowledge_scope_effective": "public",
            "attached_file_knowledge_item_ids": ["ki-report-1"],
        },
    )
    result = ToolResult(
        name="report_carbon_extract_calc",
        status="success",
        output={
            "status": "calculated",
            "extracted_activities": [
                {
                    "activity_category": "purchased_electricity",
                    "activity_name": "electricity",
                    "activity_value": 12000,
                    "activity_unit": "kWh",
                    "title": "企业碳排放报告.pdf",
                    "chunk_id": "chunk-report-1",
                    "page_number": 3,
                    "snippet": "外购电力用电量 12,000 kWh。",
                }
            ],
            "calculation": {
                "trace_id": "calc-report-1",
                "inventory_id": "inv-report-1",
                "total_emission_kgco2e": 6360,
                "breakdown": [
                    {
                        "activity_name": "electricity",
                        "activity_value": 12000,
                        "activity_unit": "kWh",
                        "factor_value": 0.53,
                        "factor_unit": "kgCO2/kWh",
                        "emission_kgco2e": 6360,
                    }
                ],
            },
            "warnings": [],
            "hits": [],
        },
        metadata={},
    )

    bundle = build_context_bundle(request, resolve_mode("ask"), tool_results=[result])

    assert "报告碳核算总量：6360 kgCO2e" in bundle["system_prompt"]
    assert bundle["report_carbon_context"]["ready"] is True

