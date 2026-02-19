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
    from fastauth.adapters.sqlalchemy.oauth import SQLAlchemyOAuthAccountAdapter
    from fastauth.adapters.sqlalchemy.rbac import SQLAlchemyRoleAdapter
    from fastauth.adapters.sqlalchemy.session import SQLAlchemySessionAdapter
    from fastauth.adapters.sqlalchemy.token import SQLAlchemyTokenAdapter
    from fastauth.adapters.sqlalchemy.user import SQLAlchemyUserAdapter


class SQLAlchemyAdapter:
    """Factory that creates all FastAuth sub-adapters from a single SQLAlchemy engine.

    Pass either a connection URL string or a pre-created
    :class:`sqlalchemy.ext.asyncio.AsyncEngine`.  All sub-adapters share the
    same engine and session factory so you don't have to manage multiple
    connections.

    Supported databases (via async drivers):

    | Database   | Driver       | URL prefix                    |
    |------------|--------------|-------------------------------|
    | SQLite     | aiosqlite    | ``sqlite+aiosqlite:///...``   |
    | PostgreSQL | asyncpg      | ``postgresql+asyncpg://...``  |
    | MySQL      | aiomysql     | ``mysql+aiomysql://...``      |

    Example:
        ```python
        from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter

        # SQLite for local development
        adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

        config = FastAuthConfig(
            secret="...",
            providers=[...],
            adapter=adapter.user,
            token_adapter=adapter.token,
            oauth_adapter=adapter.oauth,
        )

        # Create tables on startup
        @asynccontextmanager
        async def lifespan(app):
            await adapter.create_tables()
            yield
        ```
    """

    def __init__(
        self, engine_url: str | None = None, engine: AsyncEngine | None = None
    ) -> None:
        """Initialize the adapter with a connection URL or an existing engine.

        Args:
            engine_url: SQLAlchemy async connection string.
            engine: A pre-created :class:`~sqlalchemy.ext.asyncio.AsyncEngine`.

        Raises:
            ValueError: If neither *engine_url* nor *engine* is provided.
        """
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
        """Create all FastAuth database tables if they do not already exist.

        Safe to call on every startup — uses ``CREATE TABLE IF NOT EXISTS``
        semantics via SQLAlchemy's ``create_all``.
        """
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """Drop all FastAuth database tables.

        Intended for testing and local teardown only.  **Do not call in
        production** — all user data will be permanently deleted.
        """
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @property
    def user(self) -> SQLAlchemyUserAdapter:
        """
        Return a :class:`~fastauth.adapters.sqlalchemy.user.SQLAlchemyUserAdapter`.
        """
        from fastauth.adapters.sqlalchemy.user import SQLAlchemyUserAdapter

        return SQLAlchemyUserAdapter(self._session_factory)

    @property
    def token(self) -> SQLAlchemyTokenAdapter:
        """
        Return a :class:`~fastauth.adapters.sqlalchemy.token.SQLAlchemyTokenAdapter`.
        """
        from fastauth.adapters.sqlalchemy.token import SQLAlchemyTokenAdapter

        return SQLAlchemyTokenAdapter(self._session_factory)

    @property
    def session(self) -> SQLAlchemySessionAdapter:
        """
        Return a :class:\
        `~fastauth.adapters.sqlalchemy.session.SQLAlchemySessionAdapter`.
        """
        from fastauth.adapters.sqlalchemy.session import SQLAlchemySessionAdapter

        return SQLAlchemySessionAdapter(self._session_factory)

    @property
    def role(self) -> SQLAlchemyRoleAdapter:
        """
        Return a :class:`~fastauth.adapters.sqlalchemy.rbac.SQLAlchemyRoleAdapter`.
        """
        from fastauth.adapters.sqlalchemy.rbac import SQLAlchemyRoleAdapter

        return SQLAlchemyRoleAdapter(self._session_factory)

    @property
    def oauth(self) -> SQLAlchemyOAuthAccountAdapter:
        """
        Returns a :class: \
        `~fastauth.adapters.sqlalchemy.oauth.SQLAlchemyOAuthAccountAdapter`.
        """
        from fastauth.adapters.sqlalchemy.oauth import SQLAlchemyOAuthAccountAdapter

        return SQLAlchemyOAuthAccountAdapter(self._session_factory)
