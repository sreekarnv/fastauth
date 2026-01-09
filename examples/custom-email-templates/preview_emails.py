"""Preview email templates in the browser.

This script allows you to preview the email templates without sending actual emails.
It generates HTML files that you can open in your browser.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from app.email_client import CustomEmailClient
except ModuleNotFoundError:
    print("Error: FastAuth not installed")
    print("\nPlease install dependencies first:")
    print("  pip install -e ../..")
    print("  or")
    print("  pip install -r requirements.txt")
    sys.exit(1)


def preview_verification_email():
    """Generate a preview of the verification email."""
    client = CustomEmailClient()

    context = {
        **client.base_context,
        "user_email": "user@example.com",
        "verification_url": "http://localhost:8000/verify-email?token=abc123xyz",
        "token": "abc123xyz",
        "expires_in_hours": 24,
    }

    template = client.env.get_template("verification.html")
    html = template.render(context)

    output_path = Path(__file__).parent / "preview_verification.html"
    output_path.write_text(html, encoding="utf-8")

    print(f"[OK] Verification email preview saved to: {output_path}")
    print(f"  Open in browser: file://{output_path.absolute()}")


def preview_password_reset_email():
    """Generate a preview of the password reset email."""
    client = CustomEmailClient()

    context = {
        **client.base_context,
        "user_email": "user@example.com",
        "reset_url": "http://localhost:8000/reset-password?token=xyz789abc",
        "token": "xyz789abc",
        "expires_in_hours": 1,
    }

    template = client.env.get_template("password_reset.html")
    html = template.render(context)

    output_path = Path(__file__).parent / "preview_password_reset.html"
    output_path.write_text(html, encoding="utf-8")

    print(f"[OK] Password reset email preview saved to: {output_path}")
    print(f"  Open in browser: file://{output_path.absolute()}")


def preview_welcome_email():
    """Generate a preview of the welcome email."""
    client = CustomEmailClient()

    context = {
        **client.base_context,
        "user_email": "user@example.com",
        "user_name": "John Doe",
        "dashboard_url": "http://localhost:8000/dashboard",
    }

    template = client.env.get_template("welcome.html")
    html = template.render(context)

    output_path = Path(__file__).parent / "preview_welcome.html"
    output_path.write_text(html, encoding="utf-8")

    print(f"[OK] Welcome email preview saved to: {output_path}")
    print(f"  Open in browser: file://{output_path.absolute()}")


def main():
    """Generate all email previews."""
    print("Generating email template previews...\n")

    preview_verification_email()
    preview_password_reset_email()
    preview_welcome_email()

    print("\n[OK] All previews generated successfully!")
    print("\nYou can now open the preview_*.html files in your browser to see how")
    print("the emails will look to your users.")


if __name__ == "__main__":
    main()
