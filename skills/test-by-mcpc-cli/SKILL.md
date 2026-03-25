---
name: test-by-mcpc-cli
description: Use skill if you are testing or debugging MCP servers with mcpc CLI across stdio, HTTP stateless, and HTTP stateful transports — tool calling, schema validation, and automated test scripts.
---

# Test MCP Server with mcpc

Test and debug any MCP server using the `mcpc` CLI. Covers stdio, HTTP stateless, and HTTP stateful transports with session management, tool discovery, schema validation, and scripted automation.

## Trigger boundary

**Use this skill when:**

- Testing an MCP server's tools, resources, or prompts via CLI
- Debugging MCP transport issues (stdio, SSE, streamable HTTP)
- Debugging OAuth login failures with `mcpc login` (port conflicts, DCR, Supabase traps)
- Validating MCP server behavior before deployment
- Inspecting what an MCP server exposes (capabilities, schemas)
- Writing automated test scripts for MCP servers
- Setting up mcpc for the first time

**Do NOT use this skill when:**

- Building an MCP server from scratch (use `build-mcp-use-server`)
- Building an MCP client application (use `build-mcp-use-client`)
- Auditing MCP server code quality (use `optimize-mcp-server`)
- Testing Claude skills (use `enhance-skill-by-derailment`)

## Prerequisites

```bash
mcpc --version
# Expected: mcpc X.Y.Z
# If not found, read references/guides/installation.md
```

Node.js 20+ required. Install mcpc: `npm install -g @apify/mcpc`.

## Version boundary

This skill is written against `mcpc 0.1.11`.

Before using any older snippet, verify it against `mcpc --help`. In `0.1.11`, do **not** assume support for these older examples:

- `tools-call --task` / `--detach`
- `tasks-list`, `tasks-get`, `tasks-cancel`
- `mcpc login ... --scope`, `--client-id`, `--client-secret`
- `resources-read -o <file>` or `resources-read --max-size`
- `--insecure`

Use shell redirection to save resources:

```bash
mcpc @session resources-read "https://example.com/data" > output.json
```

## Persistent authenticated sessions (MUST READ for OAuth servers)

**The #1 user complaint:** "I have to re-authenticate every time I test an OAuth MCP server."

mcpc already solves this — OAuth tokens are stored in macOS Keychain and auto-refresh indefinitely. But you must follow this protocol to avoid forcing unnecessary re-logins.

### Step 0: ALWAYS check for existing sessions before connecting

Before running any `mcpc <server> connect` command, check existing state:

```bash
# 1. List all active sessions — look for a live session to the target server
mcpc

# 2. Check saved OAuth profiles — if a profile exists, login is NOT needed
mcpc --json | jq '.profiles'
```

**Decision logic:**

```
Is there a live @session for this server?
├── YES → Reuse it: `mcpc @session ping` to verify, then proceed to Step 2
├── CRASHED → Reconnect (no re-login): `mcpc <server> connect @session`
│   (mcpc re-injects tokens from Keychain automatically)
└── NO session exists
    ├── Does an OAuth profile exist for this server host?
    │   ├── YES → Connect without login: `mcpc <server> connect @session`
    │   └── NO → First-time setup: `mcpc login <server>` then connect
    └── Bearer token? → `mcpc <server> connect @session -H "Authorization: Bearer $TOKEN"`
```

### Why you never need to re-login

```
Login once → mcpc saves access_token + refresh_token in macOS Keychain
                ↓
Token expires (~1h) → bridge auto-sends refresh_token to server
                ↓
Server returns NEW access_token + NEW refresh_token
                ↓
Keychain updated → session continues indefinitely
                ↓
Each refresh resets the refresh_token expiry clock
(Supabase: 60 days, Google production: 6 months)
→ Regular usage = never re-login
```

Bridge crash? mcpc auto-restarts and re-injects credentials from Keychain.
Computer reboot? `mcpc <server> connect @session` — profile persists in Keychain, no login needed.

Read `references/guides/authentication.md` § Login once, test forever for the full explanation.

### Save session names for cross-conversation reuse

After establishing an authenticated session, **always recommend** saving the session info to the project's `CLAUDE.md` or `AGENTS.md`:

