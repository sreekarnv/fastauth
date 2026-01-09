# Custom Email Templates Example

This example demonstrates how to create beautiful, branded email templates with FastAuth using Jinja2.

## Features

- 🎨 **Beautiful HTML Emails** - Modern, responsive design that works across email clients
- 📱 **Mobile Responsive** - Emails look great on all devices
- 📝 **Plain Text Fallbacks** - Automatic plain text versions for email clients that don't support HTML
- 🎭 **Jinja2 Templates** - Powerful templating with inheritance and reusable components
- 🎨 **Easy Customization** - Simple to modify colors, branding, and content
- 👀 **Email Preview** - Preview your emails locally before sending

## What's Included

### Email Templates

1. **Verification Email** - Sent when users register
2. **Password Reset Email** - Sent when users request password reset
3. **Welcome Email** - Sent after successful email verification

Each template includes:
- HTML version with beautiful design
- Plain text version for compatibility
- Responsive layout
- Custom branding support

## Quick Start

### 1. Install Dependencies

```bash
# From this directory
pip install -r requirements.txt

# Or install FastAuth from parent directory
pip install -e ../..
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Preview Email Templates

Before sending any emails, preview them in your browser:

```bash
python preview_emails.py
```

This will generate `preview_*.html` files that you can open in your browser to see how the emails will look.

### 4. Setup SMTP (Choose One)

#### Option A: MailHog (Development - Recommended)

MailHog is a fake SMTP server perfect for testing emails locally:

```bash
# Using Docker
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Or download from: https://github.com/mailhog/MailHog/releases
```

Then access MailHog UI at: http://localhost:8025

Your `.env` should have:
```env
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USE_TLS=false
```

#### Option B: Gmail (Production)

1. Enable 2-factor authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Update `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_USE_TLS=true
```

#### Option C: SendGrid (Production)

1. Sign up for SendGrid: https://sendgrid.com
2. Create an API key
3. Update `.env`:

```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_USE_TLS=true
```

### 5. Run the Application

```bash
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for the API documentation.

## Testing Emails

### 1. Register a New User

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

