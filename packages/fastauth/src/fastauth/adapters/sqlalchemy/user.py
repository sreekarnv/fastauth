from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from cuid2 import cuid_wrapper
from sqlalchemy import select, update

from fastauth.adapters.sqlalchemy.models import UserModel
from fastauth.exceptions import UserAlreadyExistsError, UserNotFoundError
from fastauth.types import UserData

generate_id = cuid_wrapper()


def _to_user_data(user: UserModel) -> UserData:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "image": user.image,
        "email_verified": user.email_verified,
        "is_active": user.is_active,
    }


class SQLAlchemyUserAdapter:
    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    async def create_user(
        self, email: str, hashed_password: str | None = None, **kwargs: Any
    ) -> UserData:
        async with self._session_factory() as session:
            existing = await session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            if existing.scalar_one_or_none():
                raise UserAlreadyExistsError(
                    f"User with email '{email}' already exists"
                )

            now = datetime.now(timezone.utc)
            user = UserModel(
                id=generate_id(),
                email=email,
                hashed_password=hashed_password,
                name=kwargs.get("name"),
                image=kwargs.get("image"),
                email_verified=False,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return _to_user_data(user)

    async def get_user_by_id(self, user_id: str) -> UserData | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one_or_none()
            return _to_user_data(user) if user else None

    async def get_user_by_email(self, email: str) -> UserData | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            user = result.scalar_one_or_none()
            return _to_user_data(user) if user else None

    async def update_user(self, user_id: str, **kwargs: Any) -> UserData:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                raise UserNotFoundError(f"User '{user_id}' not found")

            allowed_fields = {"email", "name", "image", "email_verified", "is_active"}
            update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
            update_data["updated_at"] = datetime.now(timezone.utc)

            if update_data:
                await session.execute(
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(**update_data)
                )
                await session.commit()
                await session.refresh(user)

            return _to_user_data(user)

    async def delete_user(self, user_id: str, soft: bool = True) -> None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                raise UserNotFoundError(f"User '{user_id}' not found")

            if soft:
                now = datetime.now(timezone.utc)
                user.is_active = False
                user.deleted_at = now
                user.updated_at = now
                await session.commit()
            else:
                await session.delete(user)
                await session.commit()

    async def get_hashed_password(self, user_id: str) -> str | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel.hashed_password).where(UserModel.id == user_id)
            )
            return result.scalar_one_or_none()

    async def set_hashed_password(self, user_id: str, hashed_password: str) -> None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                raise UserNotFoundError(f"User '{user_id}' not found")

            user.hashed_password = hashed_password
            user.updated_at = datetime.now(timezone.utc)
            await session.commit()