```markdown
## MCP Testing Sessions (persistent — do not re-login)
- Server: https://mcp.example.com/mcp → Session: `@my-mcp`
- Auth: OAuth profile "default" (auto-refreshes via macOS Keychain)
- Reconnect if crashed: `mcpc https://mcp.example.com/mcp connect @my-mcp`
- Check status: `mcpc @my-mcp ping`
```

This way, the next AI conversation reads CLAUDE.md, finds the session name, runs `mcpc @my-mcp ping`, and continues testing — zero re-authentication.

### When the user says "I don't want to authenticate again"

Follow this exact sequence:

1. Check if a profile already exists: `mcpc --json | jq '.profiles'`
2. If yes: explain that tokens auto-refresh, connect using existing profile
3. If no: run `mcpc login <server>` (one-time only), then connect
4. Save session name to CLAUDE.md/AGENTS.md (see template above)
5. Confirm: "This session will persist across conversations. You won't need to login again."

## Decision tree

```
What transport does the server use?
├── Stdio (local process — npm package, Python script, binary)
│   └── Step 1A: Connect via config file
├── HTTP (remote URL endpoint)
│   ├── Stateless (SSE, no session persistence)
│   │   └── Step 1B: Connect to URL, verify independence
│   └── Stateful (streamable HTTP, MCP-Session-Id)
│       └── Step 1C: Connect to URL, verify session persistence
├── Unknown transport
│   └── Try HTTP first (most remote servers), stdio for local packages
└── Just need a command reference
    └── Read references/commands/quick-reference.md
```

## Core workflow

### Step 1A: Test stdio server

Stdio servers are local processes. Define them in a JSON config file, then connect.

**Create a config file** (or use an existing `~/.vscode/mcp.json`):

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/ABSOLUTE/CANONICAL/TEST-DIR"],
      "env": { "DEBUG": "true" }
    }
  }
}
```

If you are testing a filesystem-backed stdio server on macOS, canonicalize the path first and reuse that exact path everywhere:

```bash
TEST_DIR="$(realpath /tmp/test-dir)"
```

`/tmp/...` often resolves to `/private/tmp/...`; if the server allowlists the canonical path, tool calls using the alias path will fail. Put the `realpath` result into the config file too instead of leaving `/tmp/...` in `args`.

**Connect:**

```bash
# Connect using config file entry
mcpc --config /path/to/config.json my-server connect @test-stdio

# Or reference VS Code config
mcpc --config ~/.vscode/mcp.json filesystem connect @test-stdio
```

**Verify the server started:**

```bash
mcpc @test-stdio ping
mcpc @test-stdio help
```

If the server fails to start, run the command manually first to check for errors:

```bash
npx @modelcontextprotocol/server-filesystem "$TEST_DIR"
```

Read `references/guides/stdio-testing.md` for config format, env vars, and debugging.

Proceed to Step 2.

### Step 1B: Test HTTP stateless server (SSE)

Stateless servers treat each connection independently. No session state persists between connections.

```bash
# Connect to remote server
mcpc https://mcp.example.com connect @test-sse

# With authentication
mcpc https://mcp.example.com connect @test-sse \
  --header "Authorization: Bearer $MCP_TOKEN"

# With OAuth (interactive login first)
mcpc login https://mcp.example.com
mcpc https://mcp.example.com connect @test-sse
```

**Verify statelessness:**

```bash
# Session 1: perform an action
mcpc @test-sse tools-list
mcpc @test-sse tools-call create-item name:=test-item
mcpc @test-sse close

# Session 2: reconnect — no state from session 1
mcpc https://mcp.example.com connect @test-sse-2
mcpc @test-sse-2 tools-call list-items --json
# If server is truly stateless, result should not depend on session 1
mcpc @test-sse-2 close
```

Read `references/guides/http-testing.md` for auth, proxy, and TLS details.

Proceed to Step 2.

### Step 1C: Test HTTP stateful server (streamable HTTP)

Stateful servers maintain session state via `MCP-Session-Id` header (protocol version 2025-11-25+).

```bash
# Connect to stateful server
mcpc https://mcp.example.com connect @test-stateful
```

**Verify statefulness:**

```bash
# 1. Check session info — look for protocol version and session ID
mcpc --json @test-stateful | jq '{
  protocolVersion: .protocolVersion,
  mcpcSession: ._mcpc,
  serverInfo: .serverInfo
}'

# 2. Perform stateful operation
mcpc @test-stateful tools-call create-item name:=test-item

# 3. Verify state persists within same session
mcpc @test-stateful tools-call list-items --json
# Should include the item created above

# 4. Test session restart (drops session, creates new one)
mcpc @test-stateful restart
mcpc @test-stateful tools-call list-items --json
# Server decides if state persists across sessions

# 5. Test session keepalive (mcpc pings every 30s automatically)
mcpc @test-stateful ping
```

**Key difference from stateless:** The `MCP-Session-Id` header enables the server to track state. Mcpc auto-detects the protocol version during handshake — you do not need to configure this.

Read `references/guides/http-testing.md` § Stateful Sessions for reconnection, expiry, and resumption.

**Do not skip transport verification.** It is tempting to jump straight to tool testing, but transport-level issues (session drops, keepalive failures, protocol mismatches) are invisible from tool calls alone. If the ping output shows `MCP: 2025-11-25`, you are on a stateful streamable HTTP server — run the verification steps above before proceeding.

Proceed to Step 2.

### Step 2: Discover server capabilities

