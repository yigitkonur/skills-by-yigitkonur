# Troubleshooting Common Errors

Diagnosis and recovery for mcpc errors organized by error code and symptom.

## Error code reference

### Exit code 0 — Success OR server-side MCP error

Command completed at the CLI level. **However, the MCP server may have returned an error.** In JSON mode, check for `isError: true` in the response:

```bash
RESULT=$(mcpc @session tools-call my-tool '{"arg":"val"}' --json)
# Exit code is 0, but this could be a server validation error:
# {"content": [{"type": "text", "text": "MCP error -32602: ..."}], "isError": true}
echo "$RESULT" | jq '.isError // false'
```

Server-side errors that return exit code 0 include: tool validation errors (missing/wrong args), tool-not-found, tool execution failures. These are MCP protocol errors, not CLI errors.

### Exit code 1 — Client error

**Cause:** Invalid arguments, unknown command, validation failure **at the mcpc CLI level** (not server-side).

| Symptom | Diagnosis | Fix |
|---|---|---|
| "Unknown command" | Typo in command name | Check `mcpc help` for valid commands |
| "Missing required argument" | Missing session name or tool name | Add `@session-name` or tool name |
| "Invalid argument format" | Wrong `:=` syntax | Use `key:=value` format |
| "Session not found" | Session name doesn't exist | List sessions with `mcpc`, reconnect |
| "Config entry not found" | Wrong entry name in config | Check config file: `cat config.json \| jq '.mcpServers \| keys'` |
| "Invalid config file" | Malformed JSON | Validate: `jq . config.json` |

### Exit code 2 — Server error

**Cause:** Tool execution failed, resource not found, server-side error.

| Symptom | Diagnosis | Fix |
|---|---|---|
| "Tool execution failed" | Tool threw an error | Check tool args, inspect error message |
| "Resource not found" | Invalid resource URI | List resources: `mcpc @s resources` |
| "Method not found" | Server doesn't support this capability | Check `mcpc @s help --json \| jq .capabilities` |
| "Internal server error" | Server bug | Check server logs, report to server maintainer |
| Tool returns `isError: true` | Tool-level error (not transport) | Inspect: `mcpc @s tools-call ... --json \| jq .` |

### Exit code 3 — Network error

**Cause:** Connection failed, timeout, DNS resolution failure.

| Symptom | Diagnosis | Fix |
|---|---|---|
| "Connection refused" | Server not running | Start the server, check port |
| "Connection timed out" | Server unreachable | Check URL, firewall, proxy settings |
| "DNS resolution failed" | Invalid hostname | Verify hostname: `nslookup <host>` |
| "Request timed out" | Tool call too slow | Increase: `--timeout 600` |
| "ECONNRESET" | Connection dropped | Check server stability, try reconnecting |
| "Socket hang up" | Premature close | Check server logs for crash |

### Exit code 4 — Auth error

**Cause:** Invalid credentials, expired token, forbidden.

| Symptom | Diagnosis | Fix |
|---|---|---|
| "Unauthorized (401)" | Missing or invalid token | `mcpc login <server>` or provide `--header` |
| "Forbidden (403)" | Insufficient permissions | Check token scopes, contact admin |
| "Token expired" | OAuth token no longer valid | `mcpc login <server>` to refresh |
| "Invalid token" | Token malformed or revoked | Re-authenticate: `mcpc logout <server> && mcpc login <server>` |
| "Incompatible auth server: does not support dynamic client registration" | OAuth metadata missing `registration_endpoint` | Server must implement a DCR endpoint. Common with Supabase-backed servers. |
| OAuth callback never received (login hangs) | Port conflict: another process intercepted the callback | `lsof -i :8000-8010 \| grep LISTEN` — stop OrbStack, Docker, or dev servers on those ports |
| Browser callback shows `{"detail":"Not Found"}` (JSON) | OrbStack or other process responded instead of mcpc | mcpc's 404 is plain text. JSON means a foreign process. Free the port and retry. |
| Browser redirects to production URL, not localhost | Redirect URL not in OAuth provider's allowlist | Add `http://localhost:*/**` to provider (e.g., Supabase Dashboard > Auth > URL Config) |
| Token exchange returns 400 | Body format or parameter name mismatch | Supabase needs JSON body + `apikey` header + `auth_code` param. Check server's token proxy. |

## Session state problems

### Session shows 🟡 disconnected

**Cause:** Bridge is alive but server is not responding.

```bash
# Check session status
mcpc

# Force restart
mcpc @session restart

# If server is down, wait for it to come back
# mcpc auto-recovers when server responds (polls every 30s)
```

### Session shows 🟡 crashed

**Cause:** Bridge process was killed or crashed.

