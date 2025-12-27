# FastAuth Roadmap - Detailed Implementation Plan

## Phase 1: Documentation & Polish (PRs #7-11)

### PR #7: Add comprehensive README and quick start guide

**Branch:** `docs/readme-and-quickstart`

**Commits:**
```
📝 docs: add comprehensive README with quick start guide

- Add installation instructions
- Add quick start example
- Add feature overview
- Add architecture diagram
- Add usage examples (basic auth flow)
- Add configuration guide
- Add troubleshooting section
- Add links to examples

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `📝 docs: add comprehensive README and quick start guide`

**PR Description:**
```md
## What
Add comprehensive README.md with installation, quick start, and usage examples.

## Why
- New users need clear documentation to get started
- Shows library capabilities and use cases
- Reduces friction for adoption
- Essential before v0.1.0 release

## Scope
- [ ] Core
- [ ] Adapters
- [ ] API
- [ ] Tests
- [x] Documentation

## Breaking Changes
None

## Content Includes
- Installation instructions (pip, poetry, from source)
- Quick start guide (5-minute setup)
- Feature overview with code examples
- Basic authentication flow example
- Configuration guide (settings, env vars)
- Architecture overview
- Link to examples directory
- Troubleshooting common issues
- Contributing guidelines link
- License information

## Checklist
- [x] Installation section complete
- [x] Quick start guide tested
- [x] Code examples verified
- [x] Links to examples work
- [x] Configuration documented
- [x] Troubleshooting section added
```

---

### PR #8: Add usage examples and demo applications

**Branch:** `docs/usage-examples`

**Commits:**
```
📝 docs: add comprehensive usage examples

- Add OAuth2 password flow example
- Add protected routes example
- Add email verification flow example
- Add password reset flow example
- Add refresh token usage example
- Add custom email provider example
- Update examples README

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add multi-database example application

- Add PostgreSQL example
- Add MySQL example
- Show database-agnostic core usage
- Add docker-compose for local testing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `📝 docs: add comprehensive usage examples and demos`

**PR Description:**
```md
## What
Add comprehensive usage examples covering all major features and use cases.

## Why
- Developers learn by example
- Shows real-world integration patterns
- Demonstrates best practices
- Covers common scenarios

## Scope
- [ ] Core
- [ ] Adapters
- [ ] API
- [ ] Tests
- [x] Documentation
- [x] Examples

## Breaking Changes
None

## Examples Added

### 1. OAuth2 Password Flow (`examples/oauth2-flow/`)
- Complete OAuth2 implementation
- Token-based authentication
- Demonstrates proper security

### 2. Protected Routes (`examples/protected-routes/`)
- Route protection with dependencies
- Role-based access (basic)
- Current user injection

### 3. Email Flows (`examples/email-flows/`)
- Email verification workflow
- Password reset workflow
- Resend verification email

### 4. Custom Email Provider (`examples/custom-email/`)
- Implement custom email backend
- SendGrid integration example
- SMTP configuration example

### 5. Multi-Database (`examples/multi-database/`)
- PostgreSQL setup
- MySQL setup
- SQLite setup (existing)
- Docker Compose for testing

## Checklist
- [x] All examples tested and working
- [x] Each example has its own README
- [x] Docker setup included where applicable
- [x] Requirements documented
- [x] Environment variables documented
```

---

### PR #9: Add CHANGELOG and contributing guidelines

**Branch:** `docs/changelog-and-contributing`

**Commits:**
```
📝 docs: add CHANGELOG for version tracking

- Add CHANGELOG.md following Keep a Changelog format
- Document v0.1.0 initial release
- Add version comparison links

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
📝 docs: add contributing guidelines

- Add CONTRIBUTING.md with development setup
- Add code of conduct
- Add issue templates (bug, feature request)
- Add PR template
- Document commit message conventions
- Add development workflow guide

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `📝 docs: add CHANGELOG and contributing guidelines`

**PR Description:**
```md
## What
Add CHANGELOG.md and comprehensive contributing guidelines.

## Why
- Track version history and changes
- Help contributors understand how to contribute
- Standardize development workflow
- Improve project maintainability

## Scope
- [ ] Core
- [ ] Adapters
- [ ] API
- [ ] Tests
- [x] Documentation
- [x] Project Management

## Breaking Changes
None

## Files Added

