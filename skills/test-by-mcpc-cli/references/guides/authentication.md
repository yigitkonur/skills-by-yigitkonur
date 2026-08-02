# Authentication

Use this guide for OAuth (interactive, client-credentials, id-jag), explicit bearer headers, anonymous mode, and x402 interactions.

## Core commands

```bash
mcpc login https://mcp.example.com/mcp
mcpc login https://mcp.example.com/mcp --profile work --scope "read write"
mcpc login https://mcp.example.com/mcp --client-id cli --client-secret secret
mcpc connect https://mcp.example.com/mcp @secured --profile work
mcpc connect https://mcp.example.com/mcp @anon --no-profile
mcpc connect https://mcp.example.com/mcp @header -H 'Authorization: Bearer token'
```

## Current rules that matter

- `--profile <name>` selects a saved OAuth profile explicitly
- omitting both `--profile` and `--no-profile` allows `mcpc` to auto-pick the `default` profile when one exists for that server
- `--no-profile` disables that auto-pick and forces anonymous connection behavior
- explicit `--header` values override profile-based auth on the wire
- `--x402` skips default-profile auto-detection unless `--profile` is explicit

## Client registration (how `mcpc` identifies itself to the server)

`mcpc login` picks whichever approach the authorization server advertises:

1. **CIMD** (Client ID Metadata Documents) — the default. `mcpc`'s hosted document at
   `https://apify.github.io/mcpc/client-metadata.json` identifies every `mcpc` install as
   one client. Override with `--client-metadata-url <url>`, disable with `--no-client-metadata-url`.
2. **Pre-registration** — pass `--client-id` (and `--client-secret` if issued). If the
   client's redirect URI uses `localhost` (e.g. `localhost:3118`), match it with
   `--callback-host localhost --callback-port 3118`.
3. **DCR** (Dynamic Client Registration) — fallback when CIMD is unsupported/disabled and
   the server exposes a `registration_endpoint`.

The OAuth callback listens on `127.0.0.1` by default (`--callback-host localhost` to switch);
`--callback-port` picks the loopback port (default one of `13316`/`31613`/`16133`).

## Machine-to-machine and enterprise SSO grants

`--grant <type>` on `mcpc login` selects the OAuth grant: `authorization-code` (default,
interactive browser), `client-credentials`, or `id-jag`.

```bash
# CI/CD, daemons — no browser
mcpc login mcp.example.com --grant client-credentials \
  --client-id my-svc --client-secret s3cr3t --scope "read write"
mcpc login mcp.example.com --grant client-credentials \
  --client-id my-svc --client-key ./key.pem   # private_key_jwt (RFC 7523)

# Enterprise-managed SSO via the org's IdP (e.g. Okta) — no per-server consent screens
mcpc login mcp.example.com --grant id-jag \
  --idp https://acme.okta.com --idp-client-id idp-client \
  --client-id mcp-client --client-secret s3cr3t
```

`--client-secret` uses `client_secret_basic`; `--client-key`/`--client-key-alg` (default
`RS256`) signs a `private_key_jwt` assertion instead. `--token-endpoint <url>` pins the
token endpoint when a `client-credentials` server has no discoverable metadata. For
`id-jag`, `--idp-client-id`/`--idp-client-secret` register at the enterprise IdP separately
from `--client-id`/`--client-secret` at the MCP server's authorization server; `--idp-scope`
overrides the SSO's OIDC scopes (default `"openid profile email offline_access"`) while
`--scope` still requests MCP-server scopes. The resulting profile connects like any other:
`mcpc connect mcp.example.com @svc --profile default`.

## Headless or remote login

`mcpc login` prefers opening a browser, but it is not browser-only.
If the browser cannot open, `mcpc` prints a URL you can open manually and then asks you to paste the callback URL back into the CLI.

## JSON inspection

`mcpc --json` exposes profiles as an array.
Filter by server URL and profile name instead of assuming a host-keyed object.

```bash
mcpc --json | jq '.profiles[] | select(.serverUrl == "https://mcp.example.com/mcp" and .name == "default")'
```

Current profile metadata is flat and typically includes fields such as `name`, `serverUrl`, `authType`, `oauthGrant` (absent means `authorization_code`), `scopes`, and timestamps.
Do not document the old nested `userInfo` shape.

## Storage notes

- OAuth credentials prefer OS keychain storage when available
- `~/.mcpc/credentials.json` is the fallback when keychain integration is unavailable
- per-session headers are not OAuth profiles; they are stored with the session and cleaned with session cleanup

Route precedence edge cases to `references/patterns/auth-precedence.md`.
