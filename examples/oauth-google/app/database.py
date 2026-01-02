"""Database setup for OAuth Google example."""

from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

# SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///./oauth_example.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=True,  # Set to False in production
)


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency to get database session."""
    with Session(engine) as session:
        yield session
