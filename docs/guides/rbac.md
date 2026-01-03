# Role-Based Access Control (RBAC)

Implement fine-grained access control with roles and permissions.

## Overview

FastAuth provides built-in RBAC with:
- **Roles**: Groups of permissions (e.g., "admin", "editor", "viewer")
- **Permissions**: Specific actions (e.g., "create:post", "delete:user")
- **User-Role Assignment**: Assign roles to users
- **Role-Permission Assignment**: Assign permissions to roles

## Setup

### Step 1: Create Permissions

```python
from sqlmodel import Session
from fastauth.adapters.sqlalchemy import SQLAlchemyRoleAdapter
from fastauth.core.roles import create_permission

with Session(engine) as session:
    role_adapter = SQLAlchemyRoleAdapter(session)

    create_permission(
        roles=role_adapter,
        name="create_post",
        description="Create new blog posts",
    )

    create_permission(
        roles=role_adapter,
        name="delete_post",
        description="Delete blog posts",
    )

    session.commit()
```

### Step 2: Create Roles

```python
from fastauth.core.roles import create_role

with Session(engine) as session:
    role_adapter = SQLAlchemyRoleAdapter(session)

    create_role(
        roles=role_adapter,
        name="editor",
        description="Can create and edit posts",
    )

    create_role(
        roles=role_adapter,
        name="admin",
        description="Full access to all features",
    )

    session.commit()
```

### Step 3: Assign Permissions to Roles

```python
from fastauth.core.roles import assign_permission_to_role

with Session(engine) as session:
    role_adapter = SQLAlchemyRoleAdapter(session)

    # Editor can create and edit
    assign_permission_to_role(
        roles=role_adapter,
        role_name="editor",
        permission_name="create_post",
    )

    # Admin can create, edit, and delete
    assign_permission_to_role(
        roles=role_adapter,
        role_name="admin",
        permission_name="create_post",
    )

    assign_permission_to_role(
        roles=role_adapter,
        role_name="admin",
        permission_name="delete_post",
    )

    session.commit()
```

### Step 4: Assign Roles to Users

```python
from fastauth.core.roles import assign_role

with Session(engine) as session:
    role_adapter = SQLAlchemyRoleAdapter(session)

    assign_role(
        roles=role_adapter,
        user_id=user.id,
        role_name="editor",
    )

    session.commit()
```

## Protecting Routes

### Require Specific Role

```python
from fastapi import Depends
from fastauth.api.dependencies import require_role

@app.get("/admin/dashboard", dependencies=[Depends(require_role("admin"))])
def admin_dashboard():
    return {"message": "Admin dashboard"}
```

### Require Specific Permission

```python
from fastauth.api.dependencies import require_permission

@app.delete("/posts/{post_id}", dependencies=[Depends(require_permission("delete_post"))])
def delete_post(post_id: str):
    return {"message": f"Post {post_id} deleted"}
```

### Multiple Permissions (AND)

```python
from fastapi import Depends

@app.post(
    "/posts/{post_id}/publish",
    dependencies=[
        Depends(require_permission("edit_post")),
        Depends(require_permission("publish_post")),
    ],
)
def publish_post(post_id: str):
    return {"message": f"Post {post_id} published"}
```

### Check Permissions Manually

```python
from fastapi import Depends, HTTPException
from fastauth.api.dependencies import get_current_user
from fastauth.core.roles import check_permission
from fastauth.adapters.sqlalchemy import SQLAlchemyRoleAdapter

@app.post("/posts")
def create_post(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    role_adapter = SQLAlchemyRoleAdapter(session)

    can_create = check_permission(
        roles=role_adapter,
        user_id=current_user.id,
        permission_name="create_post",
    )

    if not can_create:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to create posts",
        )

    # Create post logic
    return {"message": "Post created"}
```

## Checking User Roles and Permissions

### Get User Roles

```python
from fastauth.core.roles import get_user_roles

with Session(engine) as session:
    role_adapter = SQLAlchemyRoleAdapter(session)

    user_roles = get_user_roles(
        roles=role_adapter,
        user_id=user.id,
    )

    role_names = [role.name for role in user_roles]
    # ['editor', 'viewer']
```

### Get User Permissions

```python
from fastauth.core.roles import get_user_permissions

with Session(engine) as session:
    role_adapter = SQLAlchemyRoleAdapter(session)

    user_permissions = get_user_permissions(
        roles=role_adapter,
        user_id=user.id,
    )

    permission_names = [perm.name for perm in user_permissions]
    # ['create_post', 'edit_post']
```

