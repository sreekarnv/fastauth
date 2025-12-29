# API Reference

Welcome to the FastAuth API reference documentation. This section provides detailed documentation for all FastAuth modules, classes, and functions.

## Core Modules

The core modules provide the main authentication and authorization functionality:

- **Users**: User management and authentication
- **OAuth**: OAuth 2.0 provider integration
- **Sessions**: Session management
- **Roles**: Role-based access control
- **Account**: Account management (email changes, password changes)
- **Email Verification**: Email verification functionality
- **Password Reset**: Password reset functionality
- **Refresh Tokens**: JWT refresh token management
- **Hashing**: Password hashing utilities

## Adapters

Adapters provide database integration:

### Base Adapters
Abstract base classes for implementing custom database adapters.

### SQLAlchemy Adapters
Pre-built SQLAlchemy implementations of all adapters.

## API Routes

FastAPI router implementations for authentication endpoints:

- **Auth Routes**: Registration, login, logout
- **OAuth Routes**: OAuth provider authentication
- **Account Routes**: Account management
- **Session Routes**: Session management

## Security

Security utilities and middleware:

- **JWT**: JSON Web Token generation and validation
- **OAuth Security**: OAuth-specific security utilities
- **Rate Limiting**: Rate limiting middleware
- **Email Verification Security**: Email verification token management
- **Password Reset Security**: Password reset token management
- **Refresh Token Security**: Refresh token validation

## Email

Email sending capabilities:

- **Base Email**: Abstract email provider interface
- **Console Provider**: Development email provider (prints to console)
- **SMTP Provider**: Production SMTP email provider
- **Email Factory**: Factory for creating email providers

## OAuth Providers

OAuth provider implementations:

- **Base Provider**: Abstract OAuth provider interface
- **Google**: Google OAuth provider

## Settings

Configuration management for FastAuth.
