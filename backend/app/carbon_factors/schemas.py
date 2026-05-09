from pydantic import BaseModel, Field


class CarbonFactorSource(BaseModel):
    source_id: str
    title: str
    publisher: str
    source_url: str | None = None
    license: str | None = None
    published_year: int | None = None
    source_type: str
    created_at: str
    updated_at: str


class CarbonFactorSummary(BaseModel):
    factor_id: str
    name: str
    category: str
    industry: str | None = None
    scope: str
    region: str | None = None
    region_code: str | None = None
    region_name: str | None = None
    year: int | None = None
    factor_value: float
    factor_unit: str
    activity_unit: str
    co2e_unit: str = "kgCO2e"
    quality: str
    version: str
    source: CarbonFactorSource | None = None
    tags: list[str] = Field(default_factory=list)


class CarbonFactorDetail(CarbonFactorSummary):
    aliases: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    is_enabled: bool = True
    created_at: str
    updated_at: str


class CarbonFactorSearchResponse(BaseModel):
    items: list[CarbonFactorSummary]
    total: int
    page: int
    page_size: int


class CarbonFactorCatalogEntry(BaseModel):
    entry_id: str
    name: str
    category: str
    industry: str | None = None
    region: str | None = None
    year: int | None = None
    factor_unit: str | None = None
    activity_unit: str | None = None
    value_status: str
    raw_value: str | None = None
    factor_value: float | None = None
    is_calculation_ready: bool
    source_title: str | None = None
    publisher: str | None = None
    source_url: str | None = None
    metadata: dict = Field(default_factory=dict)


class CarbonFactorCatalogSearchResponse(BaseModel):
    items: list[CarbonFactorCatalogEntry]
    total: int
    page: int
    page_size: int


class CarbonFactorFacets(BaseModel):
    categories: list[str]
    industries: list[str]
    regions: list[str]
    years: list[int]
    source_types: list[str]
    qualities: list[str]
    category_tree: list[dict] = Field(default_factory=list)


class CarbonFactorImportSource(BaseModel):
    title: str
    publisher: str
    source_url: str | None = None
    license: str | None = None
    published_year: int | None = None
    source_type: str = "internal_curated"


class CarbonFactorImportRequest(BaseModel):
    source: CarbonFactorImportSource
    factor_records: list[dict]
    source_kind: str = "json"


class CarbonFactorImportJob(BaseModel):
    job_id: str
    source_kind: str
    status: str
    summary: dict = Field(default_factory=dict)
    error_message: str | None = None
    created_at: str
    updated_at: str


class CarbonFactorUpdateRequest(BaseModel):
    is_enabled: bool | None = None
    quality: str | None = None


class CarbonStopSyncRequest(BaseModel):
    use_live_fetch: bool = False
