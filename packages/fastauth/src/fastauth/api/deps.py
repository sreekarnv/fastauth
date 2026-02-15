from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fastauth.core.tokens import decode_token

security = HTTPBearer(auto_error=False)


async def get_fastauth(request: Request):
    return request.app.state.fastauth


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if not credentials:
        return None
    auth = request.app.state.fastauth
    try:
        claims = decode_token(credentials.credentials, auth.config)
        if claims.get("type") != "access":
            return None
        user = await auth.config.adapter.get_user_by_id(claims["sub"])
        return user
    except Exception:
        return None


async def require_auth(
    user=Depends(get_current_user),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return user
