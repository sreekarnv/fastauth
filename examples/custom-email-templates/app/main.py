"""Custom Email Templates Example - FastAPI Application.

This example demonstrates how to use custom email templates with FastAuth
by creating a custom EmailClient that uses Jinja2 for beautiful HTML emails.
"""

from fastapi import Depends, FastAPI
from sqlmodel import Session

from fastauth import Settings as FastAuthSettings
from fastauth import auth_router
from fastauth.api import dependencies

from .database import create_db_and_tables, get_session
from .email_client import CustomEmailClient
from .settings import settings

app = FastAPI(
    title="FastAuth Custom Email Templates Example",
    description="Demonstrates custom email templates with Jinja2",
    version="1.0.0",
)

fastauth_settings = FastAuthSettings(
    jwt_secret_key=settings.jwt_secret_key,
    jwt_algorithm=settings.jwt_algorithm,
    access_token_expire_minutes=settings.access_token_expire_minutes,
    require_email_verification=settings.require_email_verification,
    # Email settings
    email_backend="smtp",
    smtp_host=settings.smtp_host,
    smtp_port=settings.smtp_port,
    smtp_username=settings.smtp_username,
    smtp_password=settings.smtp_password,
    smtp_from_email=settings.smtp_from_email,
    smtp_use_tls=settings.smtp_use_tls,
)


@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    create_db_and_tables()


# Override the email client in the auth module
# This is necessary because auth.py imports get_email_client at module level
def custom_get_email_client():
    """Return our custom email client."""
    return CustomEmailClient()


# Monkey-patch the auth module to use our custom email client
from fastauth.api import auth as auth_module  # noqa: E402

auth_module.get_email_client = custom_get_email_client

app.dependency_overrides[dependencies.get_session] = get_session

app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "message": "FastAuth Custom Email Templates Example",
        "docs": "/docs",
        "features": [
            "Beautiful HTML email templates",
            "Plain text fallbacks",
            "Jinja2 template engine",
            "Custom branding",
            "Responsive design",
        ],
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/send-welcome/{email}")
def send_welcome_email(
    email: str,
    _: Session = Depends(get_session),
):
    email_client = custom_get_email_client()
    email_client.send_welcome_email(to=email, name=email.split("@")[0])
    return {"message": f"Welcome email sent to {email}"}


@app.get("/verify-email")
def verify_email_redirect(token: str):
    """Handle email verification from clickable link.

    This endpoint converts the GET request from email links to the POST request
    expected by FastAuth's /auth/email-verification/confirm endpoint.
    """
    import requests

    response = requests.post(
        "http://localhost:8000/auth/email-verification/confirm",
        json={"token": token},
    )

    if response.status_code == 204:
        return {
            "message": "Email verified successfully!",
            "status": "success",
            "next_step": "You can now log in to your account",
        }
    else:
        return {
            "message": "Invalid or expired verification token",
            "status": "error",
            "detail": "Please request a new verification email",
        }


@app.get("/reset-password")
def reset_password_page(token: str):
    """Handle password reset from clickable link.

    This endpoint accepts the reset token from email links.
    In a real application, this would render a form where users can enter
    their new password. For this example, we'll return instructions.
    """
    return {
        "message": "Password reset token received",
        "token": token,
        "instructions": (
            "In a real application, this would show a form to enter a new password."
            "To complete the reset, make a POST request to /auth/password-reset/confirm"
            "with the token and new password."
        ),
        "example_curl": (
            f'curl -X POST "http://localhost:8000/auth/password-reset/confirm" '
            f'-H "Content-Type: application/json" '
            f'-d \'{{"token": "{token}", "password": "newpassword123"}}\''
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