## Removing Roles and Permissions

### Remove Role from User

```python
from fastauth.core.roles import unassign_role

with Session(engine) as session:
    role_adapter = SQLAlchemyRoleAdapter(session)

    unassign_role(
        roles=role_adapter,
        user_id=user.id,
        role_name="editor",
    )

    session.commit()
```

### Remove Permission from Role

```python
from fastauth.core.roles import unassign_permission_from_role

with Session(engine) as session:
    role_adapter = SQLAlchemyRoleAdapter(session)

    unassign_permission_from_role(
        roles=role_adapter,
        role_name="editor",
        permission_name="delete_post",
    )

    session.commit()
```

## Example: Blog with RBAC

Complete example with three roles:

```python
from fastapi import FastAPI, Depends
from sqlmodel import Session
from fastauth.adapters.sqlalchemy import SQLAlchemyRoleAdapter
from fastauth.api.dependencies import require_permission, get_current_user
from fastauth.core.roles import (
    create_permission,
    create_role,
    assign_permission_to_role,
)

app = FastAPI()

@app.on_event("startup")
def setup_rbac():
    with Session(engine) as session:
        role_adapter = SQLAlchemyRoleAdapter(session)

        # Create permissions
        permissions = [
            ("create_post", "Create posts"),
            ("edit_post", "Edit posts"),
            ("publish_post", "Publish posts"),
            ("delete_post", "Delete posts"),
        ]

        for name, desc in permissions:
            create_permission(roles=role_adapter, name=name, description=desc)

        # Create roles
        create_role(roles=role_adapter, name="viewer", description="View only")
        create_role(roles=role_adapter, name="editor", description="Create and edit")
        create_role(roles=role_adapter, name="admin", description="Full access")

        # Assign permissions to roles
        # Editor: create and edit
        assign_permission_to_role(role_adapter, "editor", "create_post")
        assign_permission_to_role(role_adapter, "editor", "edit_post")

        # Admin: all permissions
        for perm in ["create_post", "edit_post", "publish_post", "delete_post"]:
            assign_permission_to_role(role_adapter, "admin", perm)

        session.commit()

# Routes
@app.get("/posts")
def list_posts(current_user: User = Depends(get_current_user)):
    # All authenticated users can view
    return {"posts": [...]}

@app.post("/posts", dependencies=[Depends(require_permission("create_post"))])
def create_post():
    # Only editors and admins
    return {"message": "Post created"}

@app.delete("/posts/{id}", dependencies=[Depends(require_permission("delete_post"))])
def delete_post(id: str):
    # Only admins
    return {"message": f"Post {id} deleted"}
```

## Best Practices

### Permission Naming

Use consistent naming conventions:

```python
# Resource-based
"create:post"
"read:post"
"update:post"
"delete:post"

# Or action-based
"post.create"
"post.read"
"post.update"
"post.delete"
```

### Default Roles

Assign a default role to new users:

```python
from fastauth.core.users import create_user
from fastauth.core.roles import assign_role

user = create_user(users=user_adapter, email=email, password=password)

# Assign default "viewer" role
assign_role(roles=role_adapter, user_id=user.id, role_name="viewer")
session.commit()
```

### Hierarchical Roles

Implement role hierarchy by assigning permissions:

```python
# Basic role
assign_permission_to_role(role_adapter, "user", "read:own_profile")

# Moderator inherits user permissions + more
assign_permission_to_role(role_adapter, "moderator", "read:own_profile")
assign_permission_to_role(role_adapter, "moderator", "moderate:posts")

# Admin gets all permissions
assign_permission_to_role(role_adapter, "admin", "read:own_profile")
assign_permission_to_role(role_adapter, "admin", "moderate:posts")
assign_permission_to_role(role_adapter, "admin", "delete:users")
```

## Complete Example

See the [RBAC Blog Example](../../examples/rbac-blog/) for a full working implementation with:
- Three roles (viewer, editor, admin)
- Four permissions (create, edit, publish, delete)
- Protected routes
- Seed script for setup

## Next Steps

- **[Authentication](authentication.md)** - User registration and login
- **[Protecting Routes](protecting-routes.md)** - Secure endpoints
- **[RBAC Blog Example](../../examples/rbac-blog/)** - Complete working example
