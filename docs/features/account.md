# Account Management

FastAuth exposes account management endpoints under `/auth/account` for reading and updating the current profile, changing passwords, changing email addresses, and deleting accounts. All endpoints require authentication.

## Endpoints

| Method | Path | Auth required | Description |
|--------|------|:---:|-------------|
| `GET`  | `/auth/account/profile` | Yes | Read the current user's profile |
| `PUT`  | `/auth/account/profile` | Yes | Update the current user's `name` and/or `image` |
| `POST` | `/auth/account/change-password` | Yes | Change password |
| `POST` | `/auth/account/change-email` | Yes | Request an email address change |
| `GET`  | `/auth/account/confirm-email-change?token=<token>` | No | Confirm the new email |
| `DELETE` | `/auth/account` | Yes | Delete the account |

---

## Read the profile

Returns the `id`, `email`, `name`, and `image` of the currently authenticated user.

```bash
curl http://localhost:8000/auth/account/profile \
  -H "Authorization: Bearer <access_token>"
```

Response:

```json
{
  "id": "ckl9...user-id",
  "email": "alice@example.com",
  "name": "Alice",
  "image": "https://example.com/avatars/alice.png"
}
```

`name` and `image` may be `null` if they have never been set (e.g. for an account created via credentials without a `name` field).

---

## Update the profile

Updates one or more mutable profile fields. Send only the fields you want to change — anything omitted (or sent as `null`) is left untouched. Empty bodies return `400`.

```bash
curl -X PUT http://localhost:8000/auth/account/profile \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Liddell", "image": "https://example.com/avatars/alice.png"}'
```

Response: the updated profile, in the same shape as the `GET` response above.

!!! note "Mutable fields"
    Only `name` and `image` are mutable through this endpoint. Email and verification status are managed via `/auth/account/change-email` and the email-verification flow.

---

## Change password

Requires the current password for verification. After a successful change, all existing refresh tokens are invalidated (forcing re-login on other devices).

```bash
curl -X POST http://localhost:8000/auth/account/change-password \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "old-pass", "new_password": "new-s3cur3P@ss!"}'
```

Response:

```json
{"message": "Password changed successfully"}
```

!!! warning "Existing sessions"
    Changing the password invalidates all refresh tokens (stored in `token_adapter`). Users on other devices will be logged out on their next refresh.

---

## Change email

Email changes go through a confirmation flow to verify the new address. Requires `token_adapter` and `email_transport` to be configured.

### Step 1 — Request the change

```bash
curl -X POST http://localhost:8000/auth/account/change-email \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"new_email": "newalice@example.com", "password": "current-pass"}'
```

Response:

```json
{"message": "Confirmation email sent to new address"}
```

FastAuth sends a confirmation email to the **new** address with a token link. The change is not applied until confirmed.

### Step 2 — Confirm the new email

The link in the email points to:

```
GET /auth/account/confirm-email-change?token=<token>
```

```bash
curl "http://localhost:8000/auth/account/confirm-email-change?token=<token-from-email>"
```

Response:

```json
{"message": "Email changed successfully"}
```

!!! info "Token expiry"
    Email change tokens expire after **30 minutes**.

---

## Delete account

Soft-deletes the account (sets `is_active=False`). Requires password confirmation.

```bash
curl -X DELETE http://localhost:8000/auth/account \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"password": "current-pass"}'
```

Response:

```json
{"message": "Account deleted successfully"}
```

!!! note "Soft delete"
    By default, the account is deactivated (`is_active=False`) rather than permanently deleted from the database. Deactivated users cannot sign in.
