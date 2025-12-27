# Architecture

FastAuth uses a clean, layered architecture that separates concerns and maintains database agnosticism.

## Design Principles

### 1. Database Agnostic Core

The core business logic has no knowledge of the database layer. All database operations are abstracted through adapter interfaces.

**Benefits:**
- Swap databases without changing business logic
- Easy to test with mock adapters
- Clear separation of concerns

### 2. Adapter Pattern

Database-specific code lives in adapters that implement abstract base classes.

**Flow:**
```
API Layer → Core Logic → Adapter Interface → Adapter Implementation → Database
```

### 3. Dependency Injection

FastAPI's dependency injection system allows easy customization and testing.

```python
# Override dependencies
app.dependency_overrides[get_session] = your_custom_session
```

## Architecture Layers

```
┌─────────────────────────────────────┐
│         FastAPI Routes              │  Your application
├─────────────────────────────────────┤
│         FastAuth API Layer          │  HTTP handlers
├─────────────────────────────────────┤
│         Core Business Logic         │  Database-agnostic
├─────────────────────────────────────┤
│         Adapter Interface           │  Abstract base classes
├─────────────────────────────────────┤
│    Adapter Implementation           │  SQLAlchemy, MongoDB, etc.
└─────────────────────────────────────┘
```

### Layer Responsibilities

**FastAPI Routes (Your Application)**
- Include FastAuth router
- Define custom routes
- Override dependencies

**FastAuth API Layer**
- HTTP request/response handling
- Input validation (Pydantic)
- Error handling
- Rate limiting

**Core Business Logic**
- Authentication logic
- Authorization (RBAC)
- Token management
- Password hashing
- Email verification
- Password reset

**Adapter Interface**
- Abstract base classes
- Define required methods
- No implementation details

**Adapter Implementation**
- Database-specific code
- CRUD operations
- Query logic
- No business logic

## Component Architecture

### Core Components

#### Users (`fastauth/core/users.py`)
- User creation
- Authentication
- Password verification

#### Refresh Tokens (`fastauth/core/refresh_tokens.py`)
- Token generation
- Token validation
- Token rotation

#### Password Reset (`fastauth/core/password_reset.py`)
- Reset request
- Token validation
- Password update

#### Email Verification (`fastauth/core/email_verification.py`)
- Verification request
- Token validation
- Email confirmation

#### Roles (`fastauth/core/roles.py`)
- Role creation and management
- Permission creation and assignment
- Role-to-user assignment
- Permission checking
- User authorization

### Adapters

#### Base Adapters (`fastauth/adapters/base/`)
Abstract interfaces defining required methods.

**UserAdapter:**
```python
class UserAdapter(ABC):
    @abstractmethod
    def get_by_email(self, email: str): ...

    @abstractmethod
    def create_user(self, *, email: str, hashed_password: str): ...
```

**RoleAdapter:**
```python
class RoleAdapter(ABC):
    @abstractmethod
    def create_role(self, *, name: str, description: str | None = None): ...

    @abstractmethod
    def assign_role_to_user(self, *, user_id: UUID, role_id: UUID): ...

    @abstractmethod
    def get_user_permissions(self, user_id: UUID): ...
```

#### SQLAlchemy Implementation (`fastauth/adapters/sqlalchemy/`)
Concrete implementation using SQLModel.

```python
class SQLAlchemyUserAdapter(UserAdapter):
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str):
        return self.session.exec(
            select(User).where(User.email == email)
        ).first()
```

### API Layer

#### Routes (`fastauth/api/auth.py`)
FastAPI router with authentication endpoints.

```python
@router.post("/register")
def register(payload: RegisterRequest, session: Session = Depends(get_session)):
    users = SQLAlchemyUserAdapter(session)
    return create_user(users=users, email=payload.email, password=payload.password)
```

#### Dependencies (`fastauth/api/dependencies.py`)
Reusable dependencies for route protection.

```python
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    # Validate token and return user
```

### Security Components

#### JWT (`fastauth/security/jwt.py`)
- Token creation
- Token validation
- Expiration handling

