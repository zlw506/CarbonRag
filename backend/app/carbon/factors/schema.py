from pydantic import BaseModel, Field, field_validator

from app.carbon.schemas import CarbonFactorSnapshot


class FactorRecord(BaseModel):
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
    result_unit: str = "kgCO2e"
    valid_from: str | None = None
    valid_to: str | None = None
    is_default: bool = False
    is_deprecated: bool = False
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator(
        "factor_id",
        "factor_version",
        "source_type",
        "source_name",
        "source_url",
        "scope",
        "activity_category",
        "activity_name",
        "region",
        "factor_unit",
        "activity_unit",
        "result_unit",
        "valid_from",
        "valid_to",
        "notes",
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def to_snapshot(self) -> CarbonFactorSnapshot:
        return CarbonFactorSnapshot(
            factor_id=self.factor_id,
            factor_version=self.factor_version,
            source_type=self.source_type,
            source_name=self.source_name,
            source_url=self.source_url,
            scope=self.scope,
            activity_category=self.activity_category,
            activity_name=self.activity_name,
            region=self.region,
            year=self.year,
            factor_value=self.factor_value,
            factor_unit=self.factor_unit,
            activity_unit=self.activity_unit,
            result_unit=self.result_unit,
            is_default=self.is_default,
            is_deprecated=self.is_deprecated,
            notes=self.notes,
        )