```bash
# List tools (summary)
mcpc @session tools

# List tools with full input schemas
mcpc @session tools --full

# Get one tool's details and schema
mcpc @session tools-get tool-name

# List resources
mcpc @session resources

# List resource templates
mcpc @session resources-templates-list

# List prompts
mcpc @session prompts
```

### Before calling tools — check the schema first

Before jumping to tool calls, inspect the schema for each tool you plan to test. This prevents wasted calls with wrong argument types.

```bash
# WRONG — too shallow, hides array item types and min/max constraints:
# mcpc @session tools-get my-tool --json | jq '.inputSchema.properties | to_entries[] | {key, type: .value.type}'
# This only shows {"key":"items","type":"array"} — useless for knowing what the array contains or how many items are required.

# RIGHT — show array item types, minItems/maxItems, and required sub-fields:
mcpc @session tools-get my-tool --json | jq '
  .inputSchema.properties | to_entries[] | {
    key,
    type: .value.type,
    items: (if .value.type == "array" then (.value.items.type // .value.items) else null end),
    min: .value.minItems,
    max: .value.maxItems
  }'

# Or just dump the full schema — it's rarely that long:
mcpc @session tools-get my-tool --json | jq '.inputSchema'
```

**Why this matters:** Most real-world MCP tools take array parameters with constraints like `minItems: 3` or items that are objects (not strings). A shallow type check shows `"type": "array"` and nothing else — you'll guess wrong, get a validation error, and waste a round trip. Always check what the array *contains* and how many items are required.

**Critical rule:** `key:=value` syntax only produces **scalar values** (string, number, boolean, null). It **cannot** produce arrays or nested objects. Most real-world MCP tools take array arguments — always check the schema first.

### Step 3: Test tool calls

```bash
# Call with key:=value arguments — ONLY for scalar params (string, number, boolean)
mcpc @session tools-call my-tool count:=10 enabled:=true name:=hello

# Call with inline JSON — REQUIRED for arrays and nested objects
mcpc @session tools-call my-tool '{"keywords": ["term1", "term2"], "limit": 10}'

# key:=value CAN pass arrays via JSON literal (note shell quoting)
mcpc @session tools-call my-tool keywords:='["term1","term2"]' limit:=10

# Call with piped JSON input
echo '{"keywords": ["term1", "term2"]}' | mcpc @session tools-call my-tool

# Validate response against schema
mcpc @session tools-call my-tool '{"arg": "value"}' --schema expected.json

# Strict schema validation (fails on extra fields)
mcpc @session tools-call my-tool '{"arg": "value"}' --schema expected.json --schema-mode strict
```

**Argument auto-parsing rules:**

| Input | Parsed as | Type |
|---|---|---|
| `count:=10` | `10` | number |
| `enabled:=true` | `true` | boolean |
| `name:=hello` | `"hello"` | string |
| `id:='"123"'` | `"123"` | string (forced) |
| `items:='[1,2,3]'` | `[1,2,3]` | array (JSON literal) |
| `config:='{"k":"v"}'` | `{"k":"v"}` | object (JSON literal) |
| `'{"full":"json"}'` | full object | inline JSON (all-or-nothing) |

**When to use which format:**
- Tool params are all scalars → `key:=value` is fine
- Tool has any array/object params → use inline JSON or `key:='[...]'` with quoting
- Complex nested args → use inline JSON or pipe from stdin

Read `references/guides/tool-resource-testing.md` for advanced patterns.
Read `references/patterns/argument-parsing.md` for the full type coercion table and shell quoting rules.

### Step 4: Test resources and prompts

```bash
# Read a resource
mcpc @session resources-read "file:///path/to/resource"

# Save resource to file
mcpc @session resources-read "https://example.com/data" > output.json

# Subscribe to resource updates (registers interest, returns immediately)
# Returns: {"subscribed": true, "uri": "..."} — does NOT stream in CLI mode
# To receive push notifications, use shell mode: mcpc @session shell
mcpc @session resources-subscribe "file:///watched-path"

# Get a prompt with arguments
mcpc @session prompts-get my-prompt arg1:=value1 arg2:=value2
```

`resources-list`, `resources-templates-list`, and `prompts-list` are optional MCP capabilities. If you get `MCP error -32601: Method not found`, record "capability not implemented" and continue. That is not a transport failure.

### Step 5: Use JSON mode for scripted tests

**Exploratory testing vs scripted testing:** When you are testing a server for the first time (exploratory), show full output — do not truncate with jq slicing like `.text[:300]`. You will lose critical information (e.g., whether comments were returned, what the error details said) and be forced to re-run calls. Save truncation for automated CI scripts where you only need pass/fail. During exploratory testing, use `jq -r '.content[0].text'` to see the full response, or pipe through `head -100` if it's truly huge.

