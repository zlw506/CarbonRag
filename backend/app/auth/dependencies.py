from fastapi import Cookie, Depends, HTTPException

from app.auth.schemas import AuthenticatedUser
from app.auth.service import get_auth_service


def _load_user_from_cookie(carbonrag_session: str | None = Cookie(default=None)) -> AuthenticatedUser | None:
    if not carbonrag_session:
        return None
    return get_auth_service().get_user_from_token(carbonrag_session)


def require_authenticated_user(user: AuthenticatedUser | None = Depends(_load_user_from_cookie)) -> AuthenticatedUser:
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if user.password_must_change:
        raise HTTPException(status_code=403, detail="Password change required.")
    return user


def get_current_user(user: AuthenticatedUser | None = Depends(_load_user_from_cookie)) -> AuthenticatedUser:
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


def require_admin(user: AuthenticatedUser = Depends(require_authenticated_user)) -> AuthenticatedUser:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user
