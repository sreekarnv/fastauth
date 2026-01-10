"""Constants for error messages and common strings.

This module centralizes error messages to ensure consistency across
the application and make updates easier.
"""


class ErrorMessages:
    """Error message constants used across the application."""

    # Token-related errors
    INVALID_OR_EXPIRED_TOKEN = "Invalid or expired token"
    INVALID_OR_EXPIRED_RESET_TOKEN = "Invalid or expired reset token"
    INVALID_OR_EXPIRED_VERIFICATION_TOKEN = "Invalid or expired verification token"
    INVALID_OR_EXPIRED_EMAIL_CHANGE_TOKEN = "Invalid or expired email change token"
    INVALID_OR_EXPIRED_STATE_TOKEN = "Invalid or expired state token"

    # User-related errors
    USER_NOT_FOUND = "User not found"
    USER_NOT_FOUND_OR_INACTIVE = "User not found or inactive"
    USER_ALREADY_EXISTS = "User already exists"

    # Email-related errors
    EMAIL_ALREADY_EXISTS = "Email already exists"
    EMAIL_NOT_VERIFIED = "Email address is not verified"

    # Authentication errors
    INVALID_CREDENTIALS = "Invalid email or password"
    INVALID_PASSWORD = "Password is incorrect"
    CURRENT_PASSWORD_INVALID = "Current password is incorrect"

    # Rate limiting errors
    RATE_LIMIT_REGISTRATION = "Too many registration attempts. Try again later."
    RATE_LIMIT_LOGIN = "Too many login attempts. Try again later."
    RATE_LIMIT_GENERAL = "Too many requests. Try again later."

    # OAuth errors
    OAUTH_PROVIDER_NOT_CONFIGURED = "OAuth provider not configured"
    OAUTH_ACCOUNT_ALREADY_LINKED = "OAuth account already linked to another user"
    OAUTH_USER_NOT_FOUND = "User not found for existing OAuth account"
    OAUTH_USER_NOT_FOUND_FOR_LINKING = "User not found for linking"

    # Session errors
    SESSION_NOT_FOUND = "Session not found"

    # Role errors
    ROLE_NOT_FOUND = "Role not found"
    PERMISSION_NOT_FOUND = "Permission not found"
