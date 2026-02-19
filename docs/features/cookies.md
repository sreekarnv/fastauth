# Cookie Delivery

By default FastAuth returns tokens in the JSON response body. Switching to `"cookie"` delivery sets them as HttpOnly cookies instead — the browser sends them automatically on every request.

## Enable cookie delivery

```python
config = FastAuthConfig(
    ...,
    token_delivery="cookie",
    cookie_samesite="lax",     # default
    cookie_httponly=True,      # default
    # cookie_secure defaults to True in production (not debug),
    # False in debug mode. Override explicitly if needed:
    # cookie_secure=True,
)
```

## How it works

When `token_delivery="cookie"`:

1. **Sign-in / sign-up / refresh** — FastAuth sets two cookies on the response:
   - `access_token` (15 min, `HttpOnly`)
   - `refresh_token` (30 days, `HttpOnly`)
2. **Protected routes** — `require_auth` reads the access token from the cookie first, then falls back to the `Authorization: Bearer` header.
3. **Sign-out** — FastAuth clears both cookies.

## Cookie options

| Field | Default | Description |
|-------|---------|-------------|
| `cookie_name_access` | `"access_token"` | Access-token cookie name |
| `cookie_name_refresh` | `"refresh_token"` | Refresh-token cookie name |
| `cookie_secure` | `not debug` | `Secure` flag (HTTPS only) |
| `cookie_httponly` | `True` | `HttpOnly` flag (not accessible from JS) |
| `cookie_samesite` | `"lax"` | `SameSite` policy |
| `cookie_domain` | `None` | Domain scope |

## SameSite policy

| Value | Behaviour | When to use |
|-------|-----------|-------------|
| `"lax"` | Sent on same-site requests and top-level cross-site navigations | Default — protects against CSRF for most apps |
| `"strict"` | Only sent on same-site requests | Maximum protection, but breaks OAuth redirects |
| `"none"` | Always sent (requires `Secure=True`) | Cross-origin frontends (e.g. SPA on different domain) |

!!! warning "Cross-origin SPAs"
    If your frontend is on a different domain (e.g. `app.example.com` → `api.example.com`), set `cookie_samesite="none"` and `cookie_secure=True`. You'll also need to configure `cors_origins` and ensure your frontend sends credentials (`credentials: "include"` in fetch).

## Development mode

```python
config = FastAuthConfig(
    ...,
    token_delivery="cookie",
    debug=True,  # sets cookie_secure=False so cookies work on http://localhost
)
```

!!! danger
    Never set `debug=True` in production.
