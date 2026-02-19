import httpx
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from joserfc import jwt
from joserfc.jwk import KeySet

app = FastAPI(title="Resource Service")
security = HTTPBearer()

AUTH_JWKS_URL = "http://localhost:8000/.well-known/jwks.json"

_jwks_cache: KeySet | None = None


async def _get_key_set() -> KeySet:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(AUTH_JWKS_URL)
            resp.raise_for_status()
        _jwks_cache = KeySet.import_key_set(resp.json())
    return _jwks_cache


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    try:
        key_set = await _get_key_set()
        token = jwt.decode(credentials.credentials, key_set)
        return token.claims
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@app.get("/me")
async def me(claims: dict = Depends(get_current_user)):
    return {"user_id": claims.get("sub"), "claims": claims}


@app.get("/health")
async def health():
    return {"status": "ok"}
