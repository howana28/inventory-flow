# Security notes

- Authentication uses opaque server-side sessions stored in the database.
- The browser receives only an HttpOnly, SameSite cookie; no database or ERP secret is exposed to JavaScript.
- Passwords use PBKDF2-HMAC-SHA256 with per-user salts and 310,000 iterations.
- Role-based permissions are checked in backend dependencies, not only hidden in the UI.
- The public demo defaults to `ALLOW_EXTERNAL_CONNECTIONS=false`.
- Bling credentials are environment variables and never committed.
- OAuth access/refresh tokens require `TOKEN_ENCRYPTION_KEY` and are encrypted with Fernet before persistence.
- The Integrations screen shows sanitized database metadata only; passwords and connection strings are never returned.
- The repository contains synthetic catalog data generated deterministically at runtime.
