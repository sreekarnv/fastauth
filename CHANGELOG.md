# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.5] - 2026-05-08

### Added

- **Token introspection (RFC 7662)** — new `/auth/token/introspect` endpoint to check token validity
  - Returns `active: true/false` based on token validity and (for refresh tokens) JTI allowlist status
  - Returns token claims: `sub`, `exp`, `jti`, `type`, `email`
  - Never raises 4xx for invalid tokens — returns `active: false` instead
- **Token revocation (RFC 7009)** — new `/auth/token/revoke` endpoint to invalidate refresh tokens
  - Only token owner can revoke their own tokens (checks `sub` claim)
  - Removes JTI from allowlist when token adapter is configured
  - Returns `400` for access tokens (only refresh tokens supported)
  - Returns `403` when trying to revoke another user's token
- **Remember me login** — extended refresh token TTL option during login
  - `POST /auth/login` accepts optional `remember: boolean` field
  - When `remember: true`, refresh token TTL extends to 90 days (vs default 30 days)
  - New `JWTConfig.remember_me_ttl` config option (default: 7,776,000 seconds)
- **Profile endpoints** — new `/auth/account/profile` endpoints for user profile management
  - `GET /auth/account/profile` — returns user profile (id, email, name, image)
  - `PUT /auth/account/profile` — updates name and/or image fields

- **OAuth account linking** — authenticated users can now connect additional OAuth providers to their existing account without going through the full sign-in flow
  - `GET /auth/oauth/{provider}/link?redirect_uri=...` — requires Bearer token; returns the provider authorization URL with a link-scoped PKCE state
  - `GET /auth/oauth/{provider}/link/callback?code=...&state=...` — public; exchanges the code, creates the `OAuthAccount` record, fires the `on_oauth_link` hook, and returns `{"message": "<Provider> account linked successfully"}`
  - Returns `400` when the provider account is already linked to any user
  - `initiate_link_flow` and `link_oauth_account` added to `fastauth.core.oauth`
- **OpenAPI error schemas** — all routers now declare structured error responses via `responses=` so type-checker users, SDK generators, and API explorers see documented error shapes
  - New `ErrorDetail` Pydantic model in `fastauth.api.schemas` matching FastAPI's default `{"detail": "..."}` format
  - `create_auth_router` — `400`, `401` on all endpoints; `409` on `POST /register`
  - `create_oauth_router` — `400`, `401`, `403`, `404` on all endpoints; `409` on `GET /{provider}/link`
  - `create_magic_links_router` — `401`, `403`, `501`
  - `create_passkeys_router` — `400`, `401`, `403`, `404`, `501`

### Fixed

- JWKS route (`/.well-known/jwks.json`) was never registered when `initialize_jwks()` is called inside the FastAPI lifespan handler — `FastAuth.mount()` now checks `config.jwt.jwks_enabled` (static config) instead of `self.jwks_manager` (runtime state), which was always `None` at mount time
- Pre-commit hooks were not installed (`pre-commit install` had never been run); running it now creates `.git/hooks/pre-commit`
- `.pre-commit-config.yaml` referenced non-existent ruff version `v0.14.10`; corrected to `v0.15.1`

## [Unreleased]

## [0.5.3] - 2026-03-21

### Added

- `FastAuth.initialize_roles()` — new lifespan method that seeds roles defined in `config.roles` into the role adapter, mirroring the existing `initialize_jwks()` pattern

### Fixed

- `default_role` was never assigned to new users despite being set in `FastAuthConfig` — `assign_default_role` is now called after user creation in all three registration paths: credentials (`POST /auth/register`), magic links (auto-signup on first login), and OAuth (first-time sign-in)

## [0.5.2] - 2026-03-21

### Fixed

- JWKS route (`/.well-known/jwks.json`) was never registered when `initialize_jwks()` is called inside the FastAPI lifespan handler — `FastAuth.mount()` now checks `config.jwt.jwks_enabled` (static config) instead of `self.jwks_manager` (runtime state), which was always `None` at mount time