```bash
# mcpc auto-restarts bridge on next command
mcpc @session tools-list

# If auto-restart fails, reconnect manually
mcpc @session close
mcpc <server> connect @session
```

### Session shows 🔴 unauthorized

**Cause:** Server rejected authentication.

```bash
# Re-authenticate
mcpc login <server>

# Then restart session
mcpc @session restart
```

### Session shows 🔴 expired

**Cause:** Server rejected the session ID (common with stateful servers after long idle).

```bash
# Restart creates new session
mcpc @session restart
```

### Orphaned sessions

**Cause:** Bridge process died without cleanup, or system crash.

```bash
# Clean all sessions
mcpc clean sessions

# Verify sockets are removed
ls ~/.mcpc/bridges/

# If sockets remain, remove manually
rm ~/.mcpc/bridges/*.sock
```

## Stdio transport issues

### Server fails to start

```bash
# Run the command manually to see errors
npx @modelcontextprotocol/server-filesystem /tmp/test

# Common issues:
# - Package not installed: npm install -g @package/name
# - Wrong Node version: nvm use 20
# - Missing dependencies: npm install
# - Permission denied: check file permissions
```

### Server starts but hangs

**Cause:** Server not implementing MCP handshake correctly.

```bash
# Enable verbose to see protocol negotiation
mcpc config.json:server connect @debug --verbose

# Check bridge logs
cat ~/.mcpc/logs/bridge-debug.log
```

### Environment variables not resolved

```bash
# Verify env vars exist
echo $API_KEY

# Variables in config use ${VAR} syntax
# Missing vars resolve to empty string (no error)
# Export before connecting:
export API_KEY=my-key
mcpc config.json:my-server connect @test
```

## HTTP transport issues

### TLS certificate errors

```bash
# For self-signed certs (dev only)
mcpc https://dev.internal:3000 connect @dev --insecure

# For corporate proxies with custom CAs
export NODE_EXTRA_CA_CERTS=/path/to/ca.pem
mcpc https://server.corp connect @test
```

### CORS-related issues

mcpc is a CLI tool (not browser), so CORS headers don't apply. If you see CORS errors, you're likely using a browser-based tool — switch to mcpc for CLI testing.

### Proxy issues

```bash
# Check proxy settings
echo $HTTPS_PROXY
echo $HTTP_PROXY
echo $NO_PROXY

# Bypass proxy for local servers
export NO_PROXY=localhost,127.0.0.1
mcpc localhost:3000 connect @local

# Debug proxy
mcpc https://server.com connect @test --verbose
# Look for "Using proxy: ..." in output
```

### Rate limiting

**Cause:** Too many connections or requests to the server.

```bash
# Wait between operations
mcpc @session tools-call my-tool arg:=value
sleep 1
mcpc @session tools-call my-tool arg:=value2

# Use a single session for multiple calls (don't create multiple sessions)
```

## Schema validation errors

### Schema mismatch

```bash
# Check what the tool actually returns
mcpc @session tools-get my-tool --json | jq '.inputSchema'

# Compare with expected
diff <(mcpc @session tools-get my-tool --json | jq -S '.inputSchema') \
     <(jq -S '.' expected-schema.json)

# Use compatible mode (more lenient)
mcpc @session tools-call my-tool arg:=val --schema expected.json --schema-mode compatible
```

## Performance issues

### Slow tool calls

```bash
# Increase timeout
mcpc @session tools-call slow-tool arg:=val --timeout 600

# Check if it's a connection issue
time mcpc @session ping

# Check if it's a tool issue
time mcpc @session tools-call slow-tool arg:=val --json
```

### Memory issues with large responses

```bash
# Use resource reading with max-size limit
mcpc @session resources-read "large-resource" --max-size 10485760

# Save to file instead of stdout
mcpc @session resources-read "large-resource" -o /tmp/output.bin
```

## Debugging with verbose mode

```bash
# Command-level verbose
mcpc @session tools-call my-tool arg:=val --verbose

# Session-level verbose (all commands for this session)
MCPC_VERBOSE=1 mcpc @session tools-list

# Check bridge logs for persistent issues
cat ~/.mcpc/logs/bridge-<session-name>.log

# Tail logs in real-time
tail -f ~/.mcpc/logs/bridge-<session-name>.log
```

## Nuclear options (last resort)

```bash
# Kill all bridge processes
pkill -f mcpc-bridge

# Remove all mcpc data
mcpc clean all

# Remove data directory manually
rm -rf ~/.mcpc

# Reinstall mcpc
npm uninstall -g @apify/mcpc && npm install -g @apify/mcpc
```

**Warning:** `mcpc clean all` removes saved OAuth profiles. You will need to re-authenticate after cleaning.
