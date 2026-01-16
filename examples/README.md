# FastAuth Examples

This directory contains example applications demonstrating different FastAuth features and use cases.

## Available Examples

### [Basic Example](./basic/)

A simple FastAPI application showing the core FastAuth features:
- User registration and authentication
- Email verification (console-based for development)
- Password reset
- Token refresh
- Protected routes
- SQLite database integration

**Best for:** Getting started with FastAuth, understanding the basics

**[View Example →](./basic/)**

---

### [OAuth with Google Example](./oauth-google/)

Complete Google OAuth ("Sign in with Google") integration:
- Google OAuth 2.0 authentication flow with PKCE
- Automatic user creation from OAuth profile
- Link/unlink OAuth accounts to existing users
- View user profile with linked accounts
- Secure state management for CSRF protection

**Best for:** Adding social login, understanding OAuth flows, account linking

**[View Example →](./oauth-google/)**

---

### [RBAC Blog Example](./rbac-blog/)

Role-Based Access Control (RBAC) in a blog application:
- Three roles: Admin, Editor, Viewer with different permission levels
- Four permissions: create_post, edit_post, publish_post, delete_post
- Protected routes using `require_role()` and `require_permission()` dependencies
- Blog post management with permission-based access control
- Seed script to set up roles, permissions, and test users

**Best for:** Understanding RBAC, implementing permissions, protecting routes

**[View Example →](./rbac-blog/)**

---

### [Session Management Example](./session-devices/)

Multi-device session tracking and management:
- Session creation on login with device tracking
- View all active sessions across devices
- Revoke individual sessions remotely
- Sign out from all devices (except current)
- Session metadata (IP address, user agent, device info, last active)
- Session ID embedded in JWT tokens

**Best for:** Multi-device apps, security features, session management

**[View Example →](./session-devices/)**

---

### [Custom Email Templates Example](./custom-email-templates/) 🆕

Beautiful, branded email templates with Jinja2:
- Custom EmailClient implementation extending FastAuth
- HTML email templates with responsive design
- Plain text fallbacks for compatibility
- Verification, password reset, and welcome emails
- Email preview tool for local testing
- Easy branding customization (colors, logo, company info)
- Production-ready SMTP configuration examples

**Best for:** Branding your emails, production deployments, custom email designs

**[View Example →](./custom-email-templates/)**

---

## Running the Examples

Each example is self-contained with its own README and setup instructions.

### General Steps

1. Navigate to the example directory:
   ```bash
   cd examples/basic
   ```

2. Install dependencies:
   ```bash
   # Install FastAuth (FastAPI is a peer dependency)
   pip install sreekarnv-fastauth

   # For OAuth examples, use:
   pip install sreekarnv-fastauth[oauth]

   # Make sure FastAPI is installed in your project
   pip install fastapi uvicorn[standard]
   ```

   Or install from the parent directory (for development):
   ```bash
   pip install -e ../..
   pip install fastapi uvicorn[standard]
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```

4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

5. Visit `http://localhost:8000/docs` for the interactive API documentation

## Common Features

All examples demonstrate:

✅ FastAuth integration
✅ Database setup and configuration
✅ Environment-based configuration
✅ API documentation (via FastAPI's Swagger UI)
✅ Complete authentication flows

## Need Help?

- Check each example's README for specific instructions
- See the [main FastAuth documentation](../README.md)
- Report issues on [GitHub Issues](https://github.com/sreekarnv/fastauth/issues)