## [0.5.0] - 2026-02-27

### Added

- **Magic Links** passwordless authentication provider
  - `MagicLinksProvider` — configurable `max_age` (default 15 minutes)
  - `POST /auth/magic-links/login` — requests a link; auto-creates the user if the email is new
  - `GET /auth/magic-links/callback?token=<token>` — one-time token exchange returning an access/refresh token pair
  - Tokens are single-use and deleted immediately on first use
  - Full hook support: `allow_signin` gate and `on_signin` callback, both receiving `provider="magic_link"`
  - `is_active` check on callback; `token_delivery="cookie"` supported
  - Router is mounted only when `MagicLinksProvider` is present in `config.providers`
- **Custom email templates** via `email_template_dir` in `FastAuthConfig`
  - Point to any directory; files found there override the corresponding built-in template
  - Uses `ChoiceLoader` — unoverridden templates fall back to FastAuth's built-ins automatically
  - Supported templates: `welcome.jinja2`, `verification.jinja2`, `password_reset.jinja2`, `email_change.jinja2`, `magic_link_login.jinja2`
- **Magic Links example** (`examples/magic_link/`) — SQLite + SMTP, environment-variable driven
- **Custom templates example** (`examples/custom_templates/`) — dark-themed HTML templates matching the FastAuth docs palette, demonstrating per-template override with built-in fallback

### Fixed

- `send_magic_link_login_request` — missing `str` type annotation on `token` parameter
- `magic_link_login.jinja2` — corrected heading copy ("Log In to your email" → "Log in to your account") and added expiry hint to body text

### Changed

- `mkdocs.yml` — added Magic Links entries under Providers, Features, and Guides nav sections
- Docs: added `docs/features/magic-links.md`, `docs/providers/magic-links.md`, `docs/guides/magic-links.md`

## [0.4.0] - 2026-02-24

### Added
- **Passkeys (WebAuthn)** authentication provider via the new `webauthn` optional extra (`pip install "sreekarnv-fastauth[webauthn]"`)
  - `PasskeyProvider` — configure `rp_id`, `rp_name`, and one or more `origin` values
  - `SQLAlchemyPasskeyAdapter` — persists credentials in the `fastauth_passkeys` table with cascade delete
  - `MemoryPasskeyAdapter` — in-memory adapter for testing
  - Six new endpoints mounted under `/auth/passkeys/`: `POST register/begin`, `POST register/complete`, `GET /` (list), `DELETE /{id}`, `POST authenticate/begin`, `POST authenticate/complete`
  - `PasskeyData` TypedDict and `PasskeyAdapter` Protocol in `fastauth.types` / `fastauth.core.protocols`
  - `passkey_adapter` and `passkey_state_store` fields in `FastAuthConfig`
  - `residentKey: preferred` requested during registration — enables Windows Hello, Touch ID, and Face ID account pickers without entering an email
  - Event hooks: `on_passkey_registered(user, passkey)` and `on_passkey_deleted(user, passkey)`
  - `adapter.passkey` property on `SQLAlchemyAdapter`
- **Passkeys example** (`examples/passkeys/`) — full working demo with Jinja2 template, vanilla JS, and `@simplewebauthn/browser` loaded from CDN; includes IP-address detection warning for local development
- **Passkeys guide** (`docs/guides/passkeys.md`) and updated feature reference (`docs/features/passkeys.md`)

### Fixed
- `MemoryUserAdapter.update_user` — email index was not updated when the `email` field was changed (the old email key remained in `_email_index` indefinitely)

### Changed
- `[all]` extra now includes `webauthn`
- `README.md`, `docs/getting-started/installation.md`, and `mkdocs.yml` updated with passkeys entry points and the `webauthn` extra

## [0.3.1] - 2026-02-19

