from __future__ import annotations

from typing import Any

from sqlalchemy import delete, insert, select

from fastauth.adapters.sqlalchemy.models import (
    RoleModel,
    role_permissions,
    user_roles,
)
from fastauth.types import RoleData


class SQLAlchemyRoleAdapter:
    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    async def create_role(
        self, name: str, permissions: list[str] | None = None
    ) -> RoleData:
        async with self._session_factory() as session:
            role = RoleModel(name=name)
            session.add(role)
            await session.flush()

            perms = permissions or []
            for perm in perms:
                await session.execute(
                    insert(role_permissions).values(role_name=name, permission=perm)
                )
            await session.commit()
            return {"name": name, "permissions": perms}

    async def get_role(self, name: str) -> RoleData | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(RoleModel).where(RoleModel.name == name)
            )
            role = result.scalar_one_or_none()
            if not role:
                return None

            perm_result = await session.execute(
                select(role_permissions.c.permission).where(
                    role_permissions.c.role_name == name
                )
            )
            perms = [row[0] for row in perm_result.fetchall()]
            return {"name": role.name, "permissions": perms}

    async def list_roles(self) -> list[RoleData]:
        async with self._session_factory() as session:
            result = await session.execute(select(RoleModel))
            roles = result.scalars().all()

            role_list: list[RoleData] = []
            for role in roles:
                perm_result = await session.execute(
                    select(role_permissions.c.permission).where(
                        role_permissions.c.role_name == role.name
                    )
                )
                perms = [row[0] for row in perm_result.fetchall()]
                role_list.append({"name": role.name, "permissions": perms})
            return role_list

    async def delete_role(self, name: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(role_permissions).where(role_permissions.c.role_name == name)
            )
            await session.execute(
                delete(user_roles).where(user_roles.c.role_name == name)
            )
            await session.execute(delete(RoleModel).where(RoleModel.name == name))
            await session.commit()

    async def add_permissions(self, role_name: str, permissions: list[str]) -> None:
        async with self._session_factory() as session:
            for perm in permissions:
                await session.execute(
                    insert(role_permissions).values(
                        role_name=role_name, permission=perm
                    )
                )
            await session.commit()

    async def remove_permissions(self, role_name: str, permissions: list[str]) -> None:
        async with self._session_factory() as session:
            for perm in permissions:
                await session.execute(
                    delete(role_permissions).where(
                        role_permissions.c.role_name == role_name,
                        role_permissions.c.permission == perm,
                    )
                )
            await session.commit()

    async def assign_role(self, user_id: str, role_name: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                insert(user_roles).values(user_id=user_id, role_name=role_name)
            )
            await session.commit()

    async def revoke_role(self, user_id: str, role_name: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(user_roles).where(
                    user_roles.c.user_id == user_id,
                    user_roles.c.role_name == role_name,
                )
            )
            await session.commit()

    async def get_user_roles(self, user_id: str) -> list[str]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(user_roles.c.role_name).where(user_roles.c.user_id == user_id)
            )
            return [row[0] for row in result.fetchall()]

    async def get_user_permissions(self, user_id: str) -> set[str]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(role_permissions.c.permission)
                .select_from(
                    user_roles.join(
                        role_permissions,
                        user_roles.c.role_name == role_permissions.c.role_name,
                    )
                )
                .where(user_roles.c.user_id == user_id)
            )
            return {row[0] for row in result.fetchall()}