```bash
# All commands support --json for machine-readable output
mcpc @session tools-list --json | jq '.[].name'
mcpc @session tools-call my-tool '{"arg":"val"}' --json | jq -r '.content[0].text'
mcpc @session resources-list --json | jq '.[].uri'

# Check tool count
mcpc @session tools-list --json | jq 'length'

# Extract specific tool schema
mcpc @session tools-get my-tool --json | jq '.inputSchema'
```

**JSON response shapes differ by command — know the envelope:**

| Command | Success shape | Key fields |
|---|---|---|
| `tools-list` | bare array `[{name, inputSchema, ...}]` | `.[]` |
| `tools-call` | `{content: [{type, text}]}` | `.content[0].text` |
| `tools-call` (error) | `{content: [...], isError: true}` | `.isError` |
| `resources-read` | `{contents: [{uri, mimeType, text}]}` | `.contents[0].text` (plural!) |
| `resources-list` | bare array `[{uri, name}]` | `.[]` |

Note: `tools-call` success has `content` (singular); `resources-read` has `contents` (plural). Servers may include additional fields like `_meta` or `structuredContent` — these are server-specific extensions, not part of the base MCP spec.

**Always check `isError` when scripting — exit codes alone are not reliable:**

```bash
RESULT=$(mcpc @session tools-call my-tool '{"arg":"val"}' --json)
if echo "$RESULT" | jq -e '.isError // false' 2>/dev/null | grep -q true; then
  echo "TOOL ERROR: $(echo "$RESULT" | jq -r '.content[0].text')"
  exit 1
fi
```

Read `references/guides/scripting-automation.md` for full test scripts and CI integration.
Read `references/patterns/output-formatting.md` for exact JSON shapes of every command.

### Step 6: Cleanup

```bash
mcpc @session close           # Close one session
mcpc                         # List active sessions
mcpc --clean=sessions          # Clean all sessions
mcpc --clean=all               # Clean sessions + profiles + logs
```

## Transport comparison

| Aspect | Stdio | HTTP Stateless (SSE) | HTTP Stateful (Streamable) |
|---|---|---|---|
| Server location | Local process | Remote URL | Remote URL |
| Config source | JSON config file | Direct URL | Direct URL |
| Connection | stdin/stdout pipes | Independent HTTP requests | Persistent HTTP + MCP-Session-Id |
| Session persistence | Process lifetime | None | Server-managed |
| Auth needed | No (local) | Optional (bearer/OAuth) | Optional (bearer/OAuth) |
| Reconnection | Restart process | New connection | Auto-resume via session ID |
| Test isolation | Kill process | Independent by design | Restart session |
| Typical use | Dev/local testing | Simple remote APIs | Production servers |
| Protocol version | Any | Any | 2025-11-25+ |
| Keep-alive | Process stays alive | N/A | Auto-ping every 30s |

## Key patterns

### Quick smoke test

```bash
mcpc <server> connect @smoke && \
mcpc @smoke ping && \
mcpc @smoke tools-list && \
mcpc @smoke tools-call <first-tool> <minimal-args> && \
mcpc @smoke close
```

**Testing discipline:**
- **Use real data, not fabricated inputs.** If a tool takes URLs, use URLs from a prior tool's output (e.g., search results), not made-up URLs. Fabricated inputs produce "not found" errors that you'll dismiss as "expected" — which means you never actually tested the happy path.
- **A structured error is not a pass.** If the server returns `isError: false` but the result says "0/2 successful," the tool's HTTP layer worked but the test failed. Count first-call successes separately from retries.
- **Sequence tools with data dependencies.** If tool B needs output from tool A (e.g., `get-reddit-post` needs URLs from `search-reddit`), run A before B. Do not parallelize calls that have data dependencies just to save time — you'll end up with fabricated inputs or validation errors.

### Persistent session reuse (cross-conversation)

```bash
# In a new conversation — check if session from last time is still alive
mcpc @my-mcp ping
# If live → skip all setup, go directly to tool testing
# If crashed → reconnect (tokens still in Keychain, no login):
mcpc https://mcp.example.com connect @my-mcp
```

### Proxy for sandboxed testing

```bash
# Human authenticates, then exposes via proxy
mcpc https://mcp.example.com connect @relay --proxy 8080
# AI or untrusted client connects to proxy (no auth tokens exposed)
mcpc localhost:8080 connect @sandboxed
mcpc @sandboxed tools-list
```

### Interactive debugging shell

```bash
mcpc @session shell
# Type commands interactively: tools, tools-call, resources, help, exit
```

### Verbose transport debugging

```bash
# Enable debug logging for transport-level issues
mcpc <server> connect @debug --verbose
mcpc @debug tools-list --verbose
# Or set environment variable
MCPC_VERBOSE=1 mcpc @debug tools-list
```

## OAuth login deep dive

`mcpc login <server>` triggers a multi-stage OAuth 2.1 flow. When it works, it is seamless. When any stage fails, you need to know which stage broke and why.

### Full OAuth flow — what mcpc actually does