#### Password Hashing (`fastauth/core/hashing.py`)
- Argon2 hashing
- Password verification

#### Rate Limiting (`fastauth/security/rate_limit.py`)
- Attempt tracking
- Window-based limiting
- Automatic cleanup

### Email Components

#### Email Factory (`fastauth/email/factory.py`)
Selects appropriate email provider based on configuration.

#### Providers
- Console (development)
- SMTP (production)
- SendGrid (planned)
- AWS SES (planned)

## Data Flow

### Registration Flow

```
1. User submits email/password
   ↓
2. API validates input (Pydantic)
   ↓
3. Core checks for existing user (via adapter)
   ↓
4. Core hashes password
   ↓
5. Core creates user (via adapter)
   ↓
6. If email verification required:
   - Generate token
   - Send email
   ↓
7. Return user object
```

### Login Flow

```
1. User submits email/password
   ↓
2. API validates input
   ↓
3. Rate limiter checks attempts
   ↓
4. Core retrieves user (via adapter)
   ↓
5. Core verifies password
   ↓
6. Core checks email verification
   ↓
7. Create access token (JWT)
   ↓
8. Create refresh token (via adapter)
   ↓
9. Return tokens
```

### Token Refresh Flow

```
1. User submits refresh token
   ↓
2. Core validates token hash (via adapter)
   ↓
3. Core checks expiration
   ↓
4. Core revokes old token (via adapter)
   ↓
5. Create new access token
   ↓
6. Create new refresh token (via adapter)
   ↓
7. Return new tokens
```

### Authorization Flow (RBAC)

```
1. User requests protected resource
   ↓
2. Validate access token (get user)
   ↓
3. Check required role/permission (dependency)
   ↓
4. Core retrieves user roles (via adapter)
   ↓
5. Core retrieves role permissions (via adapter)
   ↓
6. Core checks if user has required permission
   ↓
7. If authorized → Execute route
   If unauthorized → Return 403 Forbidden
```

## Security Architecture

### Password Security

**Argon2 Hashing:**
- Industry-recommended algorithm
- Memory-hard (resistant to GPU attacks)
- Configurable cost parameters

**Flow:**
```
Plain Password → Argon2 Hash → Store in Database
```

### Token Security

**JWT Access Tokens:**
- Short-lived (30 minutes default)
- Stateless
- Signed with secret key

**Refresh Tokens:**
- Long-lived (7 days default)
- Stored in database (can be revoked)
- Hashed before storage
- Rotated on use

### Rate Limiting

**Protection Against:**
- Brute force attacks
- Credential stuffing
- DoS attacks

**Implementation:**
```python
limiter = RateLimiter(max_attempts=5, window_seconds=300)
limiter.hit(request.client.host)
```

### Authorization (RBAC)

**Role-Based Access Control:**
- Fine-grained authorization
- Separation of authentication and authorization
- Flexible permission model

**Architecture:**
```
User → [UserRole] → Role → [RolePermission] → Permission
```

**Many-to-Many Relationships:**
- Users can have multiple roles
- Roles can have multiple permissions
- Users inherit all permissions from their roles

**Route Protection:**
```python
# Protect by role
@app.get("/admin", dependencies=[Depends(require_role("admin"))])

# Protect by permission
@app.delete("/users/{id}", dependencies=[Depends(require_permission("delete:users"))])
```

**Permission Check:**
```python
# Check permission programmatically
has_access = check_permission(
    roles=role_adapter,
    user_id=user.id,
    permission_name="delete:users"
)
```

### SQL Injection Protection

All database operations use parameterized queries via SQLModel:

```python
# Safe - parameterized
statement = select(User).where(User.email == email)

# Never do this - vulnerable
query = f"SELECT * FROM users WHERE email = '{email}'"
```

## Extension Points

### Custom Adapters

Implement the adapter interface for any database:

```python
from fastauth.adapters.base import UserAdapter

class MongoDBUserAdapter(UserAdapter):
    def __init__(self, db):
        self.db = db

    def get_by_email(self, email: str):
        return self.db.users.find_one({"email": email})
```

