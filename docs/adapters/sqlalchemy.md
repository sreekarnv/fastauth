# SQLAlchemy Adapter

The SQLAlchemy adapter is the recommended storage backend for production applications. It supports any SQLAlchemy-compatible async database.

## Supported databases

| Database | Driver | Connection URL prefix |
|----------|--------|-----------------------|
| SQLite | `aiosqlite` | `sqlite+aiosqlite:///path/to/db.sqlite` |
| PostgreSQL | `asyncpg` | `postgresql+asyncpg://user:pass@host/db` |
| MySQL | `aiomysql` | `mysql+aiomysql://user:pass@host/db` |

## Install

=== "SQLite (dev)"

    ```bash
    pip install "sreekarnv-fastauth[standard]"
    # aiosqlite is included in the sqlalchemy extra
    ```

=== "PostgreSQL"

    ```bash
    pip install "sreekarnv-fastauth[standard,postgresql]"
    ```

## Setup

```python
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter

# SQLite
adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

# PostgreSQL
adapter = SQLAlchemyAdapter(
    engine_url="postgresql+asyncpg://user:pass@localhost/mydb"
)
```

### Using an existing engine

If you already manage an `AsyncEngine` elsewhere:

```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine("postgresql+asyncpg://...")
adapter = SQLAlchemyAdapter(engine=engine)
```

## Create tables

Call `create_tables()` in your app's lifespan handler:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    yield

app = FastAPI(lifespan=lifespan)
```

This is safe to call on every startup — it uses `CREATE TABLE IF NOT EXISTS` semantics.

## Sub-adapters

`SQLAlchemyAdapter` is a factory. Use its properties to get the individual adapter implementations:

```python
config = FastAuthConfig(
    adapter=adapter.user,        # required: UserAdapter
    token_adapter=adapter.token, # needed for email verification / password reset
    oauth_adapter=adapter.oauth, # needed for OAuth providers
    ...
)

# RBAC adapter (set directly on the FastAuth instance)
auth = FastAuth(config)
auth.role_adapter = adapter.role
```

| Property | Protocol | When you need it |
|----------|----------|-----------------|
| `adapter.user` | `UserAdapter` | Always |
| `adapter.token` | `TokenAdapter` | Email verification, password reset |
| `adapter.session` | `SessionAdapter` | `session_strategy="database"` |
| `adapter.role` | `RoleAdapter` | RBAC |
| `adapter.oauth` | `OAuthAccountAdapter` | OAuth providers |

## Migrations

FastAuth manages its own schema. For production, use Alembic instead of `create_tables()`:

```bash
pip install alembic
alembic init alembic
```

Import `Base` from FastAuth in your Alembic `env.py`:

```python
from fastauth.adapters.sqlalchemy.models import Base
target_metadata = Base.metadata
```