```
mcpc login https://mcp.example.com/mcp

 1. GET https://mcp.example.com/mcp/.well-known/oauth-protected-resource
    → Response includes: { "authorization_servers": ["https://mcp.example.com"] }
    → The authorization server MAY differ from the MCP server URL

 2. GET https://mcp.example.com/.well-known/oauth-authorization-server
    → Response includes: authorization_endpoint, token_endpoint, registration_endpoint, ...
    → FAILS HERE if registration_endpoint is missing (see F-03 below)

 3. POST registration_endpoint (Dynamic Client Registration — RFC 7591)
    → Sends: { "client_name": "mcpc", "redirect_uris": ["http://127.0.0.1:PORT/callback"], ... }
    → Receives: { "client_id": "...", "client_secret": "..." }

 4. Start local HTTP callback server
    → Scans ports 8000–8099, binds 127.0.0.1:PORT
    → Raw Node.js http.createServer() — NOT Hono, NOT Express
    → Only handles /callback path; everything else returns plain text "Not found"

 5. Open browser to authorization_endpoint
    → Includes: client_id, redirect_uri, code_challenge (PKCE S256), state, scope

 6. User authenticates in browser
    → Provider login (Google, GitHub, etc.), consent screen, MFA

 7. Browser redirects to http://127.0.0.1:PORT/callback?code=AUTH_CODE&state=STATE
    → mcpc validates state parameter
    → If this redirect never arrives, check port conflicts (see F-02 below)

 8. POST token_endpoint (code exchange)
    → Sends: grant_type=authorization_code, code, redirect_uri, code_verifier, client_id, client_secret
    → Receives: access_token, refresh_token, id_token, expires_at

 9. Store credentials
    → Tokens → OS keychain (auth-profile:HOST:PROFILE:tokens)
    → Client info → OS keychain (auth-profile:HOST:PROFILE:client)
    → Profile metadata → ~/.mcpc/profiles.json

10. Shutdown callback server
```

### Identifying which stage failed

| Symptom | Failed stage | Root cause |
|---|---|---|
| "Incompatible auth server: does not support dynamic client registration" | Stage 2-3 | `registration_endpoint` missing from OAuth metadata |
| Browser opens but callback never arrives | Stage 7 | Port conflict — another process intercepted the callback |
| `{"detail":"Not Found"}` in browser (JSON) | Stage 7 | OrbStack/Docker/other process on port 8000+ |
| `Not found` in browser (plain text) | Stage 7 | mcpc received request but on wrong path (not `/callback`) |
| "Token exchange failed" or 400 from token endpoint | Stage 8 | Token endpoint expects different body format (JSON vs form) or different parameter names |
| Browser redirects to wrong URL (not localhost) | Stage 6-7 | Redirect URL not whitelisted in OAuth provider dashboard |

### mcpc callback server internals

Understanding the callback server helps distinguish mcpc errors from port conflict errors:

- **Runtime:** Raw Node.js `http.createServer()` — not Hono, not Express, not Fastify
- **Bind address:** `127.0.0.1` (IPv4 only, not `0.0.0.0`, not `::1`)
- **Port scanning:** Tries 8000, then 8001, 8002, ... up to 8099
- **Port test:** Attempts `bind('127.0.0.1', port)` — if bind succeeds, mcpc considers the port free
- **Handled paths:** `/callback` only — returns HTML on success, error page on failure
- **404 format:** Plain text `Not found` (NOT JSON)
- **Lifetime:** Starts before browser opens, shuts down after receiving the callback code

**Key diagnostic:** If you see JSON in the browser's callback response (e.g., `{"detail":"Not Found"}`), the response is NOT from mcpc. Something else is listening on that port.

### Port conflict detection (CRITICAL)

mcpc's port availability check binds `127.0.0.1:PORT`. This check can pass even when another process binds `0.0.0.0:PORT` (wildcard), because the kernel treats these as non-conflicting for `bind()`. However, when the browser resolves `localhost`, the wildcard binding captures the connection first.

**Known conflicting software:**

| Software | Ports used | Bind address | Why it conflicts |
|---|---|---|---|
| OrbStack (Docker for macOS) | 8000, 8001 | `0.0.0.0` (`vcom-tunnel`) | Wildcard bind grabs localhost traffic |
| Docker Desktop | Varies | `0.0.0.0` (port-mapped containers) | Same wildcard bind issue |
| Python dev servers | 8000, 8080 | `0.0.0.0` (default) | Django/Flask defaults |
| PHP built-in server | 8000 | `0.0.0.0` or `localhost` | Common dev port |

**Always check ports before `mcpc login`:**

```bash
# Check for anything listening on mcpc's port range
lsof -i :8000-8010 | grep LISTEN

# If OrbStack is running, expect output like:
# com.docke  PID user  IPv4 ... TCP *:8000 (LISTEN)
# com.docke  PID user  IPv4 ... TCP *:8001 (LISTEN)

# Fix: stop OrbStack, or stop its vcom-tunnel, or kill the conflicting processes
# Then retry mcpc login
```

