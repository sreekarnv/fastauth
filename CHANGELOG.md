# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.2] - 2026-01-04

### Fixed
- OAuth API endpoint path parameter naming inconsistency
  - Changed function parameter from `provider_name` to `provider` to match route path `/{provider}/`
  - Fixes 422 validation errors when calling OAuth endpoints
  - Affected endpoints: `/oauth/{provider}/authorize`, `/oauth/{provider}/callback`, `/oauth/{provider}/unlink`
- OAuth SessionMiddleware handling
  - Added graceful fallback when SessionMiddleware is not configured
  - Prevents AssertionError crashes in OAuth authorize endpoint
  - PKCE code_verifier now conditionally stored only when session is available

### Changed
- Improved test coverage from 85% to 99% (1512/1519 lines covered)
  - Added 21 new tests across 7 new test files (291 total tests, up from 270)
  - Enhanced 3 existing test files with comprehensive edge case coverage
  - 52 out of 58 files now have 100% test coverage

### Added
- Comprehensive OAuth endpoint tests (tests/api/test_oauth.py)
  - 16 tests covering authorization, callback, account linking/unlinking flows
  - Tests for state validation, CSRF protection, and error handling
  - SessionMiddleware integration tests
- API dependency error path tests (tests/api/test_dependencies.py)
  - 6 tests for token validation, user authentication edge cases
  - Tests for invalid tokens, missing payload, inactive users
- OAuth adapter tests
  - tests/adapters/sqlalchemy/test_oauth_account_adapter.py (11 tests)
  - tests/adapters/sqlalchemy/test_oauth_state_adapter.py (9 tests)
  - Full CRUD coverage with timezone handling for SQLite compatibility
- OAuth provider tests (tests/providers/test_google_provider.py)
  - 15 tests for Google OAuth provider implementation
  - Token exchange, user info retrieval, refresh token flows
  - PKCE and authorization URL generation tests
- Email provider tests (tests/email_providers/test_email_providers.py)
  - 9 tests for console and SMTP email clients
  - Factory pattern and configuration tests
- Enhanced auth endpoint tests (tests/api/test_auth_endpoints.py)
  - 18 tests for rate limiting, token refresh, logout
  - Email verification and password reset flow tests
- Core OAuth edge case tests (tests/core/test_oauth.py)
  - 8 additional comprehensive tests for OAuth flow scenarios
  - Timezone-naive datetime handling
  - Provider exception wrapping and error propagation
  - User not found edge cases
  - OAuth account linking to authenticated users
  - Auto-linking with email verification checks
  - Unverified user and OAuth email validation
- Account management error path tests (tests/api/test_account.py)
  - 3 tests for UserNotFoundError handling
  - Password change, account deletion, and email change error scenarios

## [0.2.1] - 2026-01-03

### Fixed
- Updated dependency version constraints to allow newer compatible versions
  - `fastapi[all] >=0.128.0,<0.129.0` (updated from <0.126.0)
  - `argon2-cffi >=23.1.0` (updated from >=25.1.0,<26.0.0)
  - `python-jose[cryptography] >=3.3.0` (added [cryptography] extra)
  - `pydantic-settings >=2.0.0` (updated from >=2.12.0,<3.0.0)
  - `sqlmodel >=0.0.16` (updated from >=0.0.27,<0.0.28)
  - `httpx >=0.27.0` (updated from >=0.27.0,<0.28.0)

## [0.2.0] - 2024-12-29

### Added
- MkDocs documentation site with auto-generated API reference
  - Material theme with dark/light mode support
  - Auto-generated API reference using mkdocstrings (Google-style docstrings)
  - GitHub Pages deployment workflow
  - Comprehensive navigation covering all modules
  - Search functionality and code syntax highlighting
  - Live documentation at https://sreekarnv.github.io/fastauth/
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

[unreleased]: https://github.com/sreekarnv/fastauth/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/sreekarnv/fastauth/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sreekarnv/fastauth/releases/tag/v0.1.0
