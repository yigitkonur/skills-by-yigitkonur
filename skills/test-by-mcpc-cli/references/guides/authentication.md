# Authentication Deep Dive

Credential storage, OAuth 2.1 flow, bearer token auth, profile resolution, token refresh, and CI/headless configuration for mcpc.

## Three credential storage layers

mcpc uses a layered credential system. Sensitive values never touch sessions.json.

### Layer 1: `~/.mcpc/profiles.json` — OAuth metadata (no secrets)

Stores metadata about OAuth profiles: server host, profile name, client ID, scopes, timestamps. Never contains tokens or secrets. File mode: `0600`.

```json
{
  "mcp.example.com": {
    "default": {
      "host": "mcp.example.com",
      "profileName": "default",
      "clientId": "mcpc-cli",
      "scopes": ["read", "write"],
      "createdAt": "2025-03-20T10:00:00.000Z",
      "refreshedAt": "2025-03-20T12:30:00.000Z",
      "userInfo": {
        "sub": "user-123",
        "name": "Test User",
        "email": "test@example.com"
      }
    }
  }
}
```

The `userInfo` field is decoded from the OIDC `id_token` JWT. This is informational only — mcpc does not verify the JWT signature. It extracts claims using base64 decode of the payload segment.

### Layer 2: OS keychain (`@napi-rs/keyring`) — all sensitive values

Primary storage for all credentials. Uses the platform-native keychain:

- **macOS**: Keychain Access (via Security framework)
- **Linux**: Secret Service (GNOME Keyring / KWallet)
- **Windows**: Windows Credential Manager

All keychain entries use the service name `mcpc`.

### Layer 3: `~/.mcpc/credentials.json` — file fallback

When the OS keychain is unavailable (headless Linux, Docker, CI environments), mcpc automatically falls back to file-based credential storage. File mode: `0600`.

This happens silently — no warning is shown. The fallback is detected when `@napi-rs/keyring` throws on first access attempt.

```json
{
  "auth-profile:mcp.example.com:default:tokens": "{\"access_token\":\"eyJ...\",\"refresh_token\":\"dGV...\",\"expires_at\":1711000000}",
  "session:my-session:headers": "{\"Authorization\":\"Bearer abc123\"}"
}
```

## Keychain account naming

All keychain entries use the service name `mcpc` with the following account key patterns:

| Purpose | Account key pattern | Value stored |
|---|---|---|
| OAuth client info | `auth-profile:<host>:<profileName>:client` | JSON: `{clientId, clientSecret, registrationUri}` |
| OAuth tokens | `auth-profile:<host>:<profileName>:tokens` | JSON: `{access_token, refresh_token, expires_at, token_type}` |
| Session headers | `session:<sessionName>:headers` | JSON: `{"Authorization": "Bearer ..."}` |
| Proxy bearer token | `session:<sessionName>:proxy-bearer-token` | Plain string: the proxy token value |

### Examples

```
Service: mcpc
Account: auth-profile:mcp.example.com:default:client
Value:   {"clientId":"mcpc-cli","clientSecret":"s3cr3t","registrationUri":"https://mcp.example.com/register"}

Service: mcpc
Account: auth-profile:mcp.example.com:default:tokens
Value:   {"access_token":"eyJhbG...","refresh_token":"dGVz...","expires_at":1711000000,"token_type":"Bearer"}

Service: mcpc
Account: session:my-prod:headers
Value:   {"Authorization":"Bearer my-api-token-here"}
```

## OAuth 2.1 flow

### Full flow walkthrough

```bash
mcpc login https://mcp.example.com --profile myprofile
```

Step-by-step:

1. **Port scanning**: mcpc scans ports 8000 through 8099 for an available port to use as the OAuth callback listener.

2. **HTTP callback server**: Starts a temporary HTTP server on `127.0.0.1:<port>` to receive the authorization code.

3. **User prompt**: Prints a message and waits for the user to press Enter before opening the browser. This prevents the browser from opening before the callback server is ready.

4. **Browser launch**: Opens the authorization URL in the default browser using platform-specific commands:
   - macOS: `open`
   - Linux: `xdg-open`
   - Windows: `start`

5. **User authenticates**: The user completes authentication in the browser (login, consent, MFA, etc.).

6. **Callback received**: Browser redirects to `http://127.0.0.1:<port>/callback?code=...`. The callback server captures the authorization code.

7. **Token exchange**: mcpc calls the MCP SDK's `sdkAuth()` function to exchange the authorization code for tokens via the server's token endpoint.

8. **Credential storage**: Tokens stored in keychain under `auth-profile:<host>:<profileName>:tokens`. Client info stored under `auth-profile:<host>:<profileName>:client`.

9. **Profile metadata**: Non-sensitive profile info written to `~/.mcpc/profiles.json`. User info decoded from the OIDC `id_token` JWT payload (no signature verification — informational only).

