# Basic FastAuth Example

A simple FastAPI application demonstrating FastAuth integration with SQLite database.

## What This Example Shows

- ✅ Complete FastAuth setup with SQLite
- ✅ User registration and authentication
- ✅ Email verification (console output)
- ✅ Password reset functionality
- ✅ Token refresh
- ✅ Protected routes
- ✅ Environment-based configuration

## Project Structure

```
basic/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app with FastAuth routes
│   ├── database.py      # Database connection and session
│   └── settings.py      # Configuration management
├── .env.example         # Example environment variables
└── README.md           # This file
```

## Quick Start

### 1. Install Dependencies

From the repository root:

```bash
cd examples/basic
pip install fastapi[all] sqlmodel argon2-cffi python-jose pydantic-settings
```

Or with the parent package:

```bash
pip install -e ../..
```

### 2. Set Up Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` if needed:

```bash
# Database
DATABASE_URL=sqlite:///./fastauth.db

# Secret Key (change in production!)
SECRET_KEY=dev-secret-key-change-this-in-production

# Email (console for development)
EMAIL_BACKEND=console

# Auth
REQUIRE_EMAIL_VERIFICATION=false  # Set to true to require email verification
```

### 3. Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 4. Try It Out

Open your browser to `http://localhost:8000/docs` to see the interactive API documentation.

## API Endpoints

The application includes all FastAuth endpoints:

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login with email and password
- `POST /auth/logout` - Logout and revoke refresh token
- `POST /auth/refresh` - Get new access token

### Password Reset
- `POST /auth/password-reset/request` - Request password reset email
- `POST /auth/password-reset/confirm` - Reset password with token

### Email Verification
- `POST /auth/email-verification/request` - Request verification email
- `POST /auth/email-verification/confirm` - Verify email with token
- `POST /auth/email-verification/resend` - Resend verification email

### Protected Routes (Example)
- `GET /protected` - Example protected endpoint

## Usage Examples

### Register a User

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "id": "...",
  "email": "user@example.com",
  "is_verified": false,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00"
}
```

### Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Access Protected Route

```bash
curl -X GET "http://localhost:8000/protected" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:
```json
{
  "message": "You are authenticated",
  "user_id": "..."
}
```

### Refresh Token

```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### Request Password Reset

```bash
curl -X POST "http://localhost:8000/auth/password-reset/request" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

The reset token will be printed to the console (since we're using `console` email backend).

### Confirm Password Reset

```bash
curl -X POST "http://localhost:8000/auth/password-reset/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "TOKEN_FROM_CONSOLE",
    "new_password": "newpassword123"
  }'
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./fastauth.db` | Database connection string |
| `SECRET_KEY` | `dev-secret-key` | Secret key for JWT tokens (**change in production!**) |
| `REQUIRE_EMAIL_VERIFICATION` | `false` | Require email verification before login |
| `EMAIL_BACKEND` | `console` | Email provider (`console`, `smtp`) |
| `SMTP_HOST` | - | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_USERNAME` | - | SMTP username |
| `SMTP_PASSWORD` | - | SMTP password |
| `SMTP_FROM_EMAIL` | `no-reply@example.com` | From email address |

### Email Verification

To enable email verification:

1. Set `REQUIRE_EMAIL_VERIFICATION=true` in `.env`
2. Configure email backend (SMTP or other)
3. New users must verify their email before logging in

**Development (Console):**
```bash
EMAIL_BACKEND=console
REQUIRE_EMAIL_VERIFICATION=true
```
Verification tokens will print to console.

**Production (SMTP):**
```bash
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@yourapp.com
REQUIRE_EMAIL_VERIFICATION=true
```

## Understanding the Code

### main.py

The main application file:

```python
from fastapi import FastAPI
from fastauth.api.auth import router as auth_router
from fastauth.api import dependencies
from app.database import get_session, init_db

app = FastAPI(title="FastAuth Basic Example")

# Initialize database tables
init_db()

# Include FastAuth routes
app.include_router(auth_router)

# Override session dependency to use our database
app.dependency_overrides[dependencies.get_session] = get_session
```

### database.py

Database setup with SQLModel:

```python
from sqlmodel import Session, SQLModel, create_engine

engine = create_engine(settings.database_url)

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    SQLModel.metadata.create_all(engine)  # Create all tables
```

### settings.py

Configuration management with Pydantic:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./fastauth.db"
    secret_key: str = "dev-secret-key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
    )
```

## Security Notes

⚠️ **This is a development example. For production:**

1. **Change the SECRET_KEY** - Use a strong, random secret key:
   ```bash
   SECRET_KEY=$(openssl rand -hex 32)
   ```

2. **Use HTTPS** - Always use TLS/SSL in production

3. **Configure real email** - Use SMTP or email service (SendGrid, etc.)

4. **Use PostgreSQL/MySQL** - SQLite is not recommended for production

5. **Enable email verification** - Set `REQUIRE_EMAIL_VERIFICATION=true`

6. **Set strong passwords** - Enforce password requirements

7. **Rate limiting** - FastAuth has built-in rate limiting

## Troubleshooting

### Database Issues

**Problem:** `no such table: user`

**Solution:** Delete the database and restart:
```bash
rm fastauth.db
uvicorn app.main:app --reload
```

### Email Not Sending

**Problem:** Email verification token not visible

**Solution:** Check console output if using `EMAIL_BACKEND=console`:
```
Email verification token: abc123...
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'fastauth'`

**Solution:** Install FastAuth from the parent directory:
```bash
pip install -e ../..
```

## Next Steps

- Add custom user fields (see main README)
- Implement role-based access control
- Add more protected routes
- Configure production email provider
- Deploy to production

## Resources

- [FastAuth Documentation](../../README.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
