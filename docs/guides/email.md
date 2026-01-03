# Email Configuration

Configure email providers for verification and password reset.

## Overview

FastAuth supports email for:
- Email verification after registration
- Password reset requests
- Email change confirmation

Supported providers:
- **Console** - Prints to console (development)
- **SMTP** - Send via SMTP server (production)

## Console Provider (Development)

For development, use the console provider to see emails in your terminal:

### Configuration

```bash
# .env
EMAIL_PROVIDER=console
REQUIRE_EMAIL_VERIFICATION=false  # or true to test verification flow
```

### Example Output

When a verification email is sent:

```
========================================
Email sent via Console Provider
========================================
To: user@example.com
Subject: Verify your email address

Hi user@example.com,

Please verify your email address by clicking the link below:

http://localhost:8000/auth/email-verification/confirm?token=abc123...

This link expires in 24 hours.

========================================
```

## SMTP Provider (Production)

For production, configure an SMTP server to send real emails:

### Configuration

```bash
# .env
EMAIL_PROVIDER=smtp
REQUIRE_EMAIL_VERIFICATION=true

# SMTP Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Your App Name

# Email templates
EMAIL_VERIFICATION_URL=https://yourdomain.com/verify-email?token={token}
PASSWORD_RESET_URL=https://yourdomain.com/reset-password?token={token}
```

### Gmail Setup

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to Google Account → Security
   - Click "2-Step Verification"
   - Scroll to "App passwords"
   - Generate password for "Mail"
3. Use the app password in `SMTP_PASSWORD`

### SendGrid Setup

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

### AWS SES Setup

```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

## Email Verification

### Enable Email Verification

```bash
# .env
REQUIRE_EMAIL_VERIFICATION=true
EMAIL_VERIFICATION_EXPIRE_HOURS=24
```

### Verification Flow

1. User registers → Unverified user created
2. Verification email sent automatically
3. User clicks link → Email verified
4. User can now access protected routes

### Resend Verification Email

```bash
curl -X POST "http://localhost:8000/auth/email-verification/resend" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### Verify Email

```bash
curl -X POST "http://localhost:8000/auth/email-verification/confirm" \
  -H "Content-Type: application/json" \
  -d '{"token": "TOKEN_FROM_EMAIL"}'
```

### Check Verification Status

```python
from fastapi import Depends
from fastauth.api.dependencies import get_verified_user

@app.get("/verified-only")
def verified_route(current_user: User = Depends(get_verified_user)):
    return {"message": f"Hello verified user {current_user.email}"}
```

## Password Reset

### Request Password Reset

```bash
curl -X POST "http://localhost:8000/auth/password-reset/request" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

User receives an email with a reset link.

### Confirm Password Reset

```bash
curl -X POST "http://localhost:8000/auth/password-reset/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "TOKEN_FROM_EMAIL",
    "new_password": "newpassword456"
  }'
```

### Configure Reset Expiration

```bash
# .env
PASSWORD_RESET_EXPIRE_HOURS=1
```

## Custom Email Templates

### Override Email Content

Create custom email provider:

```python
from fastauth.email.base import EmailProvider

class CustomEmailProvider(EmailProvider):
    def send_verification_email(self, to_email: str, token: str):
        """Send custom verification email."""
        subject = "Welcome! Verify your email"
        verification_url = f"https://yourdomain.com/verify?token={token}"

        body = f"""
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Welcome to Our App!</h1>
            <p>Click the button below to verify your email:</p>
            <a href="{verification_url}" style="background: blue; color: white; padding: 10px;">
                Verify Email
            </a>
            <p>Or copy this link: {verification_url}</p>
        </body>
        </html>
        """

        self._send_email(to_email, subject, body, is_html=True)

    def send_password_reset_email(self, to_email: str, token: str):
        """Send custom password reset email."""
        subject = "Reset your password"
        reset_url = f"https://yourdomain.com/reset?token={token}"

        body = f"""
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Password Reset Request</h1>
            <p>Click below to reset your password:</p>
            <a href="{reset_url}">Reset Password</a>
            <p>This link expires in 1 hour.</p>
        </body>
        </html>
        """

        self._send_email(to_email, subject, body, is_html=True)

    def _send_email(self, to_email: str, subject: str, body: str, is_html: bool = False):
        """Send email via SMTP."""
        # Implement SMTP sending logic
        pass
