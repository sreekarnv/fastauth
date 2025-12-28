# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Role-Based Access Control (RBAC) system
  - Role and Permission models for fine-grained authorization
  - `require_role()` and `require_permission()` FastAPI dependencies for route protection
  - Core functions for role/permission management (create_role, assign_role, check_permission, etc.)
  - SQLAlchemy adapter for RBAC operations (SQLAlchemyRoleAdapter)
  - Support for many-to-many user-role and role-permission relationships
  - 47 comprehensive tests for RBAC functionality (110 total tests)
- Session Management system
  - Session model to track active user sessions with device info, IP address, and user agent
  - SessionAdapter interface and SQLAlchemySessionAdapter implementation
  - Automatic session creation on login and registration
  - `last_login` timestamp tracking on User model
  - Core functions for session management (create_session, get_user_sessions, delete_session, cleanup_inactive_sessions)
  - REST API endpoints for session management:
    - `GET /sessions` - List all active sessions for authenticated user
    - `DELETE /sessions/all` - Delete all user sessions
    - `DELETE /sessions/{session_id}` - Delete specific session
  - Session activity tracking and automated cleanup of inactive sessions
  - Full authorization controls - users can only manage their own sessions
  - 36 comprehensive tests for session functionality (146 total tests)

### Fixed
- UUID conversion bug in `get_current_user()` dependency (was passing string to SQLAlchemy, now converts to UUID)

## [0.1.0] - 2024-12-27

### Added
- Initial release of FastAuth
- User registration and authentication
- Email verification with token-based workflow
- Password reset functionality
- Refresh token support with automatic rotation
- JWT-based access tokens
- Rate limiting for authentication endpoints
- SQLAlchemy adapter for database operations
- Database-agnostic core architecture
- FastAPI router with all auth endpoints
- Argon2 password hashing
- Pydantic settings management
- Console and SMTP email providers
- Comprehensive test suite (63 tests)
- CI/CD pipeline with GitHub Actions
- Pre-commit hooks (Black, Ruff)
- Package distribution (wheel and sdist)
- Basic example application
- Complete documentation

### Security
- Argon2 password hashing (OWASP recommended)
- JWT token expiration and validation
- Refresh token rotation on use
- Rate limiting protection
- SQL injection protection via parameterized queries

[unreleased]: https://github.com/sreekarnv/fastauth/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sreekarnv/fastauth/releases/tag/v0.1.0
