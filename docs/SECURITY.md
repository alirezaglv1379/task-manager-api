# Security model

## JWT

- HS256 is fixed in code; token-provided algorithm values are never trusted.
- Access Token lifetime is 30 minutes.
- Access tokens require a valid signature, numeric `exp`, positive numeric-string `sub`, and `type=access`.
- User existence is checked on every authenticated request.
- Responses do not expose password hashes.

## Passwords

The current minimal-dependency plan retains Passlib Bcrypt for compatibility with hashes created by the original app. Passwords are limited to 72 UTF-8 bytes to avoid Bcrypt truncation ambiguity. Passwords are never logged.

## Refresh sessions

- Refresh tokens are cryptographically random opaque values.
- Only SHA-256 hashes are stored in SQLite.
- The raw token is set in an HttpOnly cookie with configurable Secure and SameSite flags.
- Rotation revokes the previous token and creates a new token in the same family.
- Reuse of a rotated token revokes the remaining active sessions in that family.
- Logout revokes the presented refresh session and clears the cookie.
- A stateless Access Token may remain usable until its 30-minute expiry after logout; the browser clears its in-memory copy. This is an intentional trade-off for this release.

## CSRF, CORS and cookies

- CORS credentials remain disabled (`allow_credentials=False`).
- The intended deployment is same-origin: Vite proxy in development and reverse proxy in production.
- Refresh and logout require an exact trusted `Origin`.
- Use HTTPS and `COOKIE_SECURE=true` in production.

## Login rate limiting

- IP: 20 login requests per 15-minute fixed window.
- Username: 5 failed attempts per 15-minute fixed window.
- Counters are stored in SQLite with hashed identifiers and atomic upserts.
- Forwarded IP headers are used only when the direct peer is in `TRUSTED_PROXY_IPS`.
- Limits expire automatically; accounts are not permanently locked.

## Secrets and logs

Set `SECRET_KEY` to a random value of at least 32 bytes. Never commit `.env`. Logs contain operational exception details but must not include passwords, access tokens or raw refresh tokens.

## Dependency review

`python-jose` is retained temporarily per the agreed minimal-change scope, with HS256 explicitly restricted and tested. Run `pip-audit` on every dependency update. Any reported vulnerability must be triaged and fixed or explicitly documented before release; do not silently suppress audit findings.
