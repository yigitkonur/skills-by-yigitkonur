# Authentication Precedence and Security

Critical syntax: `mcpc <target> connect @<session>`, `mcpc @session close`, `mcpc --json @session command`.

## Precedence order (highest to lowest)

1. `--header "Authorization: Bearer $TOKEN"` — Explicit header on connect
2. `--profile <name>` — Saved OAuth profile
3. Config file headers — `headers` field in mcpServers config
4. Default profile — "default" profile auto-detected for the server
5. Anonymous — No auth (omit all auth flags)

When multiple sources are present, the highest-precedence source wins. The bridge evaluates
auth at connect time and locks it for the lifetime of the session.

## Conflict rules

- `--profile <name>` + `--header "Authorization: ..."` together = ClientError (conflict)
- `--profile <name>` + non-auth headers (e.g., `--header "X-Custom: val"`) = OK (no conflict)
- If `--profile <name>` is given but doesn't exist for the server = ClientError
- Config file headers + `--header` for the same key = `--header` wins (explicit overrides config)
- Config file headers + `--profile` for Authorization = `--profile` wins (OAuth > config)

## Security properties

- Bearer tokens from `--header` are stored in OS keychain (NOT in sessions.json)
- In sessions.json, headers are redacted to `<redacted>`
- Tokens are sent to the bridge via IPC (`set-auth-credentials` message) AFTER socket is established
- Never visible in `ps` output (not passed as command-line args to bridge)
- OAuth tokens are refreshed automatically by the bridge's OAuthTokenManager
- Keychain entries are scoped per server URL, preventing cross-server token leakage
- `MCPC_HOME_DIR` can isolate credential stores per environment (CI vs local)

## When to use which method

| Scenario | Recommended method | Why |
|----------|-------------------|-----|
| Interactive development | OAuth profile (`mcpc login` + `--profile`) | Browser-based, secure, auto-refresh |
| CI/CD pipelines | `--header` + `MCPC_HOME_DIR` | No browser, secrets from env vars |
| Quick one-off test | `--header "Authorization: Bearer $TOKEN"` | Fast, no profile setup |
| Shared team config | Config file headers with `${ENV_VAR}` | Portable, env-var substituted |
| Public/open server | Omit all auth flags | Anonymous connection |
| Proxy downstream clients | `--proxy-bearer-token` | Separate from upstream auth |

## Examples

```bash
# 1. OAuth profile (interactive)
mcpc login https://mcp.example.com --profile work
mcpc https://mcp.example.com connect @test --profile work

# 2. Bearer token (CI)
mcpc https://mcp.example.com connect @ci-test \
  -H "Authorization: Bearer $MCP_TOKEN"

# 3. Config file headers
# In ~/.vscode/mcp.json:
# { "mcpServers": { "server": { "url": "https://...", "headers": { "Authorization": "Bearer ${MCP_TOKEN}" }}}}
mcpc ~/.vscode/mcp.json:server connect @config-test

# 4. Default profile (auto-detected)
mcpc login https://mcp.example.com  # saves as "default"
mcpc https://mcp.example.com connect @auto  # auto-uses "default" profile

# 5. Anonymous
mcpc https://public-server.com connect @anon

# 6. Multiple headers (auth + non-auth, no conflict)
mcpc https://mcp.example.com connect @multi \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Request-Id: test-123" \
  -H "X-Tenant: acme"
```

## Verifying auth state

```bash
# Check which profile a session uses
mcpc --json | jq '.sessions[] | {name, profileName}'

# List all profiles
mcpc --json | jq '.profiles'

# Check if session is authenticated
mcpc --json @session | jq '._mcpc.profileName // "anonymous"'

# Inspect redacted headers stored for a session
mcpc --json @session | jq '._mcpc.headers'
```

## Common auth issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Exit code 4 on connect | Token expired or invalid | Re-login or refresh token |
| "Profile not found" | Typo in `--profile` name | Check `mcpc --json \| jq '.profiles'` |
| "Conflicting auth" | `--profile` + `--header "Authorization"` | Use one or the other, not both |
| Session shows "unauthorized" | Server returned 401/403 | `mcpc login <server>` then `mcpc @session restart` |
| Token visible in process list | Old binary or wrong invocation | Upgrade mcpc; always pass via `-H` flag |
| Keychain prompt in CI | Keychain not unlocked | Set `MCPC_HOME_DIR` to use file-based store |

## Auth lifecycle

When a session is created with auth:

1. `mcpc` establishes the IPC socket with the bridge (no credentials yet)
2. `set-auth-credentials` IPC message delivers token to bridge in-memory
3. Bridge stores token in OS keychain under the server URL key
4. Bridge injects `Authorization` header into every outbound HTTP request
5. On OAuth expiry, OAuthTokenManager refreshes silently; session stays alive
6. On session close (`mcpc @session close`), keychain entry is NOT deleted — reusable on reconnect

To fully revoke stored credentials:

```bash
# Revoke and delete a saved OAuth profile
mcpc logout https://mcp.example.com --profile work

# Force re-authentication on next connect (clears cached token)
mcpc @session restart --profile work
```
