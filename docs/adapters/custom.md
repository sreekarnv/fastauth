# Custom Adapter

You can use any database or ORM by implementing the `UserAdapter` protocol. FastAuth uses structural subtyping (duck typing) — your class just needs the right methods.

## Implementing UserAdapter

```python
from fastauth.types import UserData

class MyUserAdapter:
    """Example adapter backed by a hypothetical async ORM."""

    async def create_user(
        self, email: str, hashed_password: str | None = None, **kwargs
    ) -> UserData:
        record = await db.users.insert(email=email, hashed_password=hashed_password)
        return {"id": str(record.id), "email": record.email, "is_active": True}

    async def get_user_by_id(self, user_id: str) -> UserData | None:
        record = await db.users.find_one(id=user_id)
        return _to_user_data(record) if record else None

    async def get_user_by_email(self, email: str) -> UserData | None:
        record = await db.users.find_one(email=email)
        return _to_user_data(record) if record else None

    async def update_user(self, user_id: str, **kwargs) -> UserData:
        record = await db.users.update(id=user_id, **kwargs)
        return _to_user_data(record)

    async def delete_user(self, user_id: str, soft: bool = True) -> None:
        if soft:
            await db.users.update(id=user_id, is_active=False)
        else:
            await db.users.delete(id=user_id)

    async def get_hashed_password(self, user_id: str) -> str | None:
        record = await db.users.find_one(id=user_id)
        return record.hashed_password if record else None

    async def set_hashed_password(self, user_id: str, hashed_password: str) -> None:
        await db.users.update(id=user_id, hashed_password=hashed_password)
```

## UserData shape

FastAuth expects a `UserData` `TypedDict` from every adapter method. At minimum:

```python
{
    "id": "unique-user-id",       # str, required
    "email": "alice@example.com", # str, required
    "is_active": True,            # bool, required
    # Any extra fields are passed through to hooks and JWT claims
}
```

## The full UserAdapter protocol

```python
class UserAdapter(Protocol):
    async def create_user(self, email, hashed_password=None, **kwargs) -> UserData: ...
    async def get_user_by_id(self, user_id) -> UserData | None: ...
    async def get_user_by_email(self, email) -> UserData | None: ...
    async def update_user(self, user_id, **kwargs) -> UserData: ...
    async def delete_user(self, user_id, soft=True) -> None: ...
    async def get_hashed_password(self, user_id) -> str | None: ...
    async def set_hashed_password(self, user_id, hashed_password) -> None: ...
```

## Other protocols

If you need token storage, OAuth account linking, or RBAC, implement the corresponding protocols:

| Protocol | Required for |
|----------|-------------|
| `TokenAdapter` | Email verification, password reset |
| `OAuthAccountAdapter` | OAuth providers |
| `SessionAdapter` | `session_strategy="database"` |
| `RoleAdapter` | RBAC |

All protocols are defined in `fastauth.core.protocols`. See the [Protocols Reference](../reference/protocols.md) for the full signatures.
