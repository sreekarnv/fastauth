# RBAC (Role-Based Access Control)

FastAuth includes a built-in role and permission system. Assign roles to users and protect routes with `require_role` or `require_permission`.

## Concepts

- **Role** — a named group (e.g. `"admin"`, `"editor"`). A user can have multiple roles.
- **Permission** — a string label (e.g. `"reports:read"`, `"users:delete"`). Roles have sets of permissions. A user inherits all permissions from their roles.

## Setup

You need a `RoleAdapter`. With the SQLAlchemy adapter:

```python
auth = FastAuth(config)
auth.role_adapter = adapter.role   # set after creating FastAuth instance
```

## Protecting routes

```python
from fastauth.api.deps import require_auth, require_role, require_permission

# Must be authenticated
@app.get("/dashboard")
async def dashboard(user=Depends(require_auth)):
    return {"user": user}

# Must have the "admin" role
@app.get("/admin")
async def admin(user=Depends(require_role("admin"))):
    return {"message": "admin panel"}

# Must have the "reports:read" permission (in any of their roles)
@app.get("/reports")
async def reports(user=Depends(require_permission("reports:read"))):
    return {"data": []}
```

## Managing roles via API

All RBAC management endpoints require the `admin` role.

| Method | Path | Body | Description |
|--------|------|------|-------------|
| `POST` | `/auth/roles` | `{"name": "...", "permissions": [...]}` | Create a role |
| `GET`  | `/auth/roles` | — | List all roles |
| `DELETE` | `/auth/roles/{name}` | — | Delete a role |
| `POST` | `/auth/roles/{name}/permissions` | `{"permissions": [...]}` | Add permissions to a role |
| `DELETE` | `/auth/roles/{name}/permissions` | `{"permissions": [...]}` | Remove permissions |
| `POST` | `/auth/roles/assign` | `{"user_id": "...", "role_name": "..."}` | Assign role to user |
| `POST` | `/auth/roles/revoke` | `{"user_id": "...", "role_name": "..."}` | Revoke role from user |
| `GET`  | `/auth/roles/user/{user_id}` | — | Get roles and permissions for a user |
| `GET`  | `/auth/roles/me` | — | Get current user's roles and permissions |

### Assigning a role

```bash
curl -X POST http://localhost:8000/auth/roles/assign \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-cuid", "role_name": "editor"}'
```

### Revoking a role

```bash
curl -X POST http://localhost:8000/auth/roles/revoke \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-cuid", "role_name": "editor"}'
```

### Get current user's roles

```bash
curl http://localhost:8000/auth/roles/me \
  -H "Authorization: Bearer <access_token>"
```

Response:

```json
{
  "user_id": "user-cuid",
  "roles": ["editor"],
  "permissions": ["posts:write", "posts:delete"]
}
```

## Seed roles on startup

Define initial roles in `FastAuthConfig.roles` and they will be created on first startup:

```python
config = FastAuthConfig(
    ...,
    roles=[
        {"name": "admin",  "permissions": ["users:read", "users:delete", "reports:read"]},
        {"name": "editor", "permissions": ["posts:write", "posts:delete"]},
        {"name": "viewer", "permissions": ["posts:read", "reports:read"]},
    ],
    default_role="viewer",  # automatically assigned to every new user
)
```

## Embedding roles in the JWT

Use the `modify_jwt` hook to embed the user's roles in the access token so downstream services don't need a database call:

```python
class MyHooks(EventHooks):
    async def modify_jwt(self, token: dict, user: UserData) -> dict:
        if auth.role_adapter:
            token["roles"] = await auth.role_adapter.get_user_roles(user["id"])
        return token
```
