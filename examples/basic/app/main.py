from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from fastauth.api.auth import router as auth_router
from fastauth.db.session import init_db
from fastauth.security.jwt import decode_access_token


app = FastAPI(title="FastAuth Basic Example")

init_db() 

app.include_router(auth_router)

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
