# Configuration

FastAuth is configured using environment variables and Pydantic settings.

## Environment Variables

Create a `.env` file in your project root:

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
EMAIL_PROVIDER=console
REQUIRE_EMAIL_VERIFICATION=false

# Database
DATABASE_URL=sqlite:///./app.db
```

## Settings Class

```python
from fastauth import Settings

settings = Settings(
    jwt_secret_key="your-secret-key",
    access_token_expire_minutes=30,
    require_email_verification=True
)
```

## Available Settings

See the [Settings API Reference](reference/settings.md) for all available configuration options.
