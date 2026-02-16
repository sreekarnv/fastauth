from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from fastauth.api.deps import require_auth, require_role

if TYPE_CHECKING:
    from fastauth.types import UserData


class RoleResponse(BaseModel):
    name: str
    permissions: list[str]


class CreateRoleRequest(BaseModel):
    name: str
    permissions: list[str] = []


class AssignRoleRequest(BaseModel):
    user_id: str
    role_name: str


class PermissionsRequest(BaseModel):
    permissions: list[str]


class MessageResponse(BaseModel):
    message: str


class UserRolesResponse(BaseModel):
    user_id: str
    roles: list[str]
    permissions: list[str]


def _get_role_adapter(request: Request):
    from fastauth.app import FastAuth

    fa: FastAuth = request.app.state.fastauth
    if not hasattr(fa, "role_adapter") or fa.role_adapter is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RBAC is not configured",
        )
    return fa.role_adapter


def create_rbac_router(auth: object) -> APIRouter:
    router = APIRouter(prefix="/roles")

    @router.get("", response_model=list[RoleResponse])
    async def list_roles(
        request: Request,
        _user: UserData = Depends(require_role("admin")),
    ) -> list[RoleResponse]:
        adapter = _get_role_adapter(request)
        roles = await adapter.list_roles()
        return [
            RoleResponse(name=r["name"], permissions=r.get("permissions", []))
            for r in roles
        ]

    @router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
    async def create_role(
        request: Request,
        body: CreateRoleRequest,
        _user: UserData = Depends(require_role("admin")),
    ) -> RoleResponse:
        adapter = _get_role_adapter(request)
        existing = await adapter.get_role(body.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role already exists",
            )
        role = await adapter.create_role(name=body.name, permissions=body.permissions)
        return RoleResponse(name=role["name"], permissions=role.get("permissions", []))

    @router.delete("/{role_name}", response_model=MessageResponse)
    async def delete_role(
        request: Request,
        role_name: str,
        _user: UserData = Depends(require_role("admin")),
    ) -> MessageResponse:
        adapter = _get_role_adapter(request)
        existing = await adapter.get_role(role_name)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )
        await adapter.delete_role(role_name)
        return MessageResponse(message="Role deleted")

    @router.post("/{role_name}/permissions", response_model=MessageResponse)
    async def add_permissions(
        request: Request,
        role_name: str,
        body: PermissionsRequest,
        _user: UserData = Depends(require_role("admin")),
    ) -> MessageResponse:
        adapter = _get_role_adapter(request)
        existing = await adapter.get_role(role_name)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )
        await adapter.add_permissions(role_name, body.permissions)
        return MessageResponse(message="Permissions added")

    @router.delete("/{role_name}/permissions", response_model=MessageResponse)
    async def remove_permissions(
        request: Request,
        role_name: str,
        body: PermissionsRequest,
        _user: UserData = Depends(require_role("admin")),
    ) -> MessageResponse:
        adapter = _get_role_adapter(request)
        existing = await adapter.get_role(role_name)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )
        await adapter.remove_permissions(role_name, body.permissions)
        return MessageResponse(message="Permissions removed")

    @router.post("/assign", response_model=MessageResponse)
    async def assign_role(
        request: Request,
        body: AssignRoleRequest,
        _user: UserData = Depends(require_role("admin")),
    ) -> MessageResponse:
        adapter = _get_role_adapter(request)
        await adapter.assign_role(body.user_id, body.role_name)
        return MessageResponse(message="Role assigned")

    @router.post("/revoke", response_model=MessageResponse)
    async def revoke_role(
        request: Request,
        body: AssignRoleRequest,
        _user: UserData = Depends(require_role("admin")),
    ) -> MessageResponse:
        adapter = _get_role_adapter(request)
        await adapter.revoke_role(body.user_id, body.role_name)
        return MessageResponse(message="Role revoked")

    @router.get("/user/{user_id}", response_model=UserRolesResponse)
    async def get_user_roles(
        request: Request,
        user_id: str,
        _user: UserData = Depends(require_role("admin")),
    ) -> UserRolesResponse:
        adapter = _get_role_adapter(request)
        roles = await adapter.get_user_roles(user_id)
        permissions = await adapter.get_user_permissions(user_id)
        return UserRolesResponse(
            user_id=user_id, roles=roles, permissions=list(permissions)
        )

    @router.get("/me", response_model=UserRolesResponse)
    async def get_my_roles(
        request: Request,
        user: UserData = Depends(require_auth),
    ) -> UserRolesResponse:
        adapter = _get_role_adapter(request)
        roles = await adapter.get_user_roles(user["id"])
        permissions = await adapter.get_user_permissions(user["id"])
        return UserRolesResponse(
            user_id=user["id"], roles=roles, permissions=list(permissions)
        )

    return router
