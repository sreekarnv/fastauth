# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- OAuth 2.0 authentication framework
  - OAuth provider integration with state management
  - Google OAuth provider with PKCE (Proof Key for Code Exchange) support
  - OAuth account linking and unlinking functionality
  - OAuthAccountAdapter and OAuthStateAdapter interfaces
  - SQLAlchemyOAuthAccountAdapter and SQLAlchemyOAuthStateAdapter implementations
  - Secure state token generation and validation with expiration
  - Core functions for OAuth flows (initiate_oauth_flow, complete_oauth_flow, get_linked_accounts, unlink_oauth_account)
  - REST API endpoints for OAuth:
    - `POST /oauth/{provider}/authorize` - Initiate OAuth flow
    - `POST /oauth/{provider}/callback` - Complete OAuth authentication
    - `GET /oauth/accounts` - List linked OAuth accounts
    - `DELETE /oauth/accounts/{account_id}` - Unlink OAuth account
  - OAuthAccount and OAuthState models for OAuth data persistence
  - OAuth-specific schemas (OAuthAuthorizeRequest, OAuthCallbackRequest, OAuthAccountResponse, etc.)
  - httpx dependency for OAuth provider HTTP requests
  - Extensible provider system for adding new OAuth providers
  - 17 comprehensive tests for OAuth flows and security (195 total tests)
- Comprehensive test reporting infrastructure
  - Timestamped test report folders (test-results/YYYYMMDD_HHMMSS/)
  - Multiple report formats: HTML (interactive), JUnit XML (CI/CD), detailed logs
  - Coverage reports (HTML + XML) automatically organized in timestamped folders
  - pytest-html integration for rich HTML test reports
  - Poetry scripts for convenient test execution:
    - `poetry run test` - Run tests
    - `poetry run test-cov` - Run tests with full coverage reporting
  - Reorganized test scripts into scripts/ package (scripts/test_with_coverage.py)
  - TEST_COMMANDS.md developer reference guide
  - Enhanced pytest configuration with verbose output and strict markers
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
- Account Management features
  - Change password endpoint with current password verification
  - Account deletion with soft delete (deactivation) and hard delete (permanent removal) options
  - Email change with token-based verification flow
  - Password verification requirement for all sensitive operations
  - Automatic session invalidation on password change and account deletion
  - EmailChangeAdapter interface and SQLAlchemyEmailChangeAdapter implementation
  - Core functions for account management (change_password, delete_account, request_email_change, confirm_email_change)
  - REST API endpoints for account management:
    - `POST /account/change-password` - Change password while authenticated
    - `DELETE /account/delete` - Delete account with soft/hard delete options
    - `POST /account/request-email-change` - Request email change with verification token
    - `POST /account/confirm-email-change` - Confirm email change with token
  - Extended UserAdapter with update_email(), soft_delete_user(), hard_delete_user() methods
  - Added deleted_at field to User model for soft delete support
  - EmailChangeToken model for email change verification
  - 32 comprehensive tests for account management (178 total tests)

### Fixed
- UUID conversion bug in `get_current_user()` dependency (was passing string to SQLAlchemy, now converts to UUID)
- ResourceWarnings from unclosed database connections in tests (reduced from 101 to 4 warnings by properly disposing SQLAlchemy engines)

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
