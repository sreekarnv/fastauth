from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from fastauth.adapters.sqlalchemy.models import User
from fastauth.api.adapter_factory import AdapterFactory
from fastauth.api.dependencies import get_current_user, get_session
from fastauth.api.schemas import (
    OAuthAuthorizationResponse,
    OAuthCallbackRequest,
    OAuthLinkResponse,
    TokenResponse,
)
from fastauth.api.utils import extract_request_metadata
from fastauth.core.oauth import (
    OAuthAccountAlreadyLinkedError,
    OAuthError,
    OAuthStateError,
    complete_oauth_flow,
    get_linked_accounts,
    initiate_oauth_flow,
    unlink_oauth_account,
)
from fastauth.core.refresh_tokens import create_refresh_token
from fastauth.core.sessions import create_session
from fastauth.providers import GoogleOAuthProvider, get_provider, register_provider
from fastauth.providers.base import OAuthProvider
from fastauth.security.jwt import create_access_token
from fastauth.settings import settings

router = APIRouter(prefix="/oauth", tags=["oauth"])


def _get_or_register_provider(provider_name: str) -> OAuthProvider:
    """
    Get or register an OAuth provider.

    This ensures providers are registered with credentials from settings.
    """
    provider = get_provider(provider_name)

    if provider:
        return provider

    if provider_name == "google":
        if not settings.google_client_id or not settings.google_client_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth is not configured.\
                    Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
            )

        google = GoogleOAuthProvider(
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
        )
        register_provider(google)
        return google

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"OAuth provider '{provider_name}' not found or not configured",
    )


@router.get("/{provider}/authorize", response_model=OAuthAuthorizationResponse)
def authorize(
    provider: str,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User | None = None,
) -> OAuthAuthorizationResponse:
    """
    Initiate OAuth authorization flow.

    This endpoint generates a state token and authorization URL.
    If the user is logged in, this will be a linking flow.
    If not logged in, this will be a login/registration flow.

    The code_verifier for PKCE is stored in the session.

    Args:
        provider_name: OAuth provider (e.g., 'google', 'github')
        request: FastAPI request object
        session: Database session
        current_user: Optional current user (if authenticated)

    Returns:
        OAuthAuthorizationResponse with authorization_url
    """
    provider_instance = _get_or_register_provider(provider)

    adapters = AdapterFactory(session=session)

    redirect_uri = str(request.url_for("oauth_callback", provider=provider))

    user_id = current_user.id if current_user else None

    authorization_url, state_token, code_verifier = initiate_oauth_flow(
        states=adapters.oauth_states,
        provider=provider_instance,
        redirect_uri=redirect_uri,
        user_id=user_id,
        use_pkce=True,
    )

    # NOTE: This requires SessionMiddleware to be configured
    # If SessionMiddleware is not available, we just won't store the code_verifier
    if code_verifier and "session" in request.scope:
        request.session["oauth_code_verifier"] = code_verifier
        request.session["oauth_state"] = state_token

    return OAuthAuthorizationResponse(authorization_url=authorization_url)


@router.post("/{provider}/callback", response_model=TokenResponse)
async def oauth_callback(
    provider: str,
    payload: OAuthCallbackRequest,
    request: Request,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """
    Handle OAuth callback after user authorization.

    This endpoint:
    1. Validates the state token (CSRF protection)
    2. Exchanges authorization code for tokens
    3. Fetches user info from provider
    4. Creates or links user account
    5. Issues FastAuth tokens (JWT + refresh token)

    Args:
        provider_name: OAuth provider (e.g., 'google', 'github')
        payload: Callback request with code and state
        request: FastAPI request object
        session: Database session

    Returns:
        TokenResponse with access_token and refresh_token
    """
    provider_instance = _get_or_register_provider(provider)

    code_verifier = None
    try:
        if hasattr(request, "session") and "session" in request.scope:
            code_verifier = request.session.get("oauth_code_verifier")
            stored_state = request.session.get("oauth_state")

            if stored_state is not None:
                if stored_state != payload.state:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="State mismatch - possible CSRF attack",
                    )

                request.session.pop("oauth_code_verifier", None)
                request.session.pop("oauth_state", None)
    except (AssertionError, KeyError):
        # SessionMiddleware not installed, skip session checks
        pass

    adapters = AdapterFactory(session=session)

    try:
        user, _ = await complete_oauth_flow(
            states=adapters.oauth_states,
            oauth_accounts=adapters.oauth_accounts,
            users=adapters.users,
            provider=provider_instance,
            code=payload.code,
            state=payload.state,
            code_verifier=code_verifier,
        )

    except OAuthStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except OAuthAccountAlreadyLinkedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(
        refresh_tokens=adapters.refresh_tokens,
        user_id=user.id,
    )

    metadata = extract_request_metadata(request)
    create_session(
        sessions=adapters.sessions,
        users=adapters.users,
        user_id=user.id,
        ip_address=metadata.ip_address,
        user_agent=metadata.user_agent,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get("/linked", response_model=list[OAuthLinkResponse])
def list_linked_accounts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[OAuthLinkResponse]:
    """
    List all OAuth accounts linked to the current user.

    Requires authentication.

    Args:
        session: Database session
        current_user: Current authenticated user

    Returns:
        List of linked OAuth accounts
    """
    adapters = AdapterFactory(session=session)

    accounts = get_linked_accounts(
        oauth_accounts=adapters.oauth_accounts,
        user_id=current_user.id,
    )

    return [
        OAuthLinkResponse(
            provider=account.provider,
            email=account.email,
            name=account.name,
            linked_at=account.created_at,
        )
        for account in accounts
    ]


@router.delete("/{provider}/unlink", status_code=status.HTTP_204_NO_CONTENT)
def unlink_provider(
    provider: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Unlink an OAuth provider from the current user's account.

    Requires authentication.

    Args:
        provider_name: OAuth provider to unlink (e.g., 'google', 'github')
        session: Database session
        current_user: Current authenticated user

    Returns:
        204 No Content on success
    """
    adapters = AdapterFactory(session=session)

    try:
        unlink_oauth_account(
            oauth_accounts=adapters.oauth_accounts,
            user_id=current_user.id,
            provider=provider,
        )
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return None