If you cannot stop the conflicting process, mcpc will scan upward from 8000. Ensure at least one port in 8000-8099 is truly free (no wildcard listeners).

### Supabase-specific OAuth traps

When the MCP server uses mcp-use with Supabase as the OAuth provider, the following incompatibilities arise between standard OAuth 2.1 (which mcpc implements) and Supabase's auth API:

**Trap 1: Missing `registration_endpoint`**
Supabase does not implement Dynamic Client Registration (RFC 7591). If your MCP server's `oauth-protected-resource` metadata points to Supabase directly as the authorization server, mcpc will fail with "does not support dynamic client registration." The fix is server-side: the MCP server must host its own DCR endpoint and include it in its `/.well-known/oauth-authorization-server` metadata.

**Trap 2: `provider` parameter required**
Supabase's `/auth/v1/authorize` requires a `provider=google` (or other social provider) query parameter. Standard OAuth clients do not send this. The MCP server's authorize proxy must inject this parameter.

**Trap 3: `redirect_uri` vs `redirect_to`**
Supabase uses `redirect_to` instead of the standard `redirect_uri` parameter. Without mapping, Supabase ignores the redirect and falls back to the Dashboard's configured "Site URL." The MCP server's authorize proxy must rename this parameter.

**Trap 4: Don't forward `client_id` to Supabase**
If the MCP server's DCR-generated `client_id` is forwarded to Supabase's authorize endpoint, Supabase passes it through to Google, which rejects it as an unknown client. The MCP server should strip `client_id` before proxying to Supabase.

**Trap 5: Token exchange needs JSON body + `apikey` header**
Supabase's `/auth/v1/token?grant_type=pkce` expects:
- Body: JSON (`{"auth_code": "...", "code_verifier": "..."}`) — NOT `application/x-www-form-urlencoded`
- Header: `apikey: <supabase-anon-key>` — required on every Supabase API call
- Parameter name: `auth_code` (not `code`)
The MCP server's token endpoint proxy must handle all three transformations.

**Trap 6: Redirect URL must be whitelisted**
In Supabase Dashboard > Authentication > URL Configuration > Redirect URLs, add: `http://localhost:*/**`
Without this, Supabase silently redirects to the Site URL instead of the mcpc callback.

### mcp-use deploy trap

`mcp-use deploy` clones the repository from GitHub — it does NOT upload local files. If you fix an OAuth endpoint in your MCP server code, you must `git commit && git push` before deploying. Uncommitted changes will not be deployed. This wastes deploy cycles when iterating on OAuth fixes.

## OAuth debugging checklist

Run through this checklist sequentially when `mcpc login` fails. Each step depends on the previous one succeeding.

**Pre-flight:**

- [ ] `mcpc --version` shows 0.1.10+ (OAuth support)
- [ ] `lsof -i :8000-8010 | grep LISTEN` shows no conflicting listeners (especially OrbStack `vcom-tunnel`)
- [ ] If OrbStack is running: stop it or free ports 8000-8001

**Stage 1 — Metadata discovery:**

