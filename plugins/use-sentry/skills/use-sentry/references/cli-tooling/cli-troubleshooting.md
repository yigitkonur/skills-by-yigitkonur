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

## 6. `404 Not Found` on valid issue, project, or event lookup (Regional Host Mismatch)
- **Symptom:** `sentry-cli` or API calls return `HTTP Error 404: Not Found` when querying an existing organization, project, issue ID, or event.
- **Cause:** The organization is hosted in a dedicated regional cluster (e.g. EU region `https://de.sentry.io`) while the CLI or client defaults to the US cluster `https://sentry.io`.
- **Solution:** Add `--url https://de.sentry.io/` to CLI commands, or update `url = https://de.sentry.io/` in `~/.sentryclirc` and `sentry.properties`.

## 7. `sentry-cli issues list` fails with `A project ID or slug is required`
- **Symptom:** Running `sentry-cli issues list --status unresolved` throws `error: A project ID or slug is required (provide with --project)`.
- **Cause:** Unlike the modern `sentry` binary, legacy `sentry-cli` requires an explicit `--project <SLUG>` argument for all issue queries.
- **Solution:** Always pass `-p <project>`: `sentry-cli issues list -p my-project --status unresolved`.

## 8. `sentry-cli issues mute` ran, but errors still eat monthly quota
- **Symptom:** Issues were muted from CLI or UI, yet the organization's monthly error quota is drained rapidly.
- **Cause:** Issue muting/archiving only silences alert notifications; events are still ingested at Sentry's edge and billed.
- **Solution:** Stop ingest at the edge using Server-Side Inbound Filters (`filters:error_messages`), set a rate limit on the Client Key (DSN), or drop the errors in the SDK via `ignoreErrors` or `beforeSend`.
