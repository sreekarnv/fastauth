from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from fastauth.api.auth import router as auth_router
from fastauth.security.jwt import decode_access_token
from app.database import init_db, get_session as app_get_session


app = FastAPI(title="FastAuth Basic Example")

init_db()

app.include_router(auth_router)

from fastauth.api import dependencies
app.dependency_overrides[dependencies.get_session] = app_get_session

security = HTTPBearer()


@app.get("/protected")
def protected(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    payload = decode_access_token(credentials.credentials)
    return {
        "message": "You are authenticated",
        "user_id": payload["sub"],
    }
