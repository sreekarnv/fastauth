from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fastauth.core.rbac import check_user_permission, check_user_role
from fastauth.core.tokens import decode_token
from fastauth.types import UserData

security = HTTPBearer(auto_error=False)


async def get_fastauth(request: Request):
    return request.app.state.fastauth


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if not credentials:
        return None
    auth = request.app.state.fastauth
    try:
        claims = decode_token(credentials.credentials, auth.config)
        if claims.get("type") != "access":
            return None
        user = await auth.config.adapter.get_user_by_id(claims["sub"])
        return user
    except Exception:
        return None


async def require_auth(
    user=Depends(get_current_user),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return user


def require_role(role_name: str) -> Any:
    async def dependency(
        request: Request, user: UserData = Depends(require_auth)
    ) -> UserData:
        fa = request.app.state.fastauth
        if not hasattr(fa, "role_adapter") or fa.role_adapter is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="RBAC is not configured",
            )
        has_role = await check_user_role(fa.role_adapter, user["id"], role_name)
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return user

    return dependency


def require_permission(permission: str) -> Any:
    async def dependency(
        request: Request, user: UserData = Depends(require_auth)
    ) -> UserData:
        fa = request.app.state.fastauth
        if not hasattr(fa, "role_adapter") or fa.role_adapter is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="RBAC is not configured",
            )
        has_perm = await check_user_permission(
            fa.role_adapter, user["id"], permission
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency
