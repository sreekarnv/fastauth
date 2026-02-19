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
    auth = request.app.state.fastauth

    token_str = request.cookies.get(auth.config.cookie_name_access)
    if not token_str and credentials:
        token_str = credentials.credentials
    if not token_str:
        return None

    try:
        claims = decode_token(token_str, auth.config, auth.jwks_manager)
        if claims.get("type") != "access":
            return None
        user = await auth.config.adapter.get_user_by_id(claims["sub"])
        return user
    except Exception:
        return None


async def require_auth(
    user=Depends(get_current_user),
) -> UserData:
    """FastAPI dependency that enforces authentication.

    Reads the access token from the ``Authorization: Bearer`` header **or** the
    configured access-token cookie (``FastAuthConfig.cookie_name_access``).
    Returns the current user record on success.

    Example:
        ```python
        from fastapi import Depends
        from fastauth.api.deps import require_auth
        from fastauth.types import UserData

        @app.get("/profile")
        async def profile(user: UserData = Depends(require_auth)):
            return {"email": user["email"]}
        ```

    Raises:
        HTTPException(401): If no valid access token is present or the token
            is expired / malformed.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return user


def require_role(role_name: str) -> Any:
    """Return a FastAPI dependency that enforces a specific RBAC role.

    The requesting user must be authenticated **and** have *role_name* assigned.
    RBAC must be configured — i.e. ``role_adapter`` must be set on the
    :class:`~fastauth.app.FastAuth` instance.

    Args:
        role_name: The role the user must hold (e.g. ``"admin"``).

    Example:
        ```python
        from fastauth.api.deps import require_role

        @app.get("/admin")
        async def admin_area(user: UserData = Depends(require_role("admin"))):
            return {"message": "Welcome, admin"}
        ```

    Raises:
        HTTPException(401): If the user is not authenticated.
        HTTPException(403): If the user does not hold *role_name*.
        HTTPException(500): If RBAC is not configured on the FastAuth instance.
    """

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
    """Return a FastAPI dependency that enforces a specific RBAC permission.

    Checks that the authenticated user holds at least one role that includes
    *permission*. RBAC must be configured on the
    :class:`~fastauth.app.FastAuth` instance.

    Args:
        permission: The permission string to check (e.g. ``"reports:read"``).

    Example:
        ```python
        from fastauth.api.deps import require_permission

        @app.get("/reports")
        async def reports(user: UserData = Depends(require_permission("reports:read"))):
            return {"message": "Here are your reports"}
        ```

    Raises:
        HTTPException(401): If the user is not authenticated.
        HTTPException(403): If the user lacks *permission*.
        HTTPException(500): If RBAC is not configured on the FastAuth instance.
    """

    async def dependency(
        request: Request, user: UserData = Depends(require_auth)
    ) -> UserData:
        fa = request.app.state.fastauth
        if not hasattr(fa, "role_adapter") or fa.role_adapter is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="RBAC is not configured",
            )
        has_perm = await check_user_permission(fa.role_adapter, user["id"], permission)
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency
