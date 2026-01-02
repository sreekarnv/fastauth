import uuid

from fastauth.security.jwt import decode_access_token


def parse_user_agent(user_agent: str | None) -> str:
    """Parse user agent string to extract device/browser info."""
    if not user_agent:
        return "Unknown Device"

    ua_lower = user_agent.lower()

    if "windows" in ua_lower:
        os = "Windows"
    elif "mac" in ua_lower or "macintosh" in ua_lower:
        os = "macOS"
    elif "linux" in ua_lower:
        os = "Linux"
    elif "android" in ua_lower:
        os = "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        os = "iOS"
    else:
        os = "Unknown OS"

    if "edg" in ua_lower:
        browser = "Edge"
    elif "chrome" in ua_lower:
        browser = "Chrome"
    elif "firefox" in ua_lower:
        browser = "Firefox"
    elif "safari" in ua_lower:
        browser = "Safari"
    else:
        browser = "Unknown Browser"

    return f"{browser} on {os}"


def get_session_id_from_token(token: str) -> uuid.UUID | None:
    """Extract session ID from JWT token if present."""
    try:
        payload = decode_access_token(token)
        session_id_str = payload.get("session_id")
        if session_id_str:
            return uuid.UUID(session_id_str)
    except Exception:
        pass
    return None
