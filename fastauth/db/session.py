from sqlmodel import create_engine, Session, SQLModel
from fastauth.settings import settings

engine = create_engine(
    settings.database_url,
    echo=False,
)

def get_session():
    with Session(engine) as session:
        yield session


def init_db() -> None:
    if settings.auto_create_tables:
        SQLModel.metadata.create_all(engine)
