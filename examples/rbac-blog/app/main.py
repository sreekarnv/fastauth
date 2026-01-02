"""RBAC Blog Example - FastAPI Application.

This example demonstrates:
- Role-Based Access Control (RBAC)
- Three roles: Admin, Editor, Viewer
- Four permissions: create_post, edit_post, delete_post, publish_post
- Protected routes based on roles and permissions
- Blog post management with different access levels
"""

import pathlib
import uuid
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from fastauth import Settings as FastAuthSettings
from fastauth.adapters.sqlalchemy import SQLAlchemyRoleAdapter, SQLAlchemyUserAdapter
from fastauth.adapters.sqlalchemy.models import User
from fastauth.api import dependencies
from fastauth.api.dependencies import get_current_user, require_permission, require_role
from fastauth.core.roles import check_permission, get_user_permissions, get_user_roles
from fastauth.core.users import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    authenticate_user,
    create_user,
)
from fastauth.security.jwt import create_access_token

from .database import create_db_and_tables, get_session
from .models import Post, PostCreate, PostPublish, PostResponse, PostUpdate
from .settings import settings as app_settings

BASE_DIR = pathlib.Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(
    title="FastAuth RBAC Blog Example",
    description="Demonstrates Role-Based Access Control with a blog application",
    version="0.2.0",
)

app.dependency_overrides[dependencies.get_session] = get_session

fastauth_settings = FastAuthSettings(
    jwt_secret_key=app_settings.jwt_secret_key,
    jwt_algorithm=app_settings.jwt_algorithm,
    access_token_expire_minutes=app_settings.access_token_expire_minutes,
    require_email_verification=app_settings.require_email_verification,
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/register")
def register(
    email: str,
    password: str,
    session: Session = Depends(get_session),
):
    """Register a new user.

    New users are automatically assigned the 'viewer' role.
    Use the seed script to assign other roles.
    """
    user_adapter = SQLAlchemyUserAdapter(session)

    try:
        user = create_user(
            users=user_adapter,
            email=email,
            password=password,
        )

        role_adapter = SQLAlchemyRoleAdapter(session)
        viewer_role = role_adapter.get_role_by_name("viewer")
        if viewer_role:
            role_adapter.assign_role_to_user(user_id=user.id, role_id=viewer_role.id)
            session.commit()

        access_token = create_access_token(subject=str(user.id))

        return {
            "message": "User registered successfully",
            "access_token": access_token,
            "user": {"id": str(user.id), "email": user.email},
        }
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/login")
def login_user(
    email: str,
    password: str,
    session: Session = Depends(get_session),
):
    """Login and receive access token."""
    user_adapter = SQLAlchemyUserAdapter(session)

    try:
        user = authenticate_user(
            users=user_adapter,
            email=email,
            password=password,
        )

        access_token = create_access_token(subject=str(user.id))

        role_adapter = SQLAlchemyRoleAdapter(session)
        user_roles = get_user_roles(roles=role_adapter, user_id=user.id)
        user_permissions = get_user_permissions(roles=role_adapter, user_id=user.id)

        return {
            "access_token": access_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "roles": [role.name for role in user_roles],
                "permissions": [perm.name for perm in user_permissions],
            },
        }
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/me")
def get_current_user_info(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get current user information with roles and permissions."""
    role_adapter = SQLAlchemyRoleAdapter(session)
    user_roles = get_user_roles(roles=role_adapter, user_id=current_user.id)
    user_permissions = get_user_permissions(roles=role_adapter, user_id=current_user.id)

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "roles": [role.name for role in user_roles],
        "permissions": [perm.name for perm in user_permissions],
    }


# Blog Post Endpoints (RBAC Protected)
@app.get("/posts", response_model=List[PostResponse])
def list_posts(
    published_only: bool = True,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List blog posts.

    - All authenticated users can see published posts
    - Users with edit_post permission can see all posts (including drafts)
    """
    role_adapter = SQLAlchemyRoleAdapter(session)
    can_edit = check_permission(
        roles=role_adapter,
        user_id=current_user.id,
        permission_name="edit_post",
    )

    if can_edit:
        statement = select(Post)
    else:
        statement = select(Post).where(Post.is_published == published_only)

    posts = session.exec(statement).all()
    return posts


@app.post(
    "/posts",
    response_model=PostResponse,
    dependencies=[Depends(require_permission("create_post"))],
)
def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a new blog post.

    Requires: create_post permission
    Available to: Editors and Admins
    """
    post = Post(
        title=post_data.title,
        content=post_data.content,
        author_id=current_user.id,
    )

    session.add(post)
    session.commit()
    session.refresh(post)

    return post


@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post(
    post_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a single blog post by ID.

    - All users can view published posts
    - Only users with edit_post permission can view drafts
    """
    statement = select(Post).where(Post.id == post_id)
    post = session.exec(statement).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not post.is_published:
        role_adapter = SQLAlchemyRoleAdapter(session)
        can_edit = check_permission(
            roles=role_adapter,
            user_id=current_user.id,
            permission_name="edit_post",
        )
        if not can_edit:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to view draft posts",
            )

    return post


@app.patch(
    "/posts/{post_id}",
    response_model=PostResponse,
    dependencies=[Depends(require_permission("edit_post"))],
)
def update_post(
    post_id: uuid.UUID,
    post_data: PostUpdate,
    session: Session = Depends(get_session),
):
    """Update a blog post.

    Requires: edit_post permission
    Available to: Editors and Admins
    """
    statement = select(Post).where(Post.id == post_id)
    post = session.exec(statement).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post_data.title is not None:
        post.title = post_data.title
    if post_data.content is not None:
        post.content = post_data.content

    from datetime import UTC, datetime

    post.updated_at = datetime.now(UTC)

    session.add(post)
    session.commit()
    session.refresh(post)

    return post


@app.post(
    "/posts/{post_id}/publish",
    response_model=PostResponse,
    dependencies=[Depends(require_permission("publish_post"))],
)
def publish_post(
    post_id: uuid.UUID,
    publish_data: PostPublish,
    session: Session = Depends(get_session),
):
    """Publish or unpublish a blog post.

    Requires: publish_post permission
    Available to: Admins only
    """
    statement = select(Post).where(Post.id == post_id)
    post = session.exec(statement).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.is_published = publish_data.is_published

    from datetime import UTC, datetime

    post.updated_at = datetime.now(UTC)

    session.add(post)
    session.commit()
    session.refresh(post)

    return post


@app.delete(
    "/posts/{post_id}",
    dependencies=[Depends(require_permission("delete_post"))],
)
def delete_post(
    post_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    """Delete a blog post.

    Requires: delete_post permission
    Available to: Admins only
    """
    statement = select(Post).where(Post.id == post_id)
    post = session.exec(statement).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    session.delete(post)
    session.commit()

    return {"message": "Post deleted successfully"}


# Admin Endpoints
@app.get(
    "/admin/users",
    dependencies=[Depends(require_role("admin"))],
)
def list_users(
    session: Session = Depends(get_session),
):
    """List all users with their roles.

    Requires: admin role
    """
    statement = select(User)
    users = session.exec(statement).all()

    role_adapter = SQLAlchemyRoleAdapter(session)

    result = []
    for user in users:
        user_roles = get_user_roles(roles=role_adapter, user_id=user.id)
        user_permissions = get_user_permissions(roles=role_adapter, user_id=user.id)

        result.append(
            {
                "id": str(user.id),
                "email": user.email,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "roles": [role.name for role in user_roles],
                "permissions": [perm.name for perm in user_permissions],
            }
        )

    return result


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.jinja2", context={})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