- [ ] `curl -s https://YOUR-SERVER/.well-known/oauth-protected-resource | jq .` returns valid JSON with `authorization_servers` array
- [ ] The authorization server URL in that response is correct (may be the same server or a different one)
- [ ] `curl -s https://AUTH-SERVER/.well-known/oauth-authorization-server | jq .` returns valid JSON
- [ ] Response includes `registration_endpoint` (required for mcpc's DCR)
- [ ] Response includes `authorization_endpoint` and `token_endpoint`

**Stage 2 — Dynamic Client Registration:**

- [ ] `curl -s -X POST https://AUTH-SERVER/register -H 'Content-Type: application/json' -d '{"client_name":"test","redirect_uris":["http://127.0.0.1:8000/callback"]}' | jq .` returns `client_id`
- [ ] If 404 or error: the server does not implement DCR — fix server-side

**Stage 3 — Callback server:**

- [ ] After running `mcpc login`, verify mcpc prints "Open browser" prompt (callback server is ready)
- [ ] `lsof -i :8000-8010 | grep node` shows mcpc's Node process listening (not OrbStack or Docker)
- [ ] `curl -s http://127.0.0.1:8000/test` returns plain text `Not found` (confirms mcpc is on that port, not another process)

**Stage 4 — Browser authorization:**

- [ ] Browser opens to the correct authorization URL
- [ ] If using Supabase: URL includes `provider=google` (or appropriate provider)
- [ ] After authentication, browser redirects to `http://127.0.0.1:PORT/callback?code=...`
- [ ] If browser redirects to production URL instead of localhost: add `http://localhost:*/**` to Supabase Redirect URLs

**Stage 5 — Token exchange:**

- [ ] mcpc reports "Login successful" in terminal
- [ ] If token exchange fails: check server logs for the token endpoint — common issues are JSON vs form-urlencoded body, missing `apikey` header (Supabase), wrong parameter names (`auth_code` vs `code`)
- [ ] `mcpc --json | jq '.profiles'` shows the new profile

**Stage 6 — Connection test:**

- [ ] `mcpc https://YOUR-SERVER connect @test` succeeds
- [ ] `mcpc @test tools-list` returns tools
- [ ] `mcpc @test close`

**If deploying server fixes during debugging:**

- [ ] Changes are committed: `git status` shows clean working tree
- [ ] Changes are pushed: `git push` succeeds
- [ ] Deploy uses pushed code: `mcp-use deploy` (or equivalent) runs after push
- [ ] Health check passes: `curl https://YOUR-SERVER/health/live`

## Common pitfalls

| Pitfall | Fix |
|---|---|
| `mcpc: command not found` | `npm install -g @apify/mcpc` |
| Session name collision | Use unique names: `@test-$(date +%s)` |
| Stdio server not starting | Run command manually first, check stderr |
| HTTP 401/403 on connect | `mcpc login <server>` or use `--header "Authorization: Bearer $TOKEN"` |
| Timeout on tool call | Increase with `--timeout 600` (default: 300s) |
| Private CA or self-signed cert rejected | Install the CA locally or set `NODE_EXTRA_CA_CERTS=/path/to/ca.pem` before connecting |
| Stale sessions after crash | `mcpc --clean=sessions` |
| Can't tell if stateful or stateless | Check `mcpc --json @session \| jq .protocolVersion` — 2025-11-25+ is streamable |
| Tool args parsed wrong type | Force string with `id:='"123"'` (single-quote wrapped JSON string) |
| `key:=value` fails for array params | Use inline JSON: `'{"items":["a","b"]}'` or `items:='["a","b"]'` |
| Server error but exit code is 0 | Normal — check `jq '.isError'` in JSON, not exit code |
| "unknown command: completions" | mcpc doesn't support completions/sampling/roots capabilities |
| Bridge process orphaned | `mcpc --clean=sessions` clears PIDs and sockets |
| `grep -oP` fails on macOS | macOS ships BSD grep which lacks `-P` (Perl regex). Use `grep -oE` (extended regex) instead, which works on both GNU and BSD grep |
| OrbStack/Docker grabbing callback port | `lsof -i :8000-8010 \| grep LISTEN` before `mcpc login` — stop conflicting listeners |
| `{"detail":"Not Found"}` JSON in browser callback | NOT mcpc — another process on the port (OrbStack, Docker, dev server). mcpc's 404 is plain text |
| "Incompatible auth server: does not support dynamic client registration" | Server's OAuth metadata missing `registration_endpoint`. Fix server-side: implement a DCR endpoint |
| OAuth callback redirects to production URL, not localhost | Add `http://localhost:*/**` to OAuth provider's redirect URL allowlist (Supabase Dashboard > Auth > URL Config) |
| Supabase token exchange returns 400 | Server must proxy token endpoint: send JSON body (not form-urlencoded), include `apikey` header, map `code` to `auth_code` |
| Supabase authorize returns "invalid client_id" | Server's authorize proxy must strip the DCR-generated `client_id` before forwarding to Supabase |
| `mcp-use deploy` doesn't pick up local code changes | `mcp-use deploy` clones from git — commit and push first |
| OAuth login succeeds but `mcpc connect` gets 401 | Token may have expired during debugging. Re-run `mcpc login` then `mcpc connect` |
| "I have to login every time" | You don't — check Step 0 above. Run `mcpc` to see existing sessions, `mcpc --json \| jq '.profiles'` to see saved OAuth profiles. Tokens auto-refresh via Keychain. Save `@session` name to CLAUDE.md for cross-conversation reuse |

## Reference routing

### Core guides

| File | Read when |
|---|---|
| `references/guides/installation.md` | Installing mcpc globally, locally, or with Bun; verifying installation |
| `references/guides/stdio-testing.md` | Testing local stdio servers, config file format, env var substitution, process debugging |
| `references/guides/http-testing.md` | Testing HTTP servers (stateless SSE vs stateful streamable), auth (bearer, OAuth), proxy, TLS |
| `references/guides/tool-resource-testing.md` | Tool calling patterns, argument syntax, schema validation, resource reading, prompt testing |
| `references/guides/scripting-automation.md` | JSON mode, automated test scripts, exit codes, piped input |

### Deep-dive guides

| File | Read when |
|---|---|
| `references/guides/session-management.md` | Session lifecycle, bridge architecture, IPC protocol, multi-session, auto-recovery, session states |
| `references/guides/authentication.md` | OAuth 2.1 flow internals, profiles, keychain, token refresh, bearer tokens, CI headless auth |
| `references/guides/architecture.md` | mcpc internals, transport layer, config system, error hierarchy, data directory layout |
| `references/guides/bridge-internals.md` | Bridge spawn sequence, BridgeClient IPC, SessionClient retry, health checks, crash recovery |
| `references/guides/proxy-testing.md` | Proxy mode for AI sandboxes, bearer auth, health endpoint, Docker integration |
| `references/guides/cleanup-maintenance.md` | Clean command categories, session consolidation, storage management, recovery |
| `references/guides/ci-cd-integration.md` | GitHub Actions workflows, Docker testing, MCPC_HOME_DIR isolation, headless auth |
| `references/guides/x402-payments.md` | x402 agentic payment testing, wallet setup, USDC on Base, proactive/reactive signing |
| `references/guides/async-tasks.md` | Current CLI boundary for async/task-style work; what `mcpc 0.1.11` does and does not expose |

### Patterns and internals

| File | Read when |
|---|---|
| `references/patterns/jq-patterns.md` | 25+ jq patterns for filtering tools, extracting results, session management, data transformation |
| `references/patterns/python-integration.md` | Python wrapper class, async patterns, FastAPI gateway, type-safe dataclasses, batch processing |
| `references/patterns/output-formatting.md` | How formatOutput() routes human vs JSON, exact JSON shapes, TTY detection, color stripping |
| `references/patterns/argument-parsing.md` | key:=value auto-parsing, inline JSON, stdin, type coercion table, shell quoting rules |
| `references/patterns/schema-validation.md` | Schema validation modes (strict/compatible/ignore), saving schemas, regression testing |
| `references/patterns/config-resolution.md` | Config file format, env var substitution, config entry syntax, ServerConfig validation |
| `references/patterns/shell-advanced.md` | Interactive shell internals, readline, notifications, history, shell-only features |
| `references/patterns/logging-debugging.md` | Verbose mode, bridge logs, log rotation, debugging workflows, diagnostic scripts |
| `references/patterns/notification-handling.md` | Server push notifications, types, color coding, subscription, testing notification support |
| `references/patterns/data-model.md` | Complete type definitions: SessionData, ServerConfig, AuthProfile, IpcMessage, constants |
| `references/patterns/tool-filtering.md` | Filtering/searching tools by name, description, or schema using `tools-list --json` with jq |
| `references/patterns/pagination-caching.md` | Auto-pagination with `nextCursor`, tool cache lifetime, cache invalidation via notifications |
| `references/patterns/auth-precedence.md` | Auth method priority order, conflict rules, security properties, CI auth selection matrix |

### Commands and examples

| File | Read when |
|---|---|
| `references/commands/quick-reference.md` | All mcpc commands, flags, options, and environment variables at a glance |
| `references/examples/real-world-workflows.md` | 10 complete runnable workflow scripts: smoke test, comparison, monitoring, regression, proxy, OAuth |
| `references/examples/testing-recipes.md` | 15 copy-paste assertion recipes: tool exists, schema check, exit codes, latency, cleanup verification |
| `references/troubleshooting/common-errors.md` | Error codes (0-4), session states, transport debugging, auth failures, recovery |

## What mcpc does NOT support

mcpc does not expose CLI commands for every MCP capability. If the server advertises these, you cannot test them via mcpc:

- **`completion/complete`** — argument auto-completion hints (no `completions` command exists)
- **`sampling`** — server-initiated LLM sampling requests
- **`roots`** — client root directory declarations

Do not invent commands for these — they will fail with "unknown command" (exit code 1). Check `mcpc @session help` for the actual available commands.

## Guardrails

- Always verify mcpc is installed before running commands
- Use `--json` when scripting — never parse human-readable colored output
- Use unique session names for parallel testing — collisions cause errors
- Close sessions after testing — orphaned bridges consume resources
- Do not assume a TLS-bypass flag exists in `mcpc 0.1.11` — use valid certificates or `NODE_EXTRA_CA_CERTS`
- Never hardcode tokens in scripts — use environment variables (`$MCP_TOKEN`)
- Test stdio server commands manually before connecting via mcpc
- **Exit codes reflect CLI errors only, NOT MCP server errors.** Exit codes: 0=success or server-side error, 1=bad CLI args, 3=network, 4=auth. Server-side tool errors (validation failures, tool-not-found) return exit code 0 with `isError: true` in JSON. **Always check `isError` in JSON output for server errors — do not rely on exit codes alone.**
- Before calling any tool, check its schema (`tools-get <name> --json | jq '.inputSchema'`) — if params are arrays, use inline JSON, not `key:=value`
- Do not run `mcpc --clean=all` without confirming — it deletes saved OAuth profiles
- Before running `mcpc login`, always check `lsof -i :8000-8010 | grep LISTEN` for port conflicts — OrbStack, Docker, and dev servers silently intercept OAuth callbacks
