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

## Running the Examples

Each example is self-contained with its own README and setup instructions.

### General Steps

1. Navigate to the example directory:
   ```bash
   cd examples/basic
   ```

2. Install dependencies:
   ```bash
   pip install fastapi[all] sqlmodel argon2-cffi python-jose pydantic-settings
   ```

   Or install FastAuth from the parent directory:
   ```bash
   pip install -e ../..
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
