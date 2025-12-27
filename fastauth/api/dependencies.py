import uuid
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from fastauth.adapters.sqlalchemy.models import User
from fastauth.adapters.sqlalchemy.roles import SQLAlchemyRoleAdapter
from fastauth.core.roles import check_permission
from fastauth.security.jwt import TokenError, decode_access_token

security = HTTPBearer()


def get_session():
    raise NotImplementedError(
        "get_session must be overridden by the application. "
        "Use app.dependency_overrides[dependencies.get_session] = your_get_session"
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )

    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


def get_role_adapter(session: Session = Depends(get_session)) -> SQLAlchemyRoleAdapter:
    return SQLAlchemyRoleAdapter(session=session)


def require_role(role_name: str) -> Callable:
    """
    Create a dependency that requires a user to have a specific role.

    Args:
        role_name: Name of the required role

    Returns:
        Dependency function that can be used with FastAPI Depends

    Example:
        @app.get("/admin", dependencies=[Depends(require_role("admin"))])
        def admin_endpoint():
            return {"message": "Admin access granted"}
    """

    def role_checker(
        current_user: User = Depends(get_current_user),
        roles: SQLAlchemyRoleAdapter = Depends(get_role_adapter),
    ):
        user_roles = roles.get_user_roles(user_id=current_user.id)
        user_role_names = [role.name for role in user_roles]

        if role_name not in user_role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required",
            )

        return current_user

    return role_checker


def require_permission(permission_name: str) -> Callable:
    """
    Create a dependency that requires a user to have a specific permission.

    Args:
        permission_name: Name of the required permission

    Returns:
        Dependency function that can be used with FastAPI Depends

    Example:
        @app.delete(
            "/users/{id}",
            dependencies=[Depends(require_permission("delete:users"))]
        )
        def delete_user(id: str):
            return {"message": "User deleted"}
    """

    def permission_checker(
        current_user: User = Depends(get_current_user),
        roles: SQLAlchemyRoleAdapter = Depends(get_role_adapter),
    ):
        has_permission = check_permission(
            roles=roles,
            user_id=current_user.id,
            permission_name=permission_name,
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' required",
            )

        return current_user

    return permission_checker
