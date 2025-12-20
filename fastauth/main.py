from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel

from fastauth.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(
    title="FastAuth",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok"}
