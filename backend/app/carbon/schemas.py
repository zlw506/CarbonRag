from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CarbonFactor(BaseModel):
    factor_id: str
    item: Literal["electricity", "natural_gas", "diesel"]
    name: str
    unit: str
    value: float
    source: str
    source_url: str
    note: str
    version: str


CarbonScope = Literal["scope1", "scope2", "scope3"]


class CarbonActivityItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: CarbonScope
    activity_category: str
    activity_name: str
    activity_value: float = Field(ge=0)
    activity_unit: str
    region: str | None = None
    year: int | None = None
    factor_preference: str = "official_latest"
    scope2_method: str = "location_based"
    certified_green_kwh: float | None = Field(default=None, ge=0)
    evidence_reference: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator(
        "activity_category",
        "activity_name",
        "activity_unit",
        "region",
        "factor_preference",
        "scope2_method",
        "evidence_reference",
    )
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class CarbonActivityBatch(BaseModel):
    organization_id: str | None = None
    facility_id: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    inventory_standard: str = "org_basic_v1"
    activity_items: list[CarbonActivityItem]
    legacy_mode: bool = False


class CalcCarbonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str | None = None
    period_label: str | None = None
    organization_id: str | None = None
    facility_id: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    inventory_standard: str = "org_basic_v1"
    activity_items: list[CarbonActivityItem] = Field(default_factory=list)
    electricity_kwh: float = Field(default=0, ge=0)
    natural_gas_m3: float = Field(default=0, ge=0)
    diesel_l: float = Field(default=0, ge=0)

    @field_validator("session_id", "period_label", "organization_id", "facility_id", "inventory_standard")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def require_any_activity(self) -> "CalcCarbonRequest":
        legacy_has_activity = (
            self.electricity_kwh == 0
            and self.natural_gas_m3 == 0
            and self.diesel_l == 0
        ) is False
        v2_has_activity = any(item.activity_value > 0 for item in self.activity_items)
        if not legacy_has_activity and not v2_has_activity:
            raise ValueError("At least one activity value must be greater than zero.")
        return self

    def to_activity_batch(self) -> CarbonActivityBatch:
        if self.activity_items:
            return CarbonActivityBatch(
                organization_id=self.organization_id,
                facility_id=self.facility_id,
                period_start=self.period_start,
                period_end=self.period_end,
                inventory_standard=self.inventory_standard or "org_basic_v1",
                activity_items=self.activity_items,
                legacy_mode=False,
            )

        return CarbonActivityBatch(
            organization_id=self.organization_id,
            facility_id=self.facility_id,
            period_start=self.period_start,
            period_end=self.period_end,
            inventory_standard=self.inventory_standard or "org_basic_v1",
            legacy_mode=True,
            activity_items=[
                CarbonActivityItem(
                    scope="scope2",
                    activity_category="purchased_electricity",
                    activity_name="electricity",
                    activity_value=self.electricity_kwh,
                    activity_unit="kWh",
                    region="CN",
                    factor_preference="official_latest",
                ),
                CarbonActivityItem(
                    scope="scope1",
                    activity_category="stationary_combustion",
                    activity_name="natural_gas",
                    activity_value=self.natural_gas_m3,
                    activity_unit="m3",
                    factor_preference="demo_allowed",
                ),
                CarbonActivityItem(
                    scope="scope1",
                    activity_category="stationary_combustion",
                    activity_name="diesel",
                    activity_value=self.diesel_l,
                    activity_unit="L",
                    factor_preference="demo_allowed",
                ),
            ],
        )


class CarbonBreakdownItem(BaseModel):
    item: str
    scope: str | None = None
    activity_category: str | None = None
    activity_name: str | None = None
    activity_value: float
    activity_unit: str
    normalized_activity_value: float | None = None
    normalized_activity_unit: str | None = None
    factor_value: float
    factor_unit: str
    emission_kgco2e: float
    factor_id: str


class CarbonCitation(BaseModel):
    factor_id: str
    source: str
    source_url: str | None = None


class CarbonFactorSnapshot(BaseModel):
    factor_id: str
    factor_version: str
    source_type: str
    source_name: str
    source_url: str | None = None
    scope: str
    activity_category: str
    activity_name: str
    region: str | None = None
    year: int | None = None
    factor_value: float
    factor_unit: str
    activity_unit: str
    result_unit: str
    is_default: bool = False
    is_deprecated: bool = False
    notes: str | None = None


class CarbonUnitConversionTrace(BaseModel):
    activity_name: str
    input_value: float
    input_unit: str
    normalized_value: float
    normalized_unit: str
    conversion_factor: float


class CarbonFormulaTrace(BaseModel):
    activity_name: str
    formula: str
    normalized_activity_value: float
    activity_unit: str
    factor_value: float
    factor_unit: str
    emission_kgco2e: float


class CarbonSourceSummaryItem(BaseModel):
    source_type: str
    source_name: str
    source_url: str | None = None
    factor_count: int


class CalcCarbonResponse(BaseModel):
    status: Literal["ok"]
    trace_id: str
    total_emission_kgco2e: float
    breakdown: list[CarbonBreakdownItem]
    formula_summary: str
    citations: list[CarbonCitation]
    factor_snapshot: list[CarbonFactorSnapshot] = Field(default_factory=list)
    unit_conversion_trace: list[CarbonUnitConversionTrace] = Field(default_factory=list)
    formula_trace: list[CarbonFormulaTrace] = Field(default_factory=list)
    source_summary: list[CarbonSourceSummaryItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CarbonCalculationSummary(BaseModel):
    trace_id: str
    period_label: str | None = None
    total_emission_kgco2e: float
    created_at: datetime


class StoredCarbonCalculation(BaseModel):
    trace_id: str
    session_id: str | None = None
    period_label: str | None = None
    electricity_kwh: float
    natural_gas_m3: float
    diesel_l: float
    total_emission_kgco2e: float
    breakdown: list[CarbonBreakdownItem]
    citations: list[CarbonCitation]
    factor_snapshot: list[CarbonFactorSnapshot] = Field(default_factory=list)
    unit_conversion_trace: list[CarbonUnitConversionTrace] = Field(default_factory=list)
    formula_trace: list[CarbonFormulaTrace] = Field(default_factory=list)
    source_summary: list[CarbonSourceSummaryItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime
