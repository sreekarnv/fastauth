# Adapters

An **adapter** is the piece of FastAuth that talks to your database. Providers authenticate users; adapters persist and retrieve them.

## The adapter pattern

FastAuth defines adapters as Python `Protocol` classes. This means you never inherit from a FastAuth base class. You implement the required methods on your own class and pass it in — if the methods match the protocol, it works.

This design lets FastAuth support any database engine without pulling in unwanted dependencies.

## Available adapters

### SQLAlchemyAdapter

The recommended choice for most applications. Supports any SQLAlchemy-compatible async database:

- **SQLite** (development) via `aiosqlite`
- **PostgreSQL** (production) via `asyncpg`
- **MySQL** via `aiomysql`

`SQLAlchemyAdapter` is a factory — one object gives you all the sub-adapters:

```python
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter

adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

config = FastAuthConfig(
    adapter=adapter.user,        # UserAdapter
    token_adapter=adapter.token, # TokenAdapter (email/password reset tokens)
    oauth_adapter=adapter.oauth, # OAuthAccountAdapter (linked social accounts)
    # role_adapter set separately on auth.role_adapter
)
```

See [SQLAlchemy Adapter](../adapters/sqlalchemy.md) for the full guide.

### MemoryAdapter

An in-memory adapter for testing. No database required.

```python
from fastauth.adapters.memory import MemoryUserAdapter

config = FastAuthConfig(
    adapter=MemoryUserAdapter(),
    ...
)
```

See [Memory Adapter](../adapters/memory.md).

## Sub-adapter protocols

FastAuth splits storage responsibilities across several protocols:

| Protocol | Purpose | Config field |
|----------|---------|--------------|
| `UserAdapter` | Create, read, update, delete users | `adapter` |
| `TokenAdapter` | Persist one-time verification/reset tokens | `token_adapter` |
| `SessionAdapter` | Store server-side sessions | used internally |
| `OAuthAccountAdapter` | Link OAuth provider accounts to users | `oauth_adapter` |
| `RoleAdapter` | Manage roles and permissions | `auth.role_adapter` |

You only need to configure the protocols relevant to your feature set. Email verification requires a `TokenAdapter`; OAuth requires an `OAuthAccountAdapter`; RBAC requires a `RoleAdapter`.

## Custom adapters

If you use a database not supported by SQLAlchemy, or you have existing models, you can implement the protocol directly. See [Custom Adapter](../adapters/custom.md).
