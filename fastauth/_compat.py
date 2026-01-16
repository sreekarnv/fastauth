"""
Dependency compatibility utilities.

Provides helpers for checking and importing dependencies.
FastAPI is a peer dependency (must be installed by user).
httpx is an optional extra for OAuth providers.
"""

from importlib.util import find_spec
from typing import TYPE_CHECKING

# Check which dependencies are available
HAS_FASTAPI = find_spec("fastapi") is not None
HAS_HTTPX = find_spec("httpx") is not None


class MissingDependencyError(ImportError):
    """Raised when a required dependency is not installed."""

    def __init__(self, package: str, install_hint: str):
        self.package = package
        self.install_hint = install_hint
        super().__init__(f"'{package}' is required for this feature. {install_hint}")


def require_fastapi() -> None:
    """Raise an error if FastAPI is not installed (peer dependency)."""
    if not HAS_FASTAPI:
        raise MissingDependencyError(
            "fastapi",
            "FastAPI is a peer dependency. Install it with: pip install fastapi",
        )


def require_httpx() -> None:
    """Raise an error if httpx is not installed."""
    if not HAS_HTTPX:
        raise MissingDependencyError(
            "httpx", "Install it with: pip install sreekarnv-fastauth[oauth]"
        )


# Type checking imports - these are only used for type hints
# and won't cause import errors at runtime
if TYPE_CHECKING:
    pass
