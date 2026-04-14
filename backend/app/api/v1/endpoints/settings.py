from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.settings.schemas import (
    ModelDiscoveryResult,
    ProviderConnectionRequest,
    ProviderConnectionResult,
    ProviderListResponse,
    ProviderProfile,
    UpdateUserSettingsRequest,
    UpsertProviderProfileRequest,
    UserSettingsEnvelope,
)
from app.settings.service import SettingsValidationError, get_settings_service

router = APIRouter(prefix="/settings")


@router.get("", response_model=UserSettingsEnvelope)
def get_settings(current_user: AuthenticatedUser = Depends(require_authenticated_user)) -> UserSettingsEnvelope:
    return get_settings_service().get_user_settings(owner_user_id=current_user.user_id)


@router.patch("", response_model=UserSettingsEnvelope)
def patch_settings(
    payload: UpdateUserSettingsRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> UserSettingsEnvelope:
    return get_settings_service().update_user_settings(owner_user_id=current_user.user_id, payload=payload)


@router.get("/providers", response_model=ProviderListResponse)
def list_provider_profiles(current_user: AuthenticatedUser = Depends(require_authenticated_user)) -> ProviderListResponse:
    return get_settings_service().list_provider_profiles(owner_user_id=current_user.user_id)


@router.post("/providers", response_model=ProviderProfile)
def create_provider_profile(
    payload: UpsertProviderProfileRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> ProviderProfile:
    try:
        return get_settings_service().create_provider_profile(owner_user_id=current_user.user_id, payload=payload)
    except SettingsValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/providers/{profile_id}", response_model=ProviderProfile)
def update_provider_profile(
    profile_id: str,
    payload: UpsertProviderProfileRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> ProviderProfile:
    try:
        updated = get_settings_service().update_provider_profile(
            owner_user_id=current_user.user_id,
            profile_id=profile_id,
            payload=payload,
        )
    except SettingsValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="Provider profile not found.")
    return updated


@router.delete("/providers/{profile_id}")
def delete_provider_profile(
    profile_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> dict[str, str]:
    deleted = get_settings_service().delete_provider_profile(owner_user_id=current_user.user_id, profile_id=profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Provider profile not found.")
    return {"status": "ok"}


@router.post("/providers/test", response_model=ProviderConnectionResult)
def test_provider_connection(
    payload: ProviderConnectionRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> ProviderConnectionResult:
    del current_user
    return get_settings_service().test_provider_connection(payload)


@router.post("/providers/discover-models", response_model=ModelDiscoveryResult)
def discover_models(
    payload: ProviderConnectionRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> ModelDiscoveryResult:
    del current_user
    try:
        return get_settings_service().discover_models(payload)
    except SettingsValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
