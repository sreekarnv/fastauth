"""
FastAPI integration for FastAuth.

This module provides FastAPI routers and dependencies for authentication endpoints.

Requires: FastAPI must be installed (peer dependency).

Routers:
    auth_router: Registration, login, logout, token refresh
    oauth_router: OAuth provider authentication (requires [oauth] extra)
    account_router: Account management (password change, email change)
    sessions_router: Session management
"""

from fastauth._compat import HAS_HTTPX, require_fastapi

require_fastapi()

from .account import router as account_router  # noqa: E402
from .auth import router as auth_router  # noqa: E402
from .dependencies import (  # noqa: E402
    get_current_user,
    get_session,
    require_permission,
)
from .sessions import router as sessions_router  # noqa: E402

__all__ = [
    "auth_router",
    "account_router",
    "sessions_router",
    "get_current_user",
    "get_session",
    "require_permission",
]

if HAS_HTTPX:
    from .oauth import router as oauth_router  # noqa: E402, F401

    __all__.append("oauth_router")
