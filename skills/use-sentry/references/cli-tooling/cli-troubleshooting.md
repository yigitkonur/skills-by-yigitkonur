# Sentry CLI Troubleshooting & FAQ

Common errors encountered when running `sentry` or `sentry-cli` and their immediate solutions.

## 1. `sentry auth whoami` returns 404
- **Symptom:** Running `sentry auth whoami` outputs `Error: 404 Not Found`.
- **Cause:** Sentry's backend user-identity API does not support `sntryu_` personal tokens on that specific endpoint.
- **Solution:** This is harmless. To verify token validity, run `sentry org list` instead.

## 2. CLI says "not authenticated" despite token in environment
- **Symptom:** Commands fail with `Not authenticated. Run sentry auth login`.
- **Cause:** The CLI has a stored, expired OAuth session in its keyring that takes precedence over `SENTRY_AUTH_TOKEN`.
- **Solution:** Add `export SENTRY_FORCE_ENV_TOKEN=1` to your shell profile (`~/.zshrc`) to force evaluation of the environment variable.

## 3. `403 Forbidden: You do not have permission`
- **Symptom:** Cannot list issues or create projects.
- **Cause:** The token was created with insufficient scopes.
- **Solution:** Recreate the user token with `org:read`, `project:read`, and `event:read` (plus `project:write` for initialization).

## 4. `DEPTH_ZERO_SELF_SIGNED_CERT` on Ingest
- **Symptom:** SDK crashes or fails silently when reporting events.
- **Cause:** ISP DNS interception on `*.ingest.*sentry.io`.
- **Solution:** Configure `tunnel: https://sentry.io/api/<projectId>/envelope/` in SDK initialization.

## 5. `sentry explore --sort` has no effect
- **Symptom:** Sorting by `-count()` on `-d errors` does not change order.
- **Cause:** The Sentry API only supports server-side sorting on the `spans` dataset.
- **Solution:** For errors, sort by frequency using `sentry issue list -s freq`.