### Changed
- Fixed issues within the `/auth/account/confirm-email-change` route
- `/auth/account/confirm-email-change` route is not a `GET` route instead of `POST`

## [0.3.0] - 2026-02-19

### Added
- **Complete rewrite** from v0.2.x: NextAuth-inspired modular architecture with ABC protocols for providers/adapters/backends.[file:31]
- **Monorepo**: uv workspace (`packages/fastauth`), extras (`standard`, `jwt`, `oauth`, `sqlalchemy`, `redis`, `email`, `cli`).
- **Core**: `FastAuthConfig` dataclass, JWT (HS256/RS256 w/ joserfc), sessions (JWT/database), RBAC (roles/permissions), OAuth orchestration, email dispatcher, event hooks.
- **Providers**: Credentials (argon2-cffi), Google (PKCE), GitHub.
- **Adapters**: Memory (dev/testing), SQLAlchemy (User/Session/Token/OAuthAccount/Role models as `fastauth_*` tables).
- **Session Backends**: Memory, Redis, Database (via SessionAdapter).
- **Email Transports**: Console, SMTP (aiosmtplib/Jinja2), Webhook (microservices).
- **API**: `FastAuth(config).mount(app)`, routes (register/login/refresh/logout/OAuth/session/account/rbac), deps (`get_current_user`, `require_role/permission`), `/.well-known/jwks.json`.
- **CLI**: `fastauth version/init/generate-secret/providers/check` (typer/rich extra).
- **Docs**: MkDocs (Material theme, mkdocstrings API ref), examples (basic/oauth/jwt-microservice/full).
- **Build/Test**: Ruff (lint/format, replaces Black), pytest 95%+ coverage (all phases), GitHub Actions (lint/test 3.11-3.13/docs/PyPI).
- **IDs**: cuid2 (sortable/URL-safe).
- **Key Mgmt**: JWKS manager w/ rotation (microservices).

### Changed
- Migrated from Poetry to uv monorepo (faster sync, workspace support).
- Dependencies: joserfc (full JOSE/JWK), cryptography (RSA).

### Removed
- v0.2.x codebase—**major rewrite, not backward-compatible**.

### Breaking Changes
- New API/config/schema—fresh setup required (no v0.2 → v0.3 migration).
- Tables: `fastauth_users/sessions/tokens/oauthaccounts/roles`.
- Install: `uv add fastauth[standard]` or `pip install fastauth[all]`.

## [0.2.6] - 2026-01-24

### Changed
- `User.hashed_password` is now nullable (`str | None`)
  - OAuth-only users have `hashed_password=NULL` instead of a random password
  - `verify_password()` returns `False` when password is `None`
  - Prevents OAuth-only users from using password login

## [0.2.5] - 2026-01-21

### Added
- Command-line interface (CLI) tool for FastAuth utilities
  - `fastauth version` - Display FastAuth version
  - `fastauth check` - Check installation and dependency status
  - `fastauth generate-secret` - Generate secure secret keys for JWT tokens
  - `fastauth init` - Initialize new FastAuth project with boilerplate files
  - `fastauth providers` - List available OAuth providers
- New `[cli]` optional dependency extra
  - Install with: `pip install sreekarnv-fastauth[cli]`
  - Includes `typer>=0.9.0` and `rich>=13.0.0`
- CLI documentation in docs/guides/cli.md
- 15 tests for CLI with 100% coverage

### Changed
- Updated `[all]` extra to include CLI dependencies

## [0.2.4] - 2026-01-17

### Changed
- FastAPI is now a peer dependency (not installed automatically)
  - Users must install FastAPI separately: `pip install fastapi`
  - Avoids version conflicts with existing FastAPI installations
- httpx is now an optional dependency for OAuth providers
  - Install with: `pip install sreekarnv-fastauth[oauth]`
  - `oauth_router` and `GoogleOAuthProvider` only available when httpx is installed