10. **Callback server shutdown**: The temporary HTTP server closes after receiving the code.

### OAuth with custom client credentials

```bash
mcpc login https://mcp.example.com \
  --profile work \
  --client-id my-custom-app \
  --client-secret "$CLIENT_SECRET" \
  --scope "read write admin"
```

Custom client credentials are stored in the keychain under the `:client` key. If the server supports dynamic client registration and no custom credentials are provided, mcpc registers automatically.

## Profile resolution logic

When connecting to a server, mcpc resolves authentication in this order:

### Case 1: Explicit profile (`--profile <name>`)

```bash
mcpc https://mcp.example.com connect @test --profile work
```

- Looks up `profiles.json[host][profileName]`
- If profile exists: loads tokens from keychain, attaches to session
- If profile does NOT exist: throws `ClientError` ("Profile 'work' not found for host 'mcp.example.com'")
- This is a hard error — mcpc will not silently fall back to anonymous

### Case 2: Default (no auth flags)

```bash
mcpc https://mcp.example.com connect @test
```

- Checks if a profile named `"default"` exists for this host in profiles.json
- If "default" profile exists: uses it (same as `--profile default`)
- If no default profile: connects anonymously (no auth headers)

### Case 3: Explicit headers (`--header`)

```bash
mcpc https://mcp.example.com connect @test \
  --header "Authorization: Bearer $TOKEN"
```

- Headers are sent to the bridge via IPC after socket connection (never via CLI arguments that would appear in `ps` output)
- Headers stored in keychain under `session:<sessionName>:headers`
- In sessions.json, headers appear as `<redacted>`

### Case 4: Conflict (`--profile` + `--header "Authorization: ..."`)

```bash
# This is an error!
mcpc https://mcp.example.com connect @test \
  --profile work \
  --header "Authorization: Bearer $TOKEN"
```

Throws `ClientError`: combining `--profile` with an Authorization header creates ambiguity about which credentials take precedence. mcpc refuses to guess.

Note: non-Authorization headers (e.g., `--header "X-Tenant: abc"`) can be combined with `--profile` without conflict.

## Token refresh

### OAuthTokenManager in the bridge

When a session uses OAuth, the bridge sets up an `OAuthTokenManager` that handles automatic token refresh:

**onBeforeRefresh callback**: Before attempting a refresh, reloads tokens from the keychain. This handles the case where another session sharing the same profile has already refreshed the token. Without this, two sessions could race to refresh and one would use a revoked refresh token.

**onTokenRefresh callback**: After a successful refresh, persists the new tokens to the keychain and updates `refreshedAt` in profiles.json. Other sessions sharing the same profile will pick up the new tokens on their next `onBeforeRefresh`.

### Refresh flow

1. MCP server returns 401 (token expired)
2. Transport layer triggers OAuthTokenManager
3. onBeforeRefresh: read latest tokens from keychain
4. Check if keychain tokens are still valid (another session may have already refreshed)
5. If already refreshed: use the new access_token, skip refresh
6. If still expired: send refresh_token to server's token endpoint
7. Receive new access_token + refresh_token
8. onTokenRefresh: write new tokens to keychain, update profiles.json refreshedAt
9. Retry original request with new access_token

### Multi-session token rotation safety

Because all sessions sharing a profile read from and write to the same keychain entry, mcpc avoids the "thundering herd" refresh problem:

```
Session A: onBeforeRefresh → reads tokens from keychain → expired → refreshes → writes new tokens
Session B: onBeforeRefresh → reads tokens from keychain → finds NEW tokens from A → uses them → no refresh needed
```

## Bearer token auth

### Usage

```bash
mcpc https://mcp.example.com connect @test \
  -H "Authorization: Bearer $MCP_TOKEN"
```

Short form `-H` is equivalent to `--header`.

### Security properties

1. **Never in `ps` output**: The token is not passed as a CLI argument to the bridge. It is sent via IPC after the Unix socket connection is established.

2. **Keychain storage**: Stored in keychain under `session:<sessionName>:headers`. Retrieved by the bridge on startup and on auto-restart.

3. **Redacted in sessions.json**: The sessions.json file shows `"headers": "<redacted>"` — never the actual token value.

4. **Per-session**: Bearer tokens are scoped to a specific session name, not shared across sessions.

### Multiple custom headers

```bash
mcpc https://mcp.example.com connect @test \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Request-Id: test-run-42" \
  -H "X-Tenant-Id: my-org"
```

All headers are stored together in the keychain entry as a JSON object.

## CI/headless environments

### No keychain available

In environments without a desktop keychain (CI runners, Docker, headless Linux), mcpc automatically falls back to `~/.mcpc/credentials.json`. No configuration needed.

### Recommended CI approach: bearer token via header

