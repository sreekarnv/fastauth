# Event Hooks

Event hooks let you plug custom logic into FastAuth's lifecycle — run side effects, block sign-ins, or add custom claims to JWTs.

## Setup

Subclass `EventHooks` and pass an instance to `FastAuthConfig.hooks`:

```python
from fastauth.core.protocols import EventHooks
from fastauth.types import UserData

class MyHooks(EventHooks):
    async def on_signup(self, user: UserData) -> None:
        await send_welcome_email(user["email"])

    async def on_signin(self, user: UserData, provider: str) -> None:
        await log_signin(user["id"], provider)

config = FastAuthConfig(..., hooks=MyHooks())
```

Only override the methods you need. All default implementations are no-ops (except `allow_signin` which returns `True` by default).

## Available hooks

### Lifecycle events

| Method | When it's called | Can modify return? |
|--------|-----------------|-------------------|
| `on_signup(user)` | After a new user is created | No |
| `on_signin(user, provider)` | After successful sign-in | No |
| `on_signout(user)` | After sign-out | No |
| `on_token_refresh(user)` | After token pair is refreshed | No |
| `on_email_verify(user)` | After email verification | No |
| `on_password_reset(user)` | After password reset | No |
| `on_oauth_link(user, provider)` | After OAuth account linked | No |

### Gate hooks

| Method | Returns | Effect |
|--------|---------|--------|
| `allow_signin(user, provider)` | `bool` | Return `False` → HTTP 403 |

### Mutation hooks

| Method | Returns | Effect |
|--------|---------|--------|
| `modify_jwt(token, user)` | `dict` | Returned dict is signed as the JWT payload |
| `modify_session(session, user)` | `dict` | Returned dict is stored in the session backend |

## Examples

### Block banned users

```python
class MyHooks(EventHooks):
    async def allow_signin(self, user: UserData, provider: str) -> bool:
        return not user.get("is_banned", False)
```

### Add roles to JWT

```python
class MyHooks(EventHooks):
    def __init__(self, role_adapter):
        self.role_adapter = role_adapter

    async def modify_jwt(self, token: dict, user: UserData) -> dict:
        token["roles"] = await self.role_adapter.get_user_roles(user["id"])
        return token
```

### Send a Slack notification on sign-up

```python
import httpx

class MyHooks(EventHooks):
    async def on_signup(self, user: UserData) -> None:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://hooks.slack.com/...",
                json={"text": f"New user: {user['email']}"},
            )
```

### Assign a default subscription tier

```python
class MyHooks(EventHooks):
    async def on_signup(self, user: UserData) -> None:
        await db.subscriptions.create(user_id=user["id"], plan="free")

    async def modify_jwt(self, token: dict, user: UserData) -> dict:
        sub = await db.subscriptions.get(user_id=user["id"])
        token["plan"] = sub.plan if sub else "free"
        return token
```