### Added
- Dependency compatibility module (`fastauth/_compat.py`)
  - `HAS_FASTAPI` and `HAS_HTTPX` flags for runtime dependency detection
  - `require_fastapi()` and `require_httpx()` guard functions
  - `MissingDependencyError` with helpful install hints
- `email-validator` and `itsdangerous` to core dependencies
- Tests for `_compat` module (9 tests)
- Updated documentation for optional dependencies
  - Installation guide with extras explained
  - All example READMEs updated with correct install commands

### Fixed
- Conditional imports prevent ImportError when optional dependencies missing
- CI failures due to missing `email-validator` and `itsdangerous`

## [0.2.3] - 2026-01-10

### Added
- GET endpoints for clickable email links
  - `GET /auth/email-verification/confirm?token=...` - Direct email verification via clickable link
  - `GET /account/confirm-email-change?token=...` - Direct email change confirmation via clickable link
  - `GET /auth/password-reset/validate?token=...` - Validate password reset token before showing form
  - Enables users to verify emails and confirm changes with single click instead of copying tokens
  - Returns structured JSON responses with status and messages
  - Maintains full backward compatibility with existing POST endpoints
- Custom email templates example (`examples/custom-email-templates/`)
  - Comprehensive example demonstrating Jinja2 template integration for branded emails
  - Beautiful responsive HTML email templates with gradient headers and CTA buttons
  - Plain text fallbacks for email client compatibility
  - Email preview tool for local testing without sending emails
  - SMTP testing script supporting MailHog (dev), Gmail, and SendGrid (production)
  - Password reset wrapper endpoint showing token validation pattern
  - 380+ line README with setup, testing, and customization guides
  - Demonstrates EmailClient extension, template inheritance, and MIME multipart emails

### Changed
- Refactored email verification endpoints to reduce code duplication
  - Extracted `_confirm_email_verification_helper()` function shared by POST and GET endpoints
  - Both endpoints now use identical validation logic for consistency
- Updated custom email templates example
  - Removed unnecessary `/verify-email` wrapper (uses FastAuth's native GET endpoint)
  - Simplified `/reset-password` wrapper to validate tokens using FastAuth adapters
  - Removed `requests` dependency (no longer needed for HTTP forwarding)
  - Updated email client URLs to use FastAuth's native endpoints
  - Updated documentation with correct flow diagrams and usage examples

### Tests
- Added 6 comprehensive tests for new GET endpoints
  - `test_email_verification_confirm_get_success()` - Valid email verification via GET
  - `test_email_verification_confirm_get_invalid_token()` - Invalid token error handling
  - `test_password_reset_validate_success()` - Valid password reset token validation
  - `test_password_reset_validate_invalid_token()` - Invalid token error handling
  - `test_confirm_email_change_get_success()` - Valid email change confirmation via GET
  - `test_confirm_email_change_get_invalid_token()` - Invalid token error handling
- All tests pass with 99%+ coverage maintained

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

## [0.2.0] - 2025-12-29

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

## [0.1.0] - 2025-12-27

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

[unreleased]: https://github.com/sreekarnv/fastauth/compare/v0.5.3...HEAD
[0.5.3]: https://github.com/sreekarnv/fastauth/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/sreekarnv/fastauth/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/sreekarnv/fastauth/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/sreekarnv/fastauth/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/sreekarnv/fastauth/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/sreekarnv/fastauth/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/sreekarnv/fastauth/compare/v0.2.6...v0.3.0
[0.2.6]: https://github.com/sreekarnv/fastauth/compare/v0.2.5...v0.2.6
[0.2.5]: https://github.com/sreekarnv/fastauth/compare/v0.2.4...v0.2.5
[0.2.4]: https://github.com/sreekarnv/fastauth/compare/v0.2.3...v0.2.4
[0.2.3]: https://github.com/sreekarnv/fastauth/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/sreekarnv/fastauth/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/sreekarnv/fastauth/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/sreekarnv/fastauth/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sreekarnv/fastauth/releases/tag/v0.1.0
