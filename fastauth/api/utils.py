"""API utility functions."""

from dataclasses import dataclass

from fastapi import Request


@dataclass
class RequestMetadata:
    """Request metadata extracted from HTTP request."""

    ip_address: str | None
    user_agent: str | None


def extract_request_metadata(request: Request) -> RequestMetadata:
    """
    Extract common metadata from an HTTP request.

    This utility function consolidates request metadata extraction
    to ensure consistency across endpoints.

    Args:
        request: FastAPI Request object

    Returns:
        RequestMetadata containing IP address and user agent

    Example:
        >>> metadata = extract_request_metadata(request)
        >>> create_session(ip_address=metadata.ip_address, ...)
    """
    return RequestMetadata(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
