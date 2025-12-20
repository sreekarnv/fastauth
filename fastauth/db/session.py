from sqlmodel import create_engine, Session
from fastauth.settings import settings

engine = create_engine(
    settings.database_url,
    echo=False,
)


def get_session():
    with Session(engine) as session:
        yield session
