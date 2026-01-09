"""Database configuration for the example app."""

from sqlalchemy.pool import StaticPool
from sqlmodel import Session as SQLModelSession
from sqlmodel import SQLModel, create_engine

from fastauth.adapters.sqlalchemy.models import *  # noqa: F403

from .settings import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with SQLModelSession(engine) as session:
        yield session
