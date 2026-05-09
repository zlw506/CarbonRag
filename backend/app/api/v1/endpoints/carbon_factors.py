from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import require_admin, require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.carbon_factors.schemas import (
    CarbonFactorCatalogSearchResponse,
    CarbonFactorDetail,
    CarbonFactorFacets,
    CarbonFactorImportJob,
    CarbonFactorImportRequest,
    CarbonFactorSearchResponse,
    CarbonFactorSource,
    CarbonFactorUpdateRequest,
    CarbonStopSyncRequest,
)
from app.carbon_factors.service import get_carbon_factor_database_service

router = APIRouter()


@router.get("/carbon-factors/facets", response_model=CarbonFactorFacets)
def get_carbon_factor_facets(
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> CarbonFactorFacets:
    del current_user
    return get_carbon_factor_database_service().facets()


@router.get("/carbon-factors", response_model=CarbonFactorSearchResponse)
def search_carbon_factors(
    q: str | None = None,
    category: str | None = None,
    industry: str | None = None,
    region: str | None = None,
    year: int | None = None,
    source_type: str | None = None,
    quality: str | None = None,
    unit: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> CarbonFactorSearchResponse:
    del current_user
    return get_carbon_factor_database_service().search(
        q=q,
        category=category,
        industry=industry,
        region=region,
        year=year,
        source_type=source_type,
        quality=quality,
        unit=unit,
        page=page,
        page_size=page_size,
    )


@router.get("/carbon-factor-catalog", response_model=CarbonFactorCatalogSearchResponse)
def search_carbon_factor_catalog(
    q: str | None = None,
    category: str | None = None,
    industry: str | None = None,
    year: int | None = None,
    value_status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> CarbonFactorCatalogSearchResponse:
    del current_user
    return get_carbon_factor_database_service().search_catalog(
        q=q,
        category=category,
        industry=industry,
        year=year,
        value_status=value_status,
        page=page,
        page_size=page_size,
    )


@router.get("/carbon-factors/{factor_id}", response_model=CarbonFactorDetail)
def get_carbon_factor(
    factor_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> CarbonFactorDetail:
    del current_user
    factor = get_carbon_factor_database_service().get_factor(factor_id=factor_id)
    if factor is None:
        raise HTTPException(status_code=404, detail="Carbon factor not found.")
    return factor


@router.get("/carbon-factor-sources", response_model=list[CarbonFactorSource])
def list_carbon_factor_sources(
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> list[CarbonFactorSource]:
    del current_user
    return get_carbon_factor_database_service().list_sources()


@router.get("/admin/carbon-factor-import-jobs", response_model=list[CarbonFactorImportJob])
def list_carbon_factor_import_jobs(
    current_user: AuthenticatedUser = Depends(require_admin),
) -> list[CarbonFactorImportJob]:
    del current_user
    return get_carbon_factor_database_service().list_import_jobs()


@router.post("/admin/carbon-factor-import-jobs", response_model=CarbonFactorImportJob)
def import_carbon_factor_payload(
    payload: CarbonFactorImportRequest,
    current_user: AuthenticatedUser = Depends(require_admin),
) -> CarbonFactorImportJob:
    return get_carbon_factor_database_service().import_payload(owner_user_id=current_user.user_id, payload=payload)


@router.post("/admin/carbon-factor-import-jobs/carbonstop-sync", response_model=CarbonFactorImportJob)
def sync_carbonstop_public_factors(
    payload: CarbonStopSyncRequest | None = None,
    current_user: AuthenticatedUser = Depends(require_admin),
) -> CarbonFactorImportJob:
    service = get_carbon_factor_database_service()
    if payload and payload.use_live_fetch:
        return service.sync_carbonstop_public(owner_user_id=current_user.user_id)
    return service.import_carbonstop_seed(owner_user_id=current_user.user_id)


@router.patch("/admin/carbon-factors/{factor_id}", response_model=CarbonFactorDetail)
def update_carbon_factor(
    factor_id: str,
    payload: CarbonFactorUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_admin),
) -> CarbonFactorDetail:
    del current_user
    factor = get_carbon_factor_database_service().update_factor(
        factor_id=factor_id,
        is_enabled=payload.is_enabled,
        quality=payload.quality,
    )
    if factor is None:
        raise HTTPException(status_code=404, detail="Carbon factor not found.")
    return factor
