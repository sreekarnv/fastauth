from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastauth.api.auth import router as auth_router
from fastauth.api.sessions import router as sessions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="FastAuth",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(sessions_router)


@app.get("/health")
def health():
    return {"status": "ok"}
