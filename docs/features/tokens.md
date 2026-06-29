# Token Introspection & Revocation

FastAuth exposes the standard [RFC 7662 (introspection)](https://datatracker.ietf.org/doc/html/rfc7662) and [RFC 7009 (revocation)](https://datatracker.ietf.org/doc/html/rfc7009) endpoints under `/auth/token`. Both require a valid access token on the request itself — they are not anonymous.

## Endpoints

| Method | Path | Auth required | Description |
|--------|------|:---:|-------------|
| `POST` | `/auth/token/introspect` | Yes | Check whether a token is active and return its claims |
| `POST` | `/auth/token/revoke` | Yes | Revoke a refresh token (removes its JTI from the allowlist) |

## Introspect a token

```bash
curl -X POST http://localhost:8000/auth/token/introspect \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"token": "<token-to-check>"}'
```

Response (`200 OK`):

```json
{
  "active": true,
  "sub": "ckl9...user-id",
  "exp": 1700000900,
  "jti": "ckl9...jti",
  "token_type": "refresh",
  "email": "alice@example.com"
}
```

`active` is `true` only when:

- The token's signature, `iss`, `aud`, and `exp` are all valid
- For **refresh tokens**: the token's `jti` is still present in the `token_adapter` allowlist (only checked when `token_adapter` is configured). Revoked or already-consumed refresh tokens return `active: false`.

!!! tip "Always 200 — even for bad tokens"
    Introspection never returns `4xx` for an invalid or expired token. It always responds `200 OK` with `active: false`, mirroring RFC 7662. The endpoint only returns `401` if the **caller's** own access token (the one passed in `Authorization`) is missing or invalid.

### Response fields

| Field | Type | Description |
|-------|------|-------------|
| `active` | `bool` | `true` if the token is valid and (for refresh tokens) still allowlisted |
| `sub` | `str \| null` | The user id encoded in the token |
| `exp` | `int \| null` | Expiration timestamp (seconds since epoch) |
| `jti` | `str \| null` | Token id (used for refresh-token revocation) |
| `token_type` | `str \| null` | `"access"` or `"refresh"` |
| `email` | `str \| null` | The email claim, if the token carries one |

## Revoke a refresh token

```bash
curl -X POST http://localhost:8000/auth/token/revoke \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"token": "<refresh_token>"}'
```

Response (`200 OK`):

```json
{"message": "Token revoked"}
```

Revocation rules:

- **Only refresh tokens** can be revoked. Sending an access token returns `400`.
- **Only the owner** can revoke their own token. The endpoint compares the token's `sub` claim with the caller's user id and returns `403` if they don't match.
- **Token adapter required.** When `token_adapter` is configured, the JTI is removed from the allowlist. The endpoint returns `400` if `token_adapter` is not configured.
- An invalid or expired token returns `400`.

After revocation, calling `/auth/token/introspect` with the same refresh token returns `active: false`, and `/auth/refresh` with that token fails with `401` ("Refresh token has already been used"). The token is also no longer usable for rotation; FastAuth treats any further use as a replay and revokes the **entire** refresh-token family for that user.

## How the JTI allowlist works

When `token_adapter` is configured, FastAuth records the JTI of every issued refresh token in the `refresh_jti` allowlist (one row per active refresh token). The allowlist is consulted in three places:

| Action | Effect on the JTI allowlist |
|--------|----------------------------|
| `POST /auth/login` or `/auth/register` with `token_adapter` | New JTI appended |
| `POST /auth/refresh` (success) | Old JTI atomically consumed; new JTI appended |
| `POST /auth/token/revoke` | Matching JTI deleted |
| `POST /auth/logout` | **All** JTIs for the user deleted |
| `POST /auth/account/change-password` | **All** JTIs for the user deleted |
| `POST /auth/reset-password` | **All** JTIs for the user deleted |

If a refresh attempt arrives with a JTI that is no longer in the allowlist (already used, revoked, or never existed), FastAuth treats it as a replay attack and revokes the entire refresh-token family for that user, forcing them to sign in again. This is what `/auth/token/introspect` reports as `active: false` for refresh tokens.

!!! info "Disabling the allowlist"
    If you do not configure `token_adapter`, refresh tokens are still issued but no allowlist is maintained. In that mode `introspect` cannot determine whether a refresh token is still valid (the JTI check is skipped), and `/auth/token/revoke` returns `400`.

## See also

- [Tokens & Sessions](../concepts/tokens.md) — refresh rotation, replay detection, and the refresh flow in general
- [JWT](../features/jwt.md) — token structure, claims, and signing algorithms
