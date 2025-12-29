# FastAuth Documentation

Welcome to the FastAuth documentation! This guide will help you build secure, production-ready authentication systems for your FastAPI applications.

## 📚 Table of Contents

### Getting Started

- **[Quick Start Guide](quickstart.md)** - Get up and running in 10 minutes
  - Installation
  - Basic setup
  - Common use cases
  - Frontend integration examples

### Core Concepts

- **[Architecture](architecture.md)** - Understand FastAuth's design
  - Design principles
  - Layered architecture
  - Component overview
  - Data flows
  - Security architecture
  - Extension points

- **[API Reference](api-reference.md)** - Complete API documentation
  - Core module functions
  - Adapters (base & SQLAlchemy)
  - API routes & endpoints
  - Security utilities
  - Models & schemas
  - Dependencies
  - Exceptions

### Features

- **[OAuth 2.0 Guide](oauth.md)** - Third-party authentication
  - Google OAuth setup
  - OAuth flow explained
  - PKCE implementation
  - Account linking
  - Custom providers
  - Security best practices

### Operations

- **[Testing Guide](testing.md)** - Write and run tests
  - Test organization
  - Running tests
  - Coverage analysis
  - Writing new tests
  - Best practices
  - CI/CD integration

- **[Deployment Guide](deployment.md)** - Deploy to production
  - Production checklist
  - Environment configuration
  - Database setup
  - Deployment platforms (Docker, AWS, Heroku)
  - Security hardening
  - Monitoring & logging
  - Performance optimization

## 🚀 Quick Links

### For New Users

1. Start with **[Quick Start Guide](quickstart.md)** to get FastAuth running
2. Read **[Architecture](architecture.md)** to understand the design
3. Follow **[Deployment Guide](deployment.md)** when ready for production

### For Developers

- **Testing**: See [Testing Guide](testing.md)
- **OAuth Integration**: See [OAuth Guide](oauth.md)
- **API Details**: See [API Reference](api-reference.md)

### For DevOps

- **Deployment**: See [Deployment Guide](deployment.md)
- **Testing**: See [Testing Guide](testing.md)
- **Architecture**: See [Architecture](architecture.md)

## 📖 Documentation Overview

### Quick Start Guide
**File**: `quickstart.md`
**Purpose**: Get FastAuth running quickly
**Topics**: Installation, basic setup, common patterns, frontend integration

**When to read**: First time using FastAuth

### Architecture Guide
**File**: `architecture.md`
**Purpose**: Deep dive into FastAuth's architecture
**Topics**: Design principles, layers, components, data flows, security, extensibility

**When to read**: Understanding internals, implementing custom features, debugging

### API Reference
**File**: `api-reference.md`
**Purpose**: Complete API documentation
**Topics**: All functions, classes, endpoints, parameters, return values, examples

**When to read**: Looking up specific functions, implementing features, integration

### OAuth Guide
**File**: `oauth.md`
**Purpose**: Set up OAuth 2.0 authentication
**Topics**: Provider setup, OAuth flows, PKCE, account linking, custom providers

**When to read**: Adding social login, implementing OAuth

### Testing Guide
**File**: `testing.md`
**Purpose**: Testing FastAuth applications
**Topics**: Test organization, running tests, coverage, writing tests, CI/CD

**When to read**: Writing tests, improving coverage, setting up CI

### Deployment Guide
**File**: `deployment.md`
**Purpose**: Deploy FastAuth to production
**Topics**: Production setup, databases, platforms, security, monitoring, optimization

**When to read**: Deploying to production, scaling, hardening

## 🎯 Common Use Cases

### I want to...

**...get started quickly**
→ [Quick Start Guide](quickstart.md)

**...understand how FastAuth works**
→ [Architecture](architecture.md)

**...add Google login**
→ [OAuth Guide](oauth.md)

**...deploy to production**
→ [Deployment Guide](deployment.md)

**...write tests**
→ [Testing Guide](testing.md)

