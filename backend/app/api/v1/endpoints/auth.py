from fastapi import APIRouter, Cookie, Depends, HTTPException, Response

from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    AuthStatusResponse,
    AuthUserEnvelope,
    AuthenticatedUser,
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
)
from app.auth.service import (
    AuthenticationError,
    InactiveUserError,
    UserAlreadyExistsError,
    get_auth_service,
)
from app.core.config import get_settings

router = APIRouter(prefix="/auth")


def _set_auth_cookie(response: Response, *, raw_token: str, max_age_seconds: int) -> None:
    secure = get_settings().app_env == "production"
    response.set_cookie(
        key="carbonrag_session",
        value=raw_token,
        max_age=max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )


@router.post("/register", response_model=AuthUserEnvelope)
def register(payload: RegisterRequest) -> AuthUserEnvelope:
    try:
        user = get_auth_service().register(payload)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return AuthUserEnvelope(user=user)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response) -> LoginResponse:
    try:
        result = get_auth_service().login(payload)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except InactiveUserError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    _set_auth_cookie(
        response,
        raw_token=result.raw_token,
        max_age_seconds=get_auth_service().cookie.max_age_seconds,
    )
    return LoginResponse(user=result.user, must_change_password=result.user.password_must_change)


@router.post("/logout", response_model=AuthStatusResponse)
def logout(
    response: Response,
    current_user: AuthenticatedUser = Depends(get_current_user),
    carbonrag_session: str | None = Cookie(default=None),
) -> AuthStatusResponse:
    del current_user
    get_auth_service().logout(carbonrag_session)
    response.delete_cookie("carbonrag_session", path="/")
    return AuthStatusResponse()


@router.get("/me", response_model=AuthUserEnvelope)
def me(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthUserEnvelope:
    return AuthUserEnvelope(user=current_user)


@router.post("/change-password", response_model=LoginResponse)
def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> LoginResponse:
    service = get_auth_service()
    try:
        service.change_password(
            user_id=current_user.user_id,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
        login_result = service.login({"username": current_user.username, "password": payload.new_password})
    except AuthenticationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except InactiveUserError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    _set_auth_cookie(
        response,
        raw_token=login_result.raw_token,
        max_age_seconds=service.cookie.max_age_seconds,
    )
    return LoginResponse(user=login_result.user, must_change_password=login_result.user.password_must_change)
