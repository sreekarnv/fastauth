# Cookie Delivery

By default FastAuth returns tokens in the JSON response body. Switching to `"cookie"` delivery sets access and refresh tokens as HttpOnly cookies instead — the browser sends them automatically on every request. FastAuth also sets a readable CSRF cookie so browser clients can protect state-changing requests.

!!! danger "Tokenless response bodies in cookie mode"
    When `token_delivery="cookie"`, FastAuth **never returns tokens in the JSON body**. Every sign-in / refresh / OAuth-callback / magic-link-callback / passkey-authenticate response is a small `{"message": "Authentication successful"}` payload — the tokens are attached only as `HttpOnly` cookies. This prevents accidental leaks through logs, browser dev tools, or JavaScript that happens to read the response.

    If a client needs the access token in JavaScript, use the default `"json"` delivery (or read it from your own server-side session).

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

1. **Sign-in / sign-up / refresh / OAuth callback / magic-link callback / passkey auth completion** — FastAuth sets three cookies on the response:
   - `access_token` (15 min, `HttpOnly`)
   - `refresh_token` (30 days, `HttpOnly`)
   - `csrf_token` (readable by JavaScript, used only for CSRF protection)
   The response body is `{"message": "Authentication successful"}` and intentionally contains no token material.
2. **Protected routes** — `require_auth` reads the access token from `Authorization: Bearer` first, then falls back to the access-token cookie.
3. **Unsafe cookie-authenticated requests** — `POST`, `PUT`, `PATCH`, and `DELETE` requests authenticated by cookies must send the CSRF token in the configured header. `GET`, `HEAD`, and `OPTIONS` do not require the header. Bearer-token requests do not require CSRF.
4. **Sign-out** — FastAuth clears the auth cookies and the CSRF cookie.

## CSRF protection

CSRF protection is enabled by default for cookie-authenticated unsafe requests. After login/register/refresh, read the `csrf_token` cookie and send it as `X-CSRF-Token` on every `POST`, `PUT`, `PATCH`, and `DELETE` request that relies on cookies.

```javascript
function readCookie(name) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1]
}

await fetch("/auth/account/profile", {
  method: "PUT",
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
    "X-CSRF-Token": decodeURIComponent(readCookie("csrf_token") ?? ""),
  },
  body: JSON.stringify({name: "Ada"}),
})
```

This also applies to cookie-based `POST /auth/refresh` and `POST /auth/logout`. Missing or mismatched CSRF tokens return `403 Forbidden`.

## Cookie options

| Field | Default | Description |
|-------|---------|-------------|
| `cookie_name_access` | `"access_token"` | Access-token cookie name |
| `cookie_name_refresh` | `"refresh_token"` | Refresh-token cookie name |
| `cookie_secure` | `not debug` | `Secure` flag (HTTPS only) |
| `cookie_httponly` | `True` | `HttpOnly` flag (not accessible from JS) |
| `cookie_samesite` | `"lax"` | `SameSite` policy |
| `cookie_domain` | `None` | Domain scope |
| `csrf_enabled` | `True` | Require CSRF header for cookie-authenticated unsafe requests |
| `csrf_cookie_name` | `"csrf_token"` | Readable CSRF cookie name |
| `csrf_header_name` | `"X-CSRF-Token"` | Request header that must match the CSRF cookie |

## SameSite policy

| Value | Behaviour | When to use |
|-------|-----------|-------------|
| `"lax"` | Sent on same-site requests and top-level cross-site navigations | Default for most apps |
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