**...look up a specific function**
→ [API Reference](api-reference.md)

**...protect routes with roles**
→ [Quick Start Guide - RBAC Section](quickstart.md#adding-role-based-access-control-rbac)

**...change password**
→ [Quick Start Guide - Account Management](quickstart.md#account-management)

**...customize email templates**
→ [Architecture - Email Components](architecture.md#email-components)

**...use a different database**
→ [Architecture - Custom Adapters](architecture.md#custom-adapters)

## 🛠️ Feature Coverage

### Authentication
- ✅ User registration
- ✅ Email/password login
- ✅ Email verification
- ✅ Password reset
- ✅ Refresh tokens
- ✅ OAuth 2.0 (Google)
- ✅ JWT tokens

### Authorization
- ✅ Role-Based Access Control (RBAC)
- ✅ Permissions system
- ✅ Route protection
- ✅ Programmatic permission checks

### Session Management
- ✅ Device tracking
- ✅ Session listing
- ✅ Session revocation
- ✅ Inactive session cleanup
- ✅ Multi-device support

### Account Management
- ✅ Change password
- ✅ Change email
- ✅ Delete account (soft/hard)
- ✅ Link OAuth accounts
- ✅ Unlink OAuth accounts

### Security
- ✅ Argon2 password hashing
- ✅ JWT token validation
- ✅ Refresh token rotation
- ✅ Rate limiting
- ✅ CSRF protection (OAuth state tokens)
- ✅ PKCE support
- ✅ SQL injection protection

### Database Support
- ✅ SQLAlchemy adapter (included)
- ✅ Database-agnostic core
- ⏳ MongoDB adapter (planned)
- ⏳ Custom adapter guide

### Email Providers
- ✅ Console (development)
- ✅ SMTP
- ⏳ SendGrid (planned)
- ⏳ AWS SES (planned)

## 📊 Documentation Stats

- **6 guides** covering all aspects
- **195 tests** with 85% coverage
- **Production-ready** examples
- **Security-focused** best practices
- **Framework-agnostic** core design

## 🤝 Contributing to Docs

Found an error or want to improve the documentation?

1. **Report issues**: [GitHub Issues](https://github.com/sreekarnv/fastauth/issues)
2. **Suggest improvements**: [GitHub Discussions](https://github.com/sreekarnv/fastauth/discussions)
3. **Submit PRs**: [Contributing Guide](../CONTRIBUTING.md)

### Documentation Style Guide

- Use clear, concise language
- Provide code examples
- Include both success and error cases
- Link to related documentation
- Keep examples up-to-date
- Test all code examples

## 🔗 External Resources

### FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)

### OAuth 2.0
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [PKCE RFC 7636](https://tools.ietf.org/html/rfc7636)
- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)

### Security
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Password Hashing](https://www.argon2.com/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

### Testing
- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)

### Deployment
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [AWS Documentation](https://docs.aws.amazon.com/)

## 📝 Version Information

This documentation is for **FastAuth v0.2.0**

- **Python**: 3.11+
- **FastAPI**: 0.125.0+
- **SQLModel**: 0.0.27+
- **Last Updated**: December 2025

## 💬 Getting Help

**Documentation Issues:**
- Missing information? [Report it](https://github.com/sreekarnv/fastauth/issues/new)
- Unclear explanation? [Ask in discussions](https://github.com/sreekarnv/fastauth/discussions)

**Implementation Help:**
- Check the [API Reference](api-reference.md) first
- Review [examples](../examples/)
- Search [existing issues](https://github.com/sreekarnv/fastauth/issues)
- Ask in [discussions](https://github.com/sreekarnv/fastauth/discussions)

**Bug Reports:**
- [Create an issue](https://github.com/sreekarnv/fastauth/issues/new)
- Include: FastAuth version, Python version, error message, minimal reproduction

---

**Happy authenticating!** 🔐

[Back to Main README](../README.md)
