"""Test SMTP configuration by sending a test email.

This script helps you verify that your SMTP settings are correct
before running the full application.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.email_client import CustomEmailClient
from app.settings import settings


def test_smtp_connection():
    """Test SMTP connection and send a test email."""
    print("Testing SMTP configuration...")
    print(f"  Host: {settings.smtp_host}")
    print(f"  Port: {settings.smtp_port}")
    print(f"  From: {settings.smtp_from_email}")
    print(f"  TLS: {settings.smtp_use_tls}")
    print()

    to_email = input("Enter email address to send test email to: ").strip()

    if not to_email or "@" not in to_email:
        print("[ERROR] Invalid email address")
        return

    try:
        client = CustomEmailClient()

        print(f"\nSending verification email to {to_email}...")
        client.send_verification_email(to=to_email, token="test-token-123-abc-xyz")

        print("[OK] Verification email sent successfully!")

        send_reset = input("\nSend password reset email too? (y/n):").strip().lower()
        if send_reset == "y":
            print(f"Sending password reset email to {to_email}...")
            client.send_password_reset_email(
                to=to_email, token="reset-token-456-def-uvw"
            )
            print("[OK] Password reset email sent successfully!")

        send_welcome = input("\nSend welcome email too? (y/n): ").strip().lower()
        if send_welcome == "y":
            print(f"Sending welcome email to {to_email}...")
            client.send_welcome_email(to=to_email, name=to_email.split("@")[0])
            print("[OK] Welcome email sent successfully!")

        print("\n[SUCCESS] All tests passed!")
        print("\nCheck your email inbox (and spam folder) to see the emails.")

        if settings.smtp_host == "localhost" and settings.smtp_port == 1025:
            print(
                "\n[INFO] Using MailHog? Check http://localhost:8025 to see the emails."
            )

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your SMTP credentials in .env")
        print("2. Verify firewall isn't blocking SMTP port")
        print("3. If using Gmail, ensure you're using an App Password")
        print("4. Try using MailHog for local testing (localhost:1025)")


if __name__ == "__main__":
    test_smtp_connection()
