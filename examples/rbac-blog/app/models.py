"""Blog post models."""

import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Post(SQLModel, table=True):
    """Blog post model."""

    __tablename__ = "posts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=200)
    content: str
    author_id: uuid.UUID = Field(foreign_key="users.id")
    is_published: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PostCreate(SQLModel):
    """Schema for creating a blog post."""

    title: str
    content: str


class PostUpdate(SQLModel):
    """Schema for updating a blog post."""

    title: Optional[str] = None
    content: Optional[str] = None


class PostPublish(SQLModel):
    """Schema for publishing a blog post."""

    is_published: bool


class PostResponse(SQLModel):
    """Schema for blog post response."""

    id: uuid.UUID
    title: str
    content: str
    author_id: uuid.UUID
    is_published: bool
    created_at: datetime
    updated_at: datetime
