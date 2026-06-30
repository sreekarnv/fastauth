# Custom Adapter

You can use any database or ORM by implementing the `UserAdapter` protocol. FastAuth uses structural subtyping (duck typing) — your class just needs the right methods.

## Email identity and normalization

FastAuth treats emails as case-insensitive and trims surrounding whitespace. The canonical form is `email.strip().casefold()` — for example `"  Alice@Example.COM  "` becomes `"alice@example.com"`. Built-in adapters (`MemoryUserAdapter`, `SQLAlchemyUserAdapter`) normalize every email on create, lookup, and update, and index the underlying store by the normalized form.

Custom adapters **must enforce the same contract**:

1. Normalize every incoming `email` (`email.strip().casefold()`) before you write it to your store and before you look it up.
2. Enforce uniqueness by the normalized form, not the raw input. Otherwise `Alice@example.com` and `alice@example.com` would be two separate accounts.
3. Return the normalized form in the `email` field of the `UserData` you return, so downstream code (JWT claims, hooks, `/auth/me`) sees a consistent identity.

Use the shared helper to avoid drift:

```python
from fastauth.core.identity import normalize_email

normalized = normalize_email("Alice@Example.COM")  # "alice@example.com"
```

This keeps cross-feature identity consistent — credentials login, OAuth email linking, magic-link auto-registration, and lockout tracking all rely on the same normalized form.

## Implementing UserAdapter

```python
from fastauth.core.identity import normalize_email
from fastauth.types import UserData

class MyUserAdapter:
    """Example adapter backed by a hypothetical async ORM."""

    async def create_user(
        self, email: str, hashed_password: str | None = None, **kwargs
    ) -> UserData:
        normalized = normalize_email(email)
        record = await db.users.insert(email=normalized, hashed_password=hashed_password)
        return {"id": str(record.id), "email": normalized, "is_active": True}

    async def get_user_by_id(self, user_id: str) -> UserData | None:
        record = await db.users.find_one(id=user_id)
        return _to_user_data(record) if record else None

    async def get_user_by_email(self, email: str) -> UserData | None:
        record = await db.users.find_one(email=normalize_email(email))
        return _to_user_data(record) if record else None

    async def update_user(self, user_id: str, **kwargs) -> UserData:
        if "email" in kwargs and isinstance(kwargs["email"], str):
            kwargs["email"] = normalize_email(kwargs["email"])
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

If you need token storage, OAuth account linking, user-session management, or RBAC, implement the corresponding protocols:

| Protocol | Required for |
|----------|-------------|
| `TokenAdapter` | Email verification, password reset |
| `OAuthAccountAdapter` | OAuth providers |
| `SessionAdapter` | `/auth/sessions` user-session listing and revocation |
| `RoleAdapter` | RBAC |

All protocols are defined in `fastauth.core.protocols`. See the [Protocols Reference](../reference/protocols.md) for the full signatures.