### CHANGELOG.md
- Follows [Keep a Changelog](https://keepachangelog.com/) format
- Documents all versions and changes
- Links to version comparisons

### CONTRIBUTING.md
- Development environment setup
- Running tests locally
- Code style guidelines
- Commit message conventions
- PR submission process
- Review process

### CODE_OF_CONDUCT.md
- Community guidelines
- Expected behavior
- Reporting process

### .github/ISSUE_TEMPLATE/
- Bug report template
- Feature request template
- Question template

### .github/pull_request_template.md
- PR checklist
- Required sections
- Testing requirements

## Checklist
- [x] CHANGELOG format validated
- [x] Contributing guide complete
- [x] Issue templates tested
- [x] PR template tested
- [x] Code of conduct added
```

---

### PR #10: Add API documentation and reference

**Branch:** `docs/api-reference`

**Commits:**
```
📝 docs: add API reference documentation

- Document all public classes and functions
- Add docstrings to core modules
- Add docstrings to adapters
- Add docstrings to API routes
- Add type hints throughout

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
📝 docs: add architecture documentation

- Add architecture overview
- Document adapter pattern
- Explain database-agnostic design
- Add component diagrams
- Document security considerations

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `📝 docs: add API reference and architecture documentation`

**PR Description:**
```md
## What
Add comprehensive API reference documentation and architecture guide.

## Why
- Developers need API reference for integration
- Architecture docs help understand design decisions
- Enables extension and customization
- Improves maintainability

## Scope
- [x] Core
- [x] Adapters
- [x] API
- [ ] Tests
- [x] Documentation

## Breaking Changes
None (only adding documentation)

## Documentation Added

### API Reference (`docs/api-reference.md`)
- All public classes documented
- Method signatures with parameters
- Return types and exceptions
- Usage examples for each component

### Architecture Guide (`docs/architecture.md`)
- System overview and design principles
- Adapter pattern explanation
- Database-agnostic architecture
- Component interaction diagrams
- Security architecture
- Extension points

### Module Documentation
- Added docstrings to all public APIs
- Type hints throughout codebase
- Examples in docstrings

## Checklist
- [x] All public APIs documented
- [x] Docstrings added to modules
- [x] Type hints complete
- [x] Architecture diagrams included
- [x] Security considerations documented
```

---

### PR #11: Release preparation and v0.1.0

**Branch:** `release/v0.1.0`

**Commits:**
```
🔖 chore: prepare for v0.1.0 release

- Update version to 0.1.0
- Finalize CHANGELOG for v0.1.0
- Update README with PyPI installation
- Add release notes
- Final documentation review

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `🔖 chore: prepare for v0.1.0 release`

**PR Description:**
```md
## What
Final preparation for v0.1.0 release to PyPI.

## Why
- First public release
- All documentation complete
- CI/CD pipeline ready
- Package tested and validated

## Scope
- [x] Core
- [x] Adapters
- [x] API
- [x] Tests
- [x] Documentation
- [x] Release

## Breaking Changes
None (initial release)

## v0.1.0 Features
- User registration and authentication
- Email verification
- Password reset
- Refresh token management
- Rate limiting
- SQLAlchemy adapter
- FastAPI integration
- Comprehensive test suite (63 tests)
- CI/CD pipeline
- Package distribution

## Pre-Release Checklist
- [x] All tests passing
- [x] Documentation complete
- [x] Examples working
- [x] CHANGELOG updated
- [x] Version numbers updated
- [x] Package builds successfully
- [x] PyPI trusted publishing configured
- [x] README has installation instructions
- [x] License file present
- [x] Code formatted and linted

## Post-Merge Actions
1. Create GitHub release with tag `v0.1.0`
2. Publish to PyPI via workflow
3. Announce release
4. Monitor for issues
```

---

## Phase 2: Essential Features (PRs #12-16)

### PR #12: Add role-based access control (RBAC)

**Branch:** `feat/rbac-system`

**Commits:**
```
✨ feat: add role and permission models

- Add Role model to SQLAlchemy adapter
- Add Permission model
- Add user-role many-to-many relationship
- Add role-permission relationship
- Create database migrations guide

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add role management core logic

- Add assign_role function
- Add remove_role function
- Add check_permission function
- Add get_user_roles function
- Add get_user_permissions function
- Add role adapter interface

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add role-based route protection

- Add require_role dependency
- Add require_permission dependency
- Add require_any_role dependency
- Add require_all_permissions dependency
- Add FastAPI integration

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
🧪 test(rbac): add comprehensive RBAC tests

- Test role assignment/removal
- Test permission checks
- Test route protection
- Test edge cases

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `✨ feat: add role-based access control (RBAC)`

**PR Description:**
```md
## What
Add comprehensive role-based access control system.

## Why
- Essential for multi-user applications
- Enables fine-grained permissions
- Most requested feature
- Industry standard security pattern

## Scope
- [x] Core
- [x] Adapters
- [x] API
- [x] Tests
- [ ] Documentation

## Breaking Changes
- Adds new database models (requires migration)
- User model gets `roles` relationship

## Features

### Models
- `Role`: Named roles (admin, user, moderator, etc.)
- `Permission`: Named permissions (read:users, write:posts, etc.)
- `user_roles`: Many-to-many relationship
- `role_permissions`: Many-to-many relationship

### Core Functions
```python
assign_role(user_id, role_name)
remove_role(user_id, role_name)
check_permission(user_id, permission_name)
get_user_roles(user_id)
get_user_permissions(user_id)
```

### FastAPI Dependencies
```python
@app.get("/admin", dependencies=[Depends(require_role("admin"))])
@app.get("/posts", dependencies=[Depends(require_permission("read:posts"))])
@app.get("/users", dependencies=[Depends(require_any_role(["admin", "moderator"]))])
```

### Adapters
- `RoleAdapter` interface (base)
- `SQLAlchemyRoleAdapter` implementation

## Migration Guide
```python
# Users need to run migrations to add new tables
from fastauth.adapters.sqlalchemy.models import Base
Base.metadata.create_all(engine)
```

## Usage Example
```python
from fastauth import assign_role, require_role

# Assign role
assign_role(user.id, "admin")

# Protect route
@app.get("/admin/users", dependencies=[Depends(require_role("admin"))])
def get_all_users():
    return {"users": [...]}
```

## Checklist
- [x] Role model implemented
- [x] Permission model implemented
- [x] Core logic complete
- [x] SQLAlchemy adapter implemented
- [x] FastAPI dependencies added
- [x] Tests added (role assignment, permissions, routes)
- [x] Migration guide documented
- [ ] README updated with RBAC examples
```

---

### PR #13: Add session management

**Branch:** `feat/session-management`

**Commits:**
```
✨ feat: add session tracking and management

- Add Session model to track active sessions
- Track device, IP, user agent
- Add last_active timestamp
- Add session adapter interface
- Implement SQLAlchemy session adapter

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add session management endpoints

- GET /sessions - list active sessions
- DELETE /sessions/{id} - logout specific session
- DELETE /sessions/all - logout all sessions
- Track last login time on user

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
🧪 test(sessions): add session management tests

- Test session creation on login
- Test listing sessions
- Test logout specific session
- Test logout all sessions
- Test session cleanup

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `✨ feat: add session management and tracking`

**PR Description:**
```md
## What
Add session tracking and management capabilities.

## Why
- Users need to see active sessions
- Security: logout from compromised devices
- Audit trail of login activity
- Better user experience

## Scope
- [x] Core
- [x] Adapters
- [x] API
- [x] Tests
- [ ] Documentation

## Breaking Changes
- Adds Session model (requires migration)
- User model gets `last_login` field

## Features

### Session Tracking
- Device information
- IP address
- User agent
- Last activity timestamp
- Creation timestamp

### API Endpoints
```
GET    /sessions          # List all active sessions
DELETE /sessions/{id}     # Logout specific session
DELETE /sessions/all      # Logout all other sessions
```

### Core Functions
```python
create_session(user_id, device_info)
get_user_sessions(user_id)
revoke_session(session_id)
revoke_all_sessions(user_id, except_current=True)
cleanup_expired_sessions()
```

### Automatic Cleanup
- Background task to remove expired sessions
- Configurable session timeout
- Cleanup on login

## Usage Example
```python
# List sessions
sessions = await get_user_sessions(user.id)

# Logout from specific device
await revoke_session(session_id)

# Logout from all other devices
await revoke_all_sessions(user.id, except_current=True)
```

## Checklist
- [x] Session model implemented
- [x] Session tracking on login
- [x] List sessions endpoint
- [x] Logout specific session
- [x] Logout all sessions
- [x] Expired session cleanup
- [x] Tests added
- [ ] Documentation updated
```

---

### PR #14: Add account management features

**Branch:** `feat/account-management`

**Commits:**
```
✨ feat: add change password while authenticated

- Add change_password endpoint
- Require current password verification
- Add change password core logic
- Invalidate all sessions on password change

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add change email functionality

- Add change email request endpoint
- Send verification to new email
- Add confirm email change endpoint
- Update user email after verification

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add account deletion

- Add delete account endpoint
- Require password confirmation
- Add soft delete option
- Add hard delete option
- Cleanup associated data

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
🧪 test(account): add account management tests

- Test password change
- Test email change flow
- Test account deletion
- Test authorization requirements

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `✨ feat: add account management features`

**PR Description:**
```md
## What
Add account management endpoints for authenticated users.

## Why
- Users need to manage their accounts
- Common feature in production apps
- Security best practices (password rotation)
- GDPR compliance (account deletion)

## Scope
- [x] Core
- [x] Adapters
- [x] API
- [x] Tests
- [ ] Documentation

## Breaking Changes
- User model gets `deleted_at` field for soft deletes (optional)

## Features

### Change Password
```
POST /account/change-password
Body: {
  "current_password": "old",
  "new_password": "new"
}
```
- Requires current password
- Invalidates all sessions except current
- Sends email notification

### Change Email
```
POST /account/change-email
Body: { "new_email": "new@example.com" }

POST /account/confirm-email-change
Body: { "token": "..." }
```
- Sends verification to new email
- Old email remains until confirmed
- Notification to old email

### Account Deletion
```
DELETE /account
Body: { "password": "..." }
```
- Requires password confirmation
- Soft delete (set deleted_at) or hard delete
- Cleanup: sessions, tokens, reset codes
- Optional data retention period

### Account Settings
```
GET /account/settings
PUT /account/settings
```
- Update preferences
- Notification settings
- Privacy settings

## Security Considerations
- All endpoints require authentication
- Password confirmation for sensitive actions
- Email notifications for security events
- Rate limiting on sensitive endpoints

## Checklist
- [x] Change password implemented
- [x] Change email implemented
- [x] Account deletion implemented
- [x] Settings endpoints added
- [x] Security notifications
- [x] Tests added
- [ ] Documentation updated
```

---

## Phase 3: Security Enhancements (PRs #15-17)

### PR #15: Add two-factor authentication (2FA)

**Branch:** `feat/two-factor-auth`

**Commits:**
```
✨ feat: add TOTP 2FA support

- Add TwoFactorAuth model
- Add TOTP secret generation
- Add QR code generation
- Add 2FA enable/disable endpoints
- Add backup codes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: integrate 2FA into login flow

- Check 2FA requirement on login
- Add 2FA verification endpoint
- Add "remember this device" option
- Add trusted device management

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
🧪 test(2fa): add comprehensive 2FA tests

- Test TOTP generation and verification
- Test backup codes
- Test login with 2FA
- Test device trust

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `✨ feat: add two-factor authentication (2FA/TOTP)`

**PR Description:**
```md
## What
Add TOTP-based two-factor authentication support.

## Why
- Critical security feature for enterprise apps
- Industry standard (RFC 6238)
- Protects against password compromise
- Common user expectation

## Scope
- [x] Core
- [x] Adapters
- [x] API
- [x] Tests
- [ ] Documentation

## Breaking Changes
None (optional feature)

## Features

### TOTP Support
- Generate TOTP secrets
- QR code generation for authenticator apps
- Verify TOTP codes
- Compatible with Google Authenticator, Authy, etc.

### Backup Codes
- Generate 10 single-use backup codes
- Use when authenticator unavailable
- Regenerate after use

### API Endpoints
```
POST   /2fa/enable         # Enable 2FA, returns QR code
POST   /2fa/verify-setup   # Verify TOTP to complete setup
POST   /2fa/disable        # Disable 2FA
GET    /2fa/backup-codes   # Get new backup codes
POST   /auth/verify-2fa    # Submit TOTP during login
```

### Login Flow
1. Username/password login
2. If 2FA enabled, return `requires_2fa: true`
3. User submits TOTP code
4. Issue tokens if valid

### Trusted Devices
- "Remember this device for 30 days" option
- Device fingerprinting
- Manage trusted devices

## Dependencies
```python
pyotp>=2.9.0      # TOTP implementation
qrcode>=7.4.0     # QR code generation
```

## Usage Example
```python
# Enable 2FA
response = await enable_2fa(user_id)
# Returns: { "secret": "...", "qr_code": "data:image/png;base64,..." }

# User scans QR code in authenticator app

# Verify setup
await verify_2fa_setup(user_id, totp_code)

# Login with 2FA
tokens = await login(email, password)
if tokens.requires_2fa:
    await verify_2fa(tokens.session_id, totp_code)
```

## Checklist
- [x] TOTP implementation
- [x] QR code generation
- [x] Backup codes
- [x] Login integration
- [x] Trusted devices
- [x] Tests added
- [ ] Documentation updated
- [ ] Example app updated
```

---

### PR #16: Add account lockout protection

**Branch:** `feat/account-lockout`

**Commits:**
```
✨ feat: add account lockout after failed attempts

- Track failed login attempts per user
- Lock account after N failures
- Add configurable lockout duration
- Add exponential backoff option

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add admin unlock functionality

- Add unlock account endpoint (admin only)
- Add automatic unlock after timeout
- Send email notification on lockout
- Add lockout history

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
🧪 test(lockout): add account lockout tests

- Test lockout after max attempts
- Test automatic unlock
- Test admin unlock
- Test lockout notifications

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `✨ feat: add account lockout protection`

**PR Description:**
```md
## What
Add account lockout protection against brute force attacks.

## Why
- Protect against password guessing
- OWASP security recommendation
- Compliance requirement (SOC2, etc.)
- Reduce automated attacks

## Scope
- [x] Core
- [x] Adapters
- [x] API
- [x] Tests
- [ ] Documentation

## Breaking Changes
- User model gets lockout-related fields

## Features

### Lockout Triggers
- Lock after N failed login attempts (configurable)
- Failed 2FA attempts also count
- Separate counters for login vs 2FA

### Lockout Duration
- Fixed duration (e.g., 30 minutes)
- Exponential backoff (1st: 5min, 2nd: 15min, 3rd: 1hr)
- Permanent lockout (requires admin)

### Configuration
```python
# settings.py
LOCKOUT_ENABLED = True
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30
LOCKOUT_BACKOFF_STRATEGY = "exponential"  # or "fixed"
```

### Admin Features
```
POST /admin/users/{id}/unlock  # Unlock account
GET  /admin/users/{id}/lockout-history
```

### Notifications
- Email user on lockout
- Email on successful unlock
- Alert on repeated lockouts

### User Model Fields
```python
failed_login_attempts: int
locked_until: datetime | None
lockout_count: int  # Total times locked
last_failed_attempt: datetime | None
```

## Security Notes
- Rate limiting still applies (different layer)
- Lockout is per-user, rate limit is per-IP
- Admin accounts have stricter limits
- CAPTCHA after 2 failed attempts (future PR)

## Checklist
- [x] Lockout logic implemented
- [x] Configurable settings
- [x] Admin unlock endpoint
- [x] Email notifications
- [x] Lockout history tracking
- [x] Tests added
- [ ] Documentation updated
```

---

### PR #17: Add security audit logging

**Branch:** `feat/audit-logging`

**Commits:**
```
✨ feat: add security audit log system

- Add AuditLog model
- Track login attempts (success/failure)
- Track password changes
- Track email changes
- Track 2FA events
- Track role changes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add audit log query endpoints

- GET /audit-logs - query logs
- Filter by user, event type, date range
- Export logs to JSON/CSV
- Admin-only access

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add suspicious activity detection

- Detect login from new location
- Detect login from new device
- Detect multiple failed attempts
- Send alerts on suspicious events

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
🧪 test(audit): add audit logging tests

- Test event logging
- Test log querying
- Test suspicious activity detection
- Test export functionality

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `✨ feat: add security audit logging and monitoring`

**PR Description:**
```md
## What
Add comprehensive security audit logging and suspicious activity detection.

## Why
- Compliance requirements (SOC2, HIPAA, GDPR)
- Security monitoring and forensics
- Detect compromised accounts
- User activity transparency

## Scope
- [x] Core
- [x] Adapters
- [x] API
- [x] Tests
- [ ] Documentation

## Breaking Changes
None (audit logging is automatic)

## Features

### Audit Events
- `login_success` - Successful login
- `login_failure` - Failed login attempt
- `logout` - User logout
- `password_changed` - Password update
- `email_changed` - Email update
- `2fa_enabled` - 2FA activated
- `2fa_disabled` - 2FA deactivated
- `role_assigned` - Role granted
- `role_removed` - Role revoked
- `account_locked` - Account locked
- `account_unlocked` - Account unlocked
- `account_deleted` - Account removed

### Audit Log Model
```python
class AuditLog:
    id: UUID
    user_id: UUID | None
    event_type: str
    event_data: dict  # JSON metadata
    ip_address: str
    user_agent: str
    created_at: datetime
```

### Query API
```
GET /audit-logs?user_id={id}&event_type={type}&from={date}&to={date}
GET /audit-logs/export?format=csv
```

### Suspicious Activity Detection
- New location login (geo-IP)
- New device login
- Multiple failed attempts
- After-hours access (configurable)
- Simultaneous logins from different locations

### Alerts
- Email user on suspicious activity
- Admin notifications
- Webhook integration for SIEM

### Retention
- Configurable retention period
- Automatic cleanup of old logs
- Archive to external storage

## Usage Example
```python
# Query logs
logs = await get_audit_logs(
    user_id=user.id,
    event_type="login_success",
    from_date="2024-01-01",
    to_date="2024-01-31"
)

# Export logs
csv_data = await export_audit_logs(format="csv")
```

## Checklist
- [x] Audit log model implemented
- [x] Event tracking integrated
- [x] Query API implemented
- [x] Export functionality
- [x] Suspicious activity detection
- [x] Alert system
- [x] Tests added
- [ ] Documentation updated
```

---

## Phase 4: Provider Integrations (PRs #18-21)

### PR #18: Add OAuth2 social login support

**Branch:** `feat/oauth2-social-login`

**Commits:**
```
✨ feat: add OAuth2 provider framework

- Add OAuth2Provider base class
- Add OAuth2 state management
- Add callback handler
- Add user account linking

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add Google OAuth2 provider

- Implement Google OAuth2
- Handle user info retrieval
- Support email verification via Google
- Add example configuration

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add GitHub OAuth2 provider

- Implement GitHub OAuth2
- Handle user info retrieval
- Support email scope
- Add example configuration

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
🧪 test(oauth2): add OAuth2 integration tests

- Test Google OAuth2 flow
- Test GitHub OAuth2 flow
- Test account linking
- Test error handling

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `✨ feat: add OAuth2 social login (Google, GitHub)`

**PR Description:**
```md
## What
Add OAuth2 social login support with Google and GitHub providers.

## Why
- Modern authentication expectation
- Reduce signup friction
- Better user experience
- Popular feature request

## Scope
- [x] Core
- [x] Adapters
- [x] API
- [x] Tests
- [ ] Documentation

## Breaking Changes
- Adds OAuth2Account model (requires migration)
- User model gets `oauth_accounts` relationship

## Features

### Supported Providers
- Google OAuth2
- GitHub OAuth2
- Generic OAuth2 (customizable)

### OAuth2 Flow
```
GET  /auth/oauth/{provider}           # Initiate OAuth
GET  /auth/oauth/{provider}/callback  # Handle callback
POST /auth/oauth/link                 # Link to existing account
POST /auth/oauth/unlink               # Unlink account
```

### Account Linking
- Link OAuth to existing email account
- Multiple OAuth providers per user
- Unlink providers

### Models
```python
class OAuth2Account:
    user_id: UUID
    provider: str  # "google", "github"
    provider_user_id: str
    access_token: str (encrypted)
    refresh_token: str (encrypted)
    expires_at: datetime
```

### Configuration
```python
# Google
GOOGLE_CLIENT_ID = "..."
GOOGLE_CLIENT_SECRET = "..."
GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/oauth/google/callback"

# GitHub
GITHUB_CLIENT_ID = "..."
GITHUB_CLIENT_SECRET = "..."
GITHUB_REDIRECT_URI = "http://localhost:8000/auth/oauth/github/callback"
```

### Usage Example
```python
# Initiate OAuth
@app.get("/auth/oauth/google")
async def google_login():
    return await oauth_providers.google.authorize_redirect(request)

# Handle callback
@app.get("/auth/oauth/google/callback")
async def google_callback(code: str):
    user_info = await oauth_providers.google.get_user_info(code)
    user = await link_or_create_user(user_info)
    return create_tokens(user)
```

## Dependencies
```python
authlib>=1.3.0  # OAuth2 client
httpx>=0.27.0   # HTTP client
```

## Checklist
- [x] OAuth2 framework implemented
- [x] Google provider implemented
- [x] GitHub provider implemented
- [x] Account linking implemented
- [x] State validation (CSRF protection)
- [x] Token encryption
- [x] Tests added
- [ ] Documentation updated
- [ ] Example app updated
```

---

### PR #19: Add email provider integrations

**Branch:** `feat/email-providers`

**Commits:**
```
✨ feat: add SendGrid email provider

- Implement SendGrid adapter
- Support templates
- Support attachments
- Add retry logic

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add Resend email provider

- Implement Resend adapter
- Support React email templates
- Modern API integration

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add AWS SES email provider

- Implement AWS SES adapter
- Support IAM roles
- Support configuration sets

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
🧪 test(email): add email provider tests

- Test SendGrid integration
- Test Resend integration
- Test AWS SES integration
- Mock external APIs

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `✨ feat: add email provider integrations (SendGrid, Resend, AWS SES)`

**PR Description:**
```md
## What
Add production-ready email provider integrations.

## Why
- Console and SMTP are not production-ready
- Users need reliable email delivery
- Popular email services integration
- Template support

## Scope
- [ ] Core
- [x] Adapters
- [ ] API
- [x] Tests
- [ ] Documentation

## Breaking Changes
None (additional providers only)

## Providers Added

### SendGrid
- Full API integration
- Template support
- Attachment support
- Retry with exponential backoff
- Webhook handling for bounces/complaints

### Resend
- Modern, developer-friendly API
- React email templates
- Simple configuration
- Fast delivery

### AWS SES
- Enterprise-grade reliability
- IAM role support
- Configuration sets
- Bounce/complaint handling

### Mailgun (Bonus)
- EU region support
- Template variables
- Tracking and analytics

## Configuration

### SendGrid
```python
EMAIL_PROVIDER = "sendgrid"
SENDGRID_API_KEY = "..."
SENDGRID_FROM_EMAIL = "noreply@example.com"
```

### Resend
```python
EMAIL_PROVIDER = "resend"
RESEND_API_KEY = "..."
RESEND_FROM_EMAIL = "noreply@example.com"
```

### AWS SES
```python
EMAIL_PROVIDER = "ses"
AWS_REGION = "us-east-1"
AWS_ACCESS_KEY_ID = "..."
AWS_SECRET_ACCESS_KEY = "..."
SES_FROM_EMAIL = "noreply@example.com"
```

## Usage Example
```python
# Automatic selection based on settings
email_provider = email_factory.get_provider()

# Or explicit
from fastauth.email.sendgrid import SendGridEmailProvider
email_provider = SendGridEmailProvider()

await email_provider.send_verification_email(user, token)
```

## Dependencies
```python
# Optional dependencies
sendgrid>=6.11.0
resend>=2.0.0
boto3>=1.34.0  # For AWS SES
```

## Checklist
- [x] SendGrid provider implemented
- [x] Resend provider implemented
- [x] AWS SES provider implemented
- [x] Template support
- [x] Error handling and retries
- [x] Tests added
- [ ] Documentation updated
```

---

### PR #20: Add MongoDB adapter

**Branch:** `feat/mongodb-adapter`

**Commits:**
```
✨ feat: add MongoDB adapter for users

- Implement MongoDBUserAdapter
- Add user CRUD operations
- Use Motor for async support

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add MongoDB adapters for tokens

- Implement MongoDBRefreshTokenAdapter
- Implement MongoDBPasswordResetAdapter
- Implement MongoDBEmailVerificationAdapter

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
🧪 test(mongodb): add MongoDB adapter tests

- Test user operations
- Test token operations
- Use pytest-asyncio
- Mock MongoDB in tests

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `✨ feat: add MongoDB adapter`

**PR Description:**
```md
## What
Add MongoDB adapter implementation for all data models.

## Why
- NoSQL database option
- Popular for modern apps
- Flexible schema
- Scalability

## Scope
- [ ] Core
- [x] Adapters
- [ ] API
- [x] Tests
- [ ] Documentation

## Breaking Changes
None (additional adapter only)

## Features

### Adapters Implemented
- `MongoDBUserAdapter`
- `MongoDBRefreshTokenAdapter`
- `MongoDBPasswordResetAdapter`
- `MongoDBEmailVerificationAdapter`
- `MongoDBRoleAdapter`
- `MongoDBSessionAdapter`

### Collections
```
users
refresh_tokens
password_reset_tokens
email_verification_tokens
roles
sessions
audit_logs
```

### Async Support
- Uses Motor (async MongoDB driver)
- Compatible with FastAPI async endpoints
- Connection pooling

## Configuration
```python
from motor.motor_asyncio import AsyncIOMotorClient
from fastauth.adapters.mongodb import MongoDBUserAdapter

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.fastauth

user_adapter = MongoDBUserAdapter(db)
```

## Example Usage
```python
from fastapi import FastAPI, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from fastauth.adapters.mongodb import (
    MongoDBUserAdapter,
    MongoDBRefreshTokenAdapter,
)

app = FastAPI()
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.fastauth

def get_user_adapter():
    return MongoDBUserAdapter(db)

@app.post("/register")
async def register(
    email: str,
    password: str,
    users: MongoDBUserAdapter = Depends(get_user_adapter)
):
    # Implementation
    pass
```

## Dependencies
```python
motor>=3.3.0  # Async MongoDB driver
```

## Indexes
Automatically creates indexes for:
- `users.email` (unique)
- `refresh_tokens.token_hash` (unique)
- `refresh_tokens.user_id`
- `sessions.user_id`

## Checklist
- [x] All adapters implemented
- [x] Async support
- [x] Indexes configured
- [x] Tests added
- [ ] Documentation updated
- [ ] Example app added
```

---

## Phase 5: Advanced Features (PRs #21-24)

### PR #21: Add magic link authentication

**Branch:** `feat/magic-link-auth`

**Commits:**
```
✨ feat: add magic link passwordless authentication

- Add magic link generation
- Add magic link token model
- Add magic link verification endpoint
- Send magic link via email

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
🧪 test(magic-link): add magic link tests

- Test link generation
- Test link verification
- Test expiration
- Test single use

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `✨ feat: add magic link passwordless authentication`

**PR Description:**
```md
## What
Add magic link passwordless authentication.

## Why
- Modern authentication method
- Improved UX (no password to remember)
- Reduces password-related support
- Popular for B2B apps

## Scope
- [x] Core
- [x] Adapters
- [x] API
- [x] Tests
- [ ] Documentation

## Breaking Changes
None (optional feature)

## Features

### Magic Link Flow
1. User enters email
2. System sends magic link
3. User clicks link
4. Automatically logged in

### API Endpoints
```
POST /auth/magic-link/request   # Request magic link
GET  /auth/magic-link/verify    # Verify and login
```

### Configuration
```python
MAGIC_LINK_ENABLED = True
MAGIC_LINK_EXPIRY_MINUTES = 15
MAGIC_LINK_SINGLE_USE = True
```

### Security
- Links expire after N minutes
- Single-use tokens
- Rate limiting on requests
- IP binding (optional)

## Usage Example
```python
# Request magic link
await request_magic_link(email="user@example.com")
# Sends email with link: https://app.com/auth/magic-link/verify?token=...

# Verify and login
tokens = await verify_magic_link(token)
# Returns access and refresh tokens
```

## Checklist
- [x] Magic link generation
- [x] Email sending
- [x] Verification endpoint
- [x] Expiration handling
- [x] Single-use enforcement
- [x] Tests added
- [ ] Documentation updated
```

---

### PR #22: Add API key management

**Branch:** `feat/api-key-management`

**Commits:**
```
✨ feat: add API key model and generation

- Add APIKey model
- Generate secure API keys
- Hash keys before storage
- Add expiration support

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add API key management endpoints

- Create API key
- List API keys
- Revoke API key
- Add scoped permissions

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add API key authentication dependency

- Add require_api_key dependency
- Validate API key from header
- Check permissions
- Rate limit per key

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
🧪 test(api-keys): add API key tests

- Test key generation
- Test key validation
- Test permissions
- Test revocation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `✨ feat: add API key management system`

**PR Description:**
```md
## What
Add API key management for machine-to-machine authentication.

## Why
- Service-to-service authentication
- Integration with third-party tools
- Programmatic access
- Alternative to OAuth2

## Scope
- [x] Core
- [x] Adapters
- [x] API
- [x] Tests
- [ ] Documentation

## Breaking Changes
None (new feature)

## Features

### API Key Model
```python
class APIKey:
    id: UUID
    user_id: UUID
    name: str  # "Production API", "Dev Testing"
    key_prefix: str  # "fauth_live_"
    key_hash: str  # Hashed key
    permissions: list[str]  # ["read:users", "write:posts"]
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime
```

### API Endpoints
```
POST   /api-keys          # Create new key
GET    /api-keys          # List all keys
DELETE /api-keys/{id}     # Revoke key
POST   /api-keys/{id}/rotate  # Rotate key
```

### Key Format
```
fauth_live_1234567890abcdef1234567890abcdef
│     │    │
│     │    └─ Random secure token
│     └────── Environment (live/test)
└──────────── Prefix
```

### Authentication
```python
from fastapi import Depends
from fastauth.api.dependencies import require_api_key

@app.get("/api/users", dependencies=[Depends(require_api_key)])
async def get_users(api_key: APIKey = Depends(require_api_key)):
    # api_key object available
    pass

# With permission check
@app.get("/api/admin")
async def admin_endpoint(
    api_key: APIKey = Depends(require_api_key(["admin:access"]))
):
    pass
```

### Scoped Permissions
```python
# Create key with specific permissions
key = await create_api_key(
    user_id=user.id,
    name="Analytics Service",
    permissions=["read:analytics", "read:users"]
)
```

### Rate Limiting
- Per-key rate limiting
- Different limits for different keys
- Usage tracking

## Security
- Keys are hashed before storage (only shown once)
- Optional expiration dates
- Prefix for easy identification
- Revocation support
- Audit logging

## Checklist
- [x] API key model implemented
- [x] Secure key generation
- [x] Management endpoints
- [x] Authentication dependency
- [x] Scoped permissions
- [x] Rate limiting per key
- [x] Tests added
- [ ] Documentation updated
```

---

### PR #23: Add multi-tenancy support

**Branch:** `feat/multi-tenancy`

**Commits:**
```
✨ feat: add organization/workspace model

- Add Organization model
- Add organization-user relationship
- Add workspace isolation
- Add tenant context middleware

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add organization management endpoints

- Create organization
- List organizations
- Update organization
- Delete organization
- Manage members

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
✨ feat: add per-tenant settings and roles

- Organization-specific roles
- Tenant-scoped permissions
- Per-org settings

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
🧪 test(multi-tenancy): add multi-tenancy tests

- Test org creation
- Test member management
- Test tenant isolation
- Test permissions

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Title:** `✨ feat: add multi-tenancy support (organizations/workspaces)`

**PR Description:**
```md
## What
Add multi-tenancy support with organizations and workspaces.

## Why
- SaaS applications requirement
- Team collaboration
- B2B product enabler
- Common enterprise feature

## Scope
- [x] Core
- [x] Adapters
- [x] API
- [x] Tests
- [ ] Documentation

## Breaking Changes
- Users can belong to multiple organizations
- Requires organization context for most operations

## Features

### Models
```python
class Organization:
    id: UUID
    name: str
    slug: str  # Unique URL-friendly name
    owner_id: UUID
    settings: dict
    created_at: datetime

class OrganizationMember:
    organization_id: UUID
    user_id: UUID
    role: str  # "owner", "admin", "member"
    joined_at: datetime
```

### API Endpoints
```
POST   /organizations              # Create org
GET    /organizations              # List user's orgs
GET    /organizations/{slug}       # Get org details
PUT    /organizations/{slug}       # Update org
DELETE /organizations/{slug}       # Delete org

POST   /organizations/{slug}/members     # Invite member
GET    /organizations/{slug}/members     # List members
DELETE /organizations/{slug}/members/{id} # Remove member
PUT    /organizations/{slug}/members/{id} # Update role
```

### Tenant Context
```python
from fastauth.api.dependencies import get_current_org

@app.get("/api/projects")
async def get_projects(
    org: Organization = Depends(get_current_org)
):
    # All operations scoped to this org
    return get_projects_for_org(org.id)
```

### Organization Roles
- `owner` - Full control
- `admin` - Manage members, settings
- `member` - Basic access
- Custom roles per organization

### Tenant Isolation Strategies
1. **Subdomain**: `acme.app.com`, `widgets.app.com`
2. **Path**: `app.com/acme`, `app.com/widgets`
3. **Header**: `X-Organization: acme`

### Per-Org Settings
```python
# Different settings per organization
org.settings = {
    "require_2fa": True,
    "password_policy": "strong",
    "session_timeout": 3600,
}
```

## Migration Considerations
- Existing data needs org assignment
- Default org created for existing users
- Personal workspace option

## Usage Example
```python
# Create organization
org = await create_organization(
    name="Acme Corp",
    slug="acme",
    owner_id=user.id
)

# Add member
await add_member(
    org_id=org.id,
    user_id=new_user.id,
    role="admin"
)

# Access with tenant context
@app.get("/projects")
async def get_projects(
    org: Organization = Depends(get_current_org)
):
    return await get_org_projects(org.id)
```

## Checklist
- [x] Organization model implemented
- [x] Member management
- [x] Tenant context middleware
- [x] Organization-scoped roles
- [x] Per-org settings
- [x] Tenant isolation
- [x] Tests added
- [ ] Documentation updated
- [ ] Migration guide
```

---

## Summary Table

| Phase | PR # | Feature | Priority | Complexity | Dependencies |
|-------|------|---------|----------|------------|--------------|
| **1** | #7 | README & Quick Start | Critical | Low | None |
| **1** | #8 | Usage Examples | Critical | Low | None |
| **1** | #9 | CHANGELOG & Contributing | High | Low | None |
| **1** | #10 | API Docs & Architecture | High | Medium | None |
| **1** | #11 | v0.1.0 Release | Critical | Low | PRs #7-10 |
| **2** | #12 | RBAC System | High | High | v0.1.0 |
| **2** | #13 | Session Management | High | Medium | v0.1.0 |
| **2** | #14 | Account Management | High | Medium | v0.1.0 |
| **3** | #15 | Two-Factor Auth | High | High | v0.1.0 |
| **3** | #16 | Account Lockout | High | Medium | v0.1.0 |
| **3** | #17 | Audit Logging | High | High | v0.1.0 |
| **4** | #18 | OAuth2 Social Login | Medium | High | v0.1.0 |
| **4** | #19 | Email Providers | Medium | Medium | v0.1.0 |
| **4** | #20 | MongoDB Adapter | Medium | Medium | v0.1.0 |
| **5** | #21 | Magic Link Auth | Low | Medium | v0.1.0 |
| **5** | #22 | API Key Management | Medium | Medium | v0.1.0 |
| **5** | #23 | Multi-Tenancy | Medium | High | #12 (RBAC) |

## Recommended Execution Order

1. **Complete Phase 1 first** (PRs #7-11) - Get to v0.1.0
2. **Pick features based on your use case:**
   - Building SaaS? → RBAC (#12), Multi-tenancy (#23)
   - Need security? → 2FA (#15), Audit Logging (#17)
   - Want growth? → OAuth2 (#18), Magic Links (#21)

## Version Milestones

- **v0.1.0** - Initial release (current + Phase 1)
- **v0.2.0** - Essential features (Phase 2)
- **v0.3.0** - Security enhancements (Phase 3)
- **v0.4.0** - Provider integrations (Phase 4)
- **v0.5.0** - Advanced features (Phase 5)
- **v1.0.0** - Stable API, production ready