```

### Use Custom Provider

```python
from fastapi import FastAPI
from fastauth import Settings as FastAuthSettings

app = FastAPI()

# Override email provider
custom_provider = CustomEmailProvider()
fastauth_settings = FastAuthSettings(
    email_provider_instance=custom_provider
)
```

## Frontend Integration

### Verification Page

```javascript
// Extract token from URL
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('token');

// Verify email
async function verifyEmail(token) {
  const response = await fetch('http://localhost:8000/auth/email-verification/confirm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token })
  });

  if (response.ok) {
    alert('Email verified successfully!');
    window.location.href = '/login';
  } else {
    alert('Verification failed. Token may be expired.');
  }
}

if (token) {
  verifyEmail(token);
}
```

### Password Reset Page

```javascript
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('token');

async function resetPassword(token, newPassword) {
  const response = await fetch('http://localhost:8000/auth/password-reset/confirm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, new_password: newPassword })
  });

  if (response.ok) {
    alert('Password reset successfully!');
    window.location.href = '/login';
  } else {
    alert('Reset failed. Token may be expired.');
  }
}
```

## Testing Emails

### Manual Testing

1. Set `EMAIL_PROVIDER=console`
2. Register a user
3. Check terminal for verification email
4. Copy token from console output
5. Call verification endpoint with token

### Automated Testing

```python
import pytest
from fastauth.email.console import ConsoleEmailProvider

def test_verification_email(client):
    # Register user
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200

    # In tests, you can capture console output or mock the email provider
    # to verify emails are sent correctly
```

### Mock Email Provider

```python
class MockEmailProvider(EmailProvider):
    def __init__(self):
        self.sent_emails = []

    def send_verification_email(self, to_email: str, token: str):
        self.sent_emails.append({
            "type": "verification",
            "to": to_email,
            "token": token
        })

    def send_password_reset_email(self, to_email: str, token: str):
        self.sent_emails.append({
            "type": "password_reset",
            "to": to_email,
            "token": token
        })

# Use in tests
mock_provider = MockEmailProvider()
# ... configure FastAuth to use mock_provider
# ... assert emails were sent correctly
assert len(mock_provider.sent_emails) == 1
assert mock_provider.sent_emails[0]["type"] == "verification"
```

## Common Issues

### "Email not sent"

**Cause**: SMTP credentials incorrect or provider blocking.

**Solution**:
- Verify SMTP credentials
- Check spam folder
- Enable "Less secure app access" (Gmail)
- Use app-specific password

### "Token expired"

**Cause**: Verification token expired (default: 24 hours).

**Solution**: Request new verification email:
```bash
POST /auth/email-verification/resend
```

### "Email already verified"

**Cause**: User already verified their email.

**Solution**: This is expected behavior. User can proceed to login.

## Environment Variables Reference

```bash
# Email Provider
EMAIL_PROVIDER=console  # or smtp

# Email Requirements
REQUIRE_EMAIL_VERIFICATION=false  # or true

# SMTP Settings (for smtp provider)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Your App Name
SMTP_TLS=true

# Token Expiration
EMAIL_VERIFICATION_EXPIRE_HOURS=24
PASSWORD_RESET_EXPIRE_HOURS=1

# Frontend URLs (for email links)
EMAIL_VERIFICATION_URL=https://yourdomain.com/verify-email?token={token}
PASSWORD_RESET_URL=https://yourdomain.com/reset-password?token={token}
```

## Next Steps

- **[Authentication](authentication.md)** - Registration and login
- **[Configuration](../reference/configuration.md)** - All environment variables
- **[Testing](../testing.md)** - Test your email flows
