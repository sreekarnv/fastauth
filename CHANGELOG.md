# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