Check MailHog (http://localhost:8025) to see the verification email! Click the "Verify Email" button in the email to complete verification.

### 2. Request Password Reset

```bash
curl -X POST "http://localhost:8000/auth/password-reset/request" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com"
  }'
```

Check MailHog to see the password reset email! Click the "Reset Password" button to proceed.

### 3. Send Welcome Email (Custom Endpoint)

```bash
curl -X POST "http://localhost:8000/send-welcome/test@example.com"
```

## Customizing Templates

### Modify Colors and Branding

Edit `templates/emails/base.html`:

```css
/* Change primary color */
.header {
    background: linear-gradient(135deg, #your-color 0%, #your-color-2 100%);
}

.button {
    background: linear-gradient(135deg, #your-color 0%, #your-color-2 100%);
}
```

### Update Company Information

Edit `app/email_client.py`:

```python
self.base_context = {
    "app_name": "Your App Name",
    "company_name": "Your Company",
    "support_email": "support@yourcompany.com",
    "year": 2024,
}
```

### Add Your Logo

1. Place your logo in `templates/static/logo.png`
2. Update `templates/emails/base.html` header section:

```html
<td class="header">
    <img src="https://yourdomain.com/logo.png" alt="Logo" style="max-width: 200px;">
    <h1>{{ app_name }}</h1>
</td>
```

### Create New Email Templates

1. Create new HTML template in `templates/emails/your-template.html`
2. Create plain text version in `templates/emails/your-template.txt`
3. Add method to `CustomEmailClient`:

```python
def send_custom_email(self, *, to: str, custom_data: str) -> None:
    context = {
        **self.base_context,
        "user_email": to,
        "custom_data": custom_data,
    }

    html_template = self.env.get_template("your-template.html")
    html_body = html_template.render(context)

    text_template = self.env.get_template("your-template.txt")
    text_body = text_template.render(context)

    self._send_email(
        to=to,
        subject="Your Subject",
        html_body=html_body,
        text_body=text_body,
    )
```

## Project Structure

```
custom-email-templates/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── email_client.py      # Custom email client
│   ├── database.py          # Database configuration
│   └── settings.py          # App settings
├── templates/
│   ├── emails/
│   │   ├── base.html        # Base template (header/footer)
│   │   ├── verification.html
│   │   ├── verification.txt
│   │   ├── password_reset.html
│   │   ├── password_reset.txt
│   │   ├── welcome.html
│   │   └── welcome.txt
│   └── static/
│       └── logo.png         # Your logo (add this)
├── preview_emails.py        # Email preview generator
├── requirements.txt
├── .env.example
└── README.md
```

## How It Works

### 1. Custom EmailClient

The `CustomEmailClient` class extends FastAuth's `EmailClient` base class:

```python
class CustomEmailClient(EmailClient):
    def __init__(self, template_dir: str = "templates/emails"):
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(template_path),
            autoescape=True,
        )

    def send_verification_email(self, *, to: str, token: str) -> None:
        # Render templates
        html = self.env.get_template("verification.html").render(context)
        text = self.env.get_template("verification.txt").render(context)

        # Send email
        self._send_email(to=to, subject="...", html_body=html, text_body=text)
```

### 2. Override the Default Email Client

In `app/main.py`, we need to monkey-patch the auth module:

```python
def custom_get_email_client():
    return CustomEmailClient()

# Monkey-patch the auth module to use our custom email client
from fastauth.api import auth as auth_module
auth_module.get_email_client = custom_get_email_client
```

**Why monkey-patch?** The `fastauth.api.auth` module imports `get_email_client` at the module level, so it keeps a reference to the original function. We need to override it in the auth module itself for it to take effect.

Now FastAuth will use your custom email client for all authentication emails!

### 3. Email Verification Flow with Clickable Links

FastAuth's API uses POST endpoints for verification (`/auth/email-verification/confirm`), but email links need to be GET requests. This example includes wrapper endpoints that make the flow work:

**The Flow:**
1. User registers → FastAuth sends verification email with token
2. Email contains clickable link: `http://localhost:8000/verify-email?token=abc123`
3. User clicks link → hits our GET endpoint `/verify-email`
4. Our endpoint forwards to FastAuth's POST endpoint `/auth/email-verification/confirm`
5. Returns success/error message to user

**Wrapper Endpoints in `app/main.py`:**

```python
@app.get("/verify-email")
def verify_email_redirect(token: str):
    """Convert GET request from email to POST request for FastAuth API."""
    response = requests.post(
        "http://localhost:8000/auth/email-verification/confirm",
        json={"token": token},
    )
    return {"message": "Email verified successfully!"} if response.status_code == 204 else {"error": "Invalid token"}

@app.get("/reset-password")
def reset_password_page(token: str):
    """Handle password reset link from email."""
    # In production, this would render a form for entering new password
    return {"message": "Password reset token received", "token": token}
```

**Why is this needed?** The default FastAuth email client just sends the token as plain text without any URL. For better UX with clickable "Verify Email" buttons, we need these wrapper endpoints.

## Email Design Best Practices

### Inline CSS

Email clients don't support external CSS or `<style>` tags well. Use inline styles:

```html
<p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
    Your text here
</p>
```

### Tables for Layout

Use `<table>` elements for layout (not divs) for maximum compatibility:

```html
<table role="presentation" width="100%" cellspacing="0" cellpadding="0">
    <tr>
        <td>Content here</td>
    </tr>
</table>
```

### Test Across Email Clients

Test your emails in:
- Gmail (web, mobile app)
- Outlook (Windows, Mac, web)
- Apple Mail (iOS, macOS)
- Yahoo Mail
- ProtonMail

Tools like [Litmus](https://litmus.com) or [Email on Acid](https://www.emailonacid.com) can help with testing.

## Production Considerations

### Use a Transactional Email Service

For production, use services like:
- **SendGrid** - 100 emails/day free tier
- **Amazon SES** - Very cheap, $0.10 per 1000 emails
- **Mailgun** - Good deliverability
- **Postmark** - Focused on transactional emails

### Monitor Email Deliverability

Track:
- Delivery rates
- Open rates
- Bounce rates
- Spam complaints

### Implement Email Retry Logic

For failed sends, implement retry with exponential backoff:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def send_with_retry(self, to, subject, body):
    # Send email
    pass
```

### Use Background Tasks

For better performance, send emails asynchronously:

```python
from fastapi import BackgroundTasks

@app.post("/register")
def register(background_tasks: BackgroundTasks):
    # ... create user ...
    background_tasks.add_task(
        email_client.send_verification_email,
        to=user.email,
        token=token
    )
```

## Troubleshooting

### Emails Not Sending

1. Check SMTP credentials in `.env`
2. Verify firewall isn't blocking SMTP port
3. Check spam folder
4. Review logs: `uvicorn app.main:app --log-level debug`

### Templates Not Loading

1. Ensure templates are in `templates/emails/` directory
2. Check template file names match exactly
3. Verify Jinja2 is installed: `pip list | grep -i jinja`

### Styling Issues

1. Use inline CSS instead of `<style>` tags
2. Test in multiple email clients
3. Use tables for layout
4. Avoid JavaScript (not supported in emails)

## Next Steps

- Add more email templates (e.g., account locked, password changed, etc.)
- Implement email analytics tracking
- Add A/B testing for email content
- Create multi-language email support
- Add email preference center

## Resources

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Email Design Best Practices](https://www.campaignmonitor.com/blog/email-marketing/best-practices/)
- [Can I Email?](https://www.caniemail.com/) - Email client CSS support
- [Really Good Emails](https://reallygoodemails.com/) - Email design inspiration

## Need Help?

- Check the [FastAuth documentation](https://sreekarnv.github.io/fastauth/)
- Report issues on [GitHub](https://github.com/sreekarnv/fastauth/issues)
- Ask questions in [Discussions](https://github.com/sreekarnv/fastauth/discussions)
