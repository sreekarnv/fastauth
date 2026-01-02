"""OAuth Google Example - FastAPI Application.

This example demonstrates:
- Google OAuth login (Sign in with Google)
- Linking OAuth accounts to existing users
- Unlinking OAuth accounts
- Creating new users from OAuth profile
- Viewing user profile with OAuth data
"""

import pathlib
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from starlette.middleware.sessions import SessionMiddleware

from fastauth import Settings as FastAuthSettings
from fastauth.adapters.sqlalchemy import (
    SQLAlchemyOAuthAccountAdapter,
    SQLAlchemyOAuthStateAdapter,
    SQLAlchemyRefreshTokenAdapter,
    SQLAlchemyUserAdapter,
)
from fastauth.core.oauth import (
    complete_oauth_flow,
    get_linked_accounts,
    initiate_oauth_flow,
)
from fastauth.core.refresh_tokens import create_refresh_token
from fastauth.providers.google import GoogleOAuthProvider
from fastauth.security.jwt import create_access_token, decode_access_token

from .database import create_db_and_tables, get_session
from .settings import settings as app_settings

BASE_DIR = pathlib.Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(
    title="FastAuth OAuth Example",
    description="Demonstrates Google OAuth integration with FastAuth",
    version="0.2.0",
)

# Add session middleware for storing PKCE code_verifier
# In production, use a strong secret key from environment variables
app.add_middleware(
    SessionMiddleware,
    secret_key=app_settings.jwt_secret_key,
)

fastauth_settings = FastAuthSettings(
    jwt_secret_key=app_settings.jwt_secret_key,
    jwt_algorithm=app_settings.jwt_algorithm,
    access_token_expire_minutes=app_settings.access_token_expire_minutes,
    require_email_verification=app_settings.require_email_verification,
    google_client_id=app_settings.google_client_id,
    google_client_secret=app_settings.google_client_secret,
)

google_provider = GoogleOAuthProvider(
    client_id=app_settings.google_client_id,
    client_secret=app_settings.google_client_secret,
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with login button."""
    return templates.TemplateResponse(request=request, name="home.jinja2", context={})


@app.get("/oauth/google/authorize")
async def google_authorize(
    request: Request,
    session: Session = Depends(get_session),
):
    """Initiate Google OAuth flow.

    This endpoint:
    1. Generates a secure state token and PKCE code_verifier
    2. Stores state in database and code_verifier in session
    3. Redirects user to Google's OAuth consent screen
    """
    oauth_state_adapter = SQLAlchemyOAuthStateAdapter(session)

    authorization_url, state_token, code_verifier = initiate_oauth_flow(
        states=oauth_state_adapter,
        provider=google_provider,
        redirect_uri=app_settings.google_redirect_uri,
    )

    request.session["oauth_code_verifier"] = code_verifier
    request.session["oauth_state"] = state_token

    return RedirectResponse(url=authorization_url)


@app.get("/oauth/google/callback")
async def google_callback(
    request: Request,
    code: str,
    state: str,
    session: Session = Depends(get_session),
):
    """Handle Google OAuth callback.

    This endpoint:
    1. Validates the state token
    2. Exchanges code for access token with PKCE verifier
    3. Fetches user info from Google
    4. Creates or links user account
    5. Returns JWT tokens
    """
    user_adapter = SQLAlchemyUserAdapter(session)
    oauth_account_adapter = SQLAlchemyOAuthAccountAdapter(session)
    oauth_state_adapter = SQLAlchemyOAuthStateAdapter(session)
    refresh_token_adapter = SQLAlchemyRefreshTokenAdapter(session)

    try:
        code_verifier = request.session.get("oauth_code_verifier")
        if not code_verifier:
            raise HTTPException(
                status_code=400,
                detail="Missing code_verifier in session.",
            )

        user, is_new_user = await complete_oauth_flow(
            states=oauth_state_adapter,
            oauth_accounts=oauth_account_adapter,
            users=user_adapter,
            provider=google_provider,
            code=code,
            state=state,
            code_verifier=code_verifier,
        )

        print(f"Is new user: {is_new_user}")

        request.session.pop("oauth_code_verifier", None)
        request.session.pop("oauth_state", None)

        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(
            refresh_tokens=refresh_token_adapter,
            user_id=user.id,
        )

        return templates.TemplateResponse(
            request=request,
            name="callback.jinja2",
            context={
                "refresh_token": refresh_token,
                "access_token": access_token,
                "user": user,
            },
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/oauth-accounts")
async def list_oauth_accounts(
    request: Request,
    access_token: str,
    session: Session = Depends(get_session),
):
    """List all OAuth accounts linked to the authenticated user.

    In a real app, you'd get the access_token from Authorization header.
    For demo purposes, we accept it as a query parameter.
    """
    try:
        payload = decode_access_token(access_token)
        print(payload)
        user_id = payload["sub"]

        oauth_account_adapter = SQLAlchemyOAuthAccountAdapter(session)
        accounts = get_linked_accounts(
            oauth_accounts=oauth_account_adapter,
            user_id=uuid.UUID(user_id),
        )

        return templates.TemplateResponse(
            request=request,
            name="linked_oauth_accounts.jinja2",
            context={"accounts": accounts, "access_token": access_token},
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


@app.get("/oauth-accounts/{account_id}/unlink")
async def unlink_account_route(
    account_id: str,
    access_token: str,
    session: Session = Depends(get_session),
):
    """Unlink an OAuth account."""
    try:
        payload = decode_access_token(access_token)
        user_id = uuid.UUID(payload["sub"])

        oauth_account_adapter = SQLAlchemyOAuthAccountAdapter(session)

        user_accounts = get_linked_accounts(
            oauth_accounts=oauth_account_adapter,
            user_id=user_id,
        )

        account_ids = [str(account.id) for account in user_accounts]
        if account_id not in account_ids:
            raise HTTPException(
                status_code=403, detail="Account does not belong to user"
            )

        oauth_account_adapter.delete(account_id=uuid.UUID(account_id))

        return RedirectResponse(url=f"/oauth-accounts?access_token={access_token}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/profile")
async def get_profile(
    request: Request,
    access_token: str,
    session: Session = Depends(get_session),
):
    """Get user profile with OAuth information."""
    try:
        payload = decode_access_token(access_token)
        user_id = uuid.UUID(payload["sub"])

        user_adapter = SQLAlchemyUserAdapter(session)
        user = user_adapter.get_by_id(user_id=user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        oauth_account_adapter = SQLAlchemyOAuthAccountAdapter(session)
        oauth_accounts = get_linked_accounts(
            oauth_accounts=oauth_account_adapter,
            user_id=user_id,
        )

        print(oauth_accounts)

        return templates.TemplateResponse(
            request=request,
            name="profile.jinja2",
            context={
                "oauth_accounts": oauth_accounts,
                "user": user,
                "access_token": access_token,
            },
        )

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
