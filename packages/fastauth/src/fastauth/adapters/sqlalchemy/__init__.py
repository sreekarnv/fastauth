from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from fastauth.adapters.sqlalchemy.models import Base

if TYPE_CHECKING:
    from fastauth.adapters.sqlalchemy.rbac import SQLAlchemyRoleAdapter
    from fastauth.adapters.sqlalchemy.session import SQLAlchemySessionAdapter
    from fastauth.adapters.sqlalchemy.token import SQLAlchemyTokenAdapter
    from fastauth.adapters.sqlalchemy.user import SQLAlchemyUserAdapter


class SQLAlchemyAdapter:
    """Factory that provides all sub-adapters from a single engine."""

    def __init__(
        self, engine_url: str | None = None, engine: AsyncEngine | None = None
    ) -> None:
        if engine:
            self._engine = engine
        elif engine_url:
            self._engine = create_async_engine(engine_url)
        else:
            raise ValueError("Provide either engine_url or engine")

        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_tables(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @property
    def user(self) -> SQLAlchemyUserAdapter:
        from fastauth.adapters.sqlalchemy.user import SQLAlchemyUserAdapter

        return SQLAlchemyUserAdapter(self._session_factory)

    @property
    def token(self) -> SQLAlchemyTokenAdapter:
        from fastauth.adapters.sqlalchemy.token import SQLAlchemyTokenAdapter

        return SQLAlchemyTokenAdapter(self._session_factory)

    @property
    def session(self) -> SQLAlchemySessionAdapter:
        from fastauth.adapters.sqlalchemy.session import SQLAlchemySessionAdapter

        return SQLAlchemySessionAdapter(self._session_factory)

    @property
    def role(self) -> SQLAlchemyRoleAdapter:
        from fastauth.adapters.sqlalchemy.rbac import SQLAlchemyRoleAdapter

        return SQLAlchemyRoleAdapter(self._session_factory)
