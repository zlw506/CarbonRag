from datetime import datetime
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


class CalcCarbonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str | None = None
    period_label: str | None = None
    electricity_kwh: float = Field(default=0, ge=0)
    natural_gas_m3: float = Field(default=0, ge=0)
    diesel_l: float = Field(default=0, ge=0)

    @field_validator("session_id", "period_label")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def require_any_activity(self) -> "CalcCarbonRequest":
        if (
            self.electricity_kwh == 0
            and self.natural_gas_m3 == 0
            and self.diesel_l == 0
        ):
            raise ValueError("At least one activity value must be greater than zero.")
        return self


class CarbonBreakdownItem(BaseModel):
    item: Literal["electricity", "natural_gas", "diesel"]
    activity_value: float
    activity_unit: str
    factor_value: float
    factor_unit: str
    emission_kgco2e: float
    factor_id: str


class CarbonCitation(BaseModel):
    factor_id: str
    source: str
    source_url: str


class CalcCarbonResponse(BaseModel):
    status: Literal["ok"]
    trace_id: str
    total_emission_kgco2e: float
    breakdown: list[CarbonBreakdownItem]
    formula_summary: str
    citations: list[CarbonCitation]


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
    created_at: datetime