```bash
# Use --header instead of OAuth for CI (no browser available)
mcpc https://mcp.example.com connect @ci-test \
  --header "Authorization: Bearer $MCP_TOKEN"
```

### Isolated test environments

Use `MCPC_HOME_DIR` to prevent CI runs from interfering with each other or with local development:

```bash
export MCPC_HOME_DIR="/tmp/mcpc-ci-$(date +%s)"
mcpc https://mcp.example.com connect @ci \
  --header "Authorization: Bearer $TOKEN"
mcpc @ci tools-list --json
mcpc @ci close
rm -rf "$MCPC_HOME_DIR"
```

### GitHub Actions example

```yaml
name: MCP Server Tests
on: [push, pull_request]

jobs:
  test-mcp:
    runs-on: ubuntu-latest
    env:
      MCPC_HOME_DIR: /tmp/mcpc-ci
      MCPC_JSON: 1
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install mcpc
        run: npm install -g @apify/mcpc

      - name: Start MCP server
        run: |
          npm run build
          npm run start &
          sleep 5

      - name: Test with bearer token
        env:
          MCP_TOKEN: ${{ secrets.MCP_API_TOKEN }}
        run: |
          mcpc localhost:3000 connect @ci-test \
            --header "Authorization: Bearer $MCP_TOKEN"

          # Verify connectivity
          mcpc @ci-test ping

          # Verify tools
          TOOL_COUNT=$(mcpc @ci-test tools-list --json | jq 'length')
          echo "Found $TOOL_COUNT tools"
          [ "$TOOL_COUNT" -gt 0 ] || exit 1

          # Smoke test first tool
          FIRST_TOOL=$(mcpc @ci-test tools-list --json | jq -r '.[0].name')
          mcpc @ci-test tools-get "$FIRST_TOOL" --json

          mcpc @ci-test close

      - name: Cleanup
        if: always()
        run: rm -rf /tmp/mcpc-ci
```

## Testing auth configurations

### List profiles

```bash
# All profiles across all servers
mcpc --json | jq '.profiles'

# Profiles for a specific server
mcpc --json | jq '.profiles["mcp.example.com"]'

# Profile details
mcpc --json | jq '.profiles["mcp.example.com"]["default"]'
```

### Verify session auth method

```bash
# Check what auth a session is using
mcpc --json @test | jq '._mcpc | {profile, headers}'
# profile: "default" (OAuth) or null (bearer/anonymous)
# headers: "<redacted>" (bearer provided) or null (OAuth or anonymous)
```

### Test all three auth methods against the same server

```bash
# 1. Bearer token
mcpc https://server.com connect @bearer-test \
  -H "Authorization: Bearer $TOKEN"
mcpc @bearer-test tools-list --json | jq 'length'
mcpc @bearer-test close

# 2. OAuth profile
mcpc login https://server.com --profile testprofile
mcpc https://server.com connect @oauth-test --profile testprofile
mcpc @oauth-test tools-list --json | jq 'length'
mcpc @oauth-test close

# 3. Anonymous (no flags)
mcpc https://server.com connect @anon-test
mcpc @anon-test tools-list --json | jq 'length'
mcpc @anon-test close
```

### Verify token is not leaked

```bash
# sessions.json should never contain actual tokens
cat ~/.mcpc/sessions.json | jq '."my-session".headers'
# Expected: "<redacted>" or null

# Process list should not show tokens
ps aux | grep mcpc
# Tokens are sent via IPC, not command-line arguments
```

## Logout and profile cleanup

```bash
# Remove default profile for a server
mcpc logout https://mcp.example.com

# Remove named profile
mcpc logout https://mcp.example.com --profile work

# Remove all profiles (nuclear)
mcpc clean profiles

# Remove everything including profiles
mcpc clean all
```

Logout removes:
- Profile entry from profiles.json
- Client credentials from keychain (`auth-profile:<host>:<profile>:client`)
- Tokens from keychain (`auth-profile:<host>:<profile>:tokens`)

Active sessions using the deleted profile continue working until their current access_token expires. They will fail on the next token refresh.

## Common auth pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| 401 on connect | No auth or wrong token | Provide `--header` or `mcpc login` first |
| 403 on tool call | Token lacks required scope | Re-login with `--scope "read write admin"` |
| "Profile not found" | Typo in `--profile` name | Check: `mcpc --json \| jq '.profiles'` |
| "Cannot combine --profile with Authorization header" | Conflicting auth flags | Use one or the other, not both |
| Token expired in CI | Static token has time limit | Rotate token in CI secrets |
| OAuth login hangs | Port 8000-8099 all in use | Free a port or kill stale processes |
| "Browser open failed" | Headless environment | Use `--header` auth instead of OAuth |
| Keychain access denied | macOS Keychain prompt denied | Grant access in Keychain Access.app |
| Credentials lost after `mcpc clean all` | Clean removes profiles | Re-run `mcpc login` after cleaning |