### Custom Email Providers

Implement the email provider interface:

```python
from fastauth.email.base import EmailProvider

class SendGridProvider(EmailProvider):
    def send_verification_email(self, user, token):
        # SendGrid implementation
```

### Custom Routes

Add your own protected routes:

```python
from fastauth.api.dependencies import get_current_user

@app.get("/profile")
def get_profile(current_user = Depends(get_current_user)):
    return {"email": current_user.email}
```

## Testing Architecture

### Unit Tests

Test core logic with mock adapters:

```python
class FakeUserAdapter(UserAdapter):
    def __init__(self):
        self.users = {}

    def create_user(self, email, hashed_password):
        user = User(email=email, hashed_password=hashed_password)
        self.users[email] = user
        return user
```

### Integration Tests

Test with real database (SQLite in memory):

```python
@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
```

### API Tests

Test HTTP endpoints with TestClient:

```python
client = TestClient(app)
response = client.post("/auth/register", json={
    "email": "test@example.com",
    "password": "password123"
})
```

## Performance Considerations

### Database

**Connection Pooling:**
- SQLAlchemy manages connection pools
- Configure pool size for your workload

**Indexes:**
- Email (unique)
- Token hashes (unique)
- User IDs (primary key)

### Caching

**Rate Limiter:**
- In-memory storage (defaultdict)
- Automatic cleanup of old attempts

**Sessions:**
- Database-backed (can be moved to Redis)

### Token Generation

**Secure Random:**
- Uses `secrets` module
- Cryptographically secure

**Hashing:**
- Argon2 is CPU-intensive (by design)
- Balance security with performance

## Configuration

### Settings Management

Pydantic settings with environment variables:

```python
class Settings(BaseSettings):
    jwt_secret_key: str
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env")
```

### Environment-Based

Different settings per environment:

```bash
# Development
EMAIL_PROVIDER=console
REQUIRE_EMAIL_VERIFICATION=false

# Production
EMAIL_PROVIDER=smtp
REQUIRE_EMAIL_VERIFICATION=true
```

## Error Handling

### Exception Hierarchy

```
Exception
├── UserAlreadyExistsError
├── InvalidCredentialsError
├── EmailNotVerifiedError
├── RefreshTokenError
├── PasswordResetError
├── EmailVerificationError
├── RoleNotFoundError
├── PermissionNotFoundError
├── RoleAlreadyExistsError
├── PermissionAlreadyExistsError
├── RateLimitExceeded
└── TokenError
```

### HTTP Error Mapping

```python
try:
    user = authenticate_user(...)
except InvalidCredentialsError:
    raise HTTPException(status_code=401, detail="Invalid credentials")
except EmailNotVerifiedError:
    raise HTTPException(status_code=403, detail="Email not verified")
```

## Deployment Considerations

### Database Migrations

FastAuth doesn't include migrations. Use Alembic:

```bash
alembic init alembic
alembic revision --autogenerate -m "Add FastAuth models"
alembic upgrade head
```

### Secret Management

Never commit secrets:

```bash
# Use environment variables
export JWT_SECRET_KEY=$(openssl rand -hex 32)

# Or secret management service
# AWS Secrets Manager, HashiCorp Vault, etc.
```

### Scaling

**Horizontal Scaling:**
- Stateless API (JWT tokens)
- Database handles state
- Load balancer distributes requests

**Database Scaling:**
- Read replicas for queries
- Write to primary
- Consider separate auth database

## Future Architecture

**Completed:**
- ✅ **RBAC** - Role-based access control with permissions (implemented)

Planned enhancements:

**Multi-Tenancy:**
- Organization context
- Tenant isolation
- Per-tenant settings

**Session Management:**
- Track active sessions
- Device information
- Logout from specific device

**Two-Factor Authentication:**
- TOTP support
- Backup codes
- Trusted devices

**Audit Logging:**
- All auth events
- Suspicious activity detection
- Compliance requirements
