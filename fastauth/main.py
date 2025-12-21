from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastauth.api.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="FastAuth",
    lifespan=lifespan,
)

app.include_router(auth_router)


@app.get("/health")
def health():
    return {"status": "ok"}
