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
- Validating MCP server behavior before deployment
- Inspecting what an MCP server exposes (capabilities, schemas)
- Writing automated test scripts for MCP servers
- Setting up mcpc for the first time

**Do NOT use this skill when:**

- Building an MCP server from scratch (use `build-mcp-use-server`)
- Building an MCP client application (use `build-mcp-use-client`)
- Auditing MCP server code quality (use `optimize-mcp-server`)
- Testing Claude skills (use `test-skill-quality`)

## Prerequisites

```bash
mcpc --version
# Expected: mcpc X.Y.Z (0.1.10+)
# If not found, read references/guides/installation.md
```

Node.js 20+ required. Install mcpc: `npm install -g @apify/mcpc`.

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
      "args": ["@modelcontextprotocol/server-filesystem", "/tmp/test-dir"],
      "env": { "DEBUG": "true" }
    }
  }
}
```

**Connect:**

```bash
# Connect using config file entry
mcpc /path/to/config.json:my-server connect @test-stdio

# Or reference VS Code config
mcpc ~/.vscode/mcp.json:filesystem connect @test-stdio
```

**Verify the server started:**

```bash
mcpc @test-stdio ping
mcpc @test-stdio help
```

If the server fails to start, run the command manually first to check for errors:

```bash
npx @modelcontextprotocol/server-filesystem /tmp/test-dir
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

### Step 3: Test tool calls

```bash
# Call with key:=value arguments (auto-typed)
mcpc @session tools-call my-tool count:=10 enabled:=true name:=hello

# Call with inline JSON
mcpc @session tools-call my-tool '{"count": 10, "enabled": true}'

# Call with piped JSON input
echo '{"count": 10}' | mcpc @session tools-call my-tool

# Validate response against schema
mcpc @session tools-call my-tool arg:=value --schema expected.json

# Strict schema validation (fails on extra fields)
mcpc @session tools-call my-tool arg:=value --schema expected.json --schema-mode strict
```

**Argument auto-parsing rules:**

| Input | Parsed as | Type |
|---|---|---|
| `count:=10` | `10` | number |
| `enabled:=true` | `true` | boolean |
| `name:=hello` | `"hello"` | string |
| `id:='"123"'` | `"123"` | string (forced) |

Read `references/guides/tool-resource-testing.md` for advanced patterns.

### Step 4: Test resources and prompts

```bash
# Read a resource
mcpc @session resources-read "file:///path/to/resource"

# Save resource to file
mcpc @session resources-read "https://example.com/data" -o output.json

# Subscribe to resource updates (stays open)
mcpc @session resources-subscribe "file:///watched-path"

# Get a prompt with arguments
mcpc @session prompts-get my-prompt arg1:=value1 arg2:=value2
```

### Step 5: Use JSON mode for scripted tests

```bash
# All commands support --json for machine-readable output
mcpc @session tools-list --json | jq '.[].name'
mcpc @session tools-call my-tool arg:=val --json | jq '.content'
mcpc @session resources-list --json | jq '.[].uri'

# Check tool count
mcpc @session tools-list --json | jq 'length'

# Extract specific tool schema
mcpc @session tools-get my-tool --json | jq '.inputSchema'
```

Read `references/guides/scripting-automation.md` for full test scripts and CI integration.

### Step 6: Cleanup

```bash
mcpc @session close           # Close one session
mcpc                         # List active sessions
mcpc clean sessions          # Clean all sessions
mcpc clean all               # Clean sessions + profiles + logs
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

## Common pitfalls

| Pitfall | Fix |
|---|---|
| `mcpc: command not found` | `npm install -g @apify/mcpc` |
| Session name collision | Use unique names: `@test-$(date +%s)` |
| Stdio server not starting | Run command manually first, check stderr |
| HTTP 401/403 on connect | `mcpc login <server>` or use `--header "Authorization: Bearer $TOKEN"` |
| Timeout on tool call | Increase with `--timeout 600` (default: 300s) |
| Self-signed cert rejected | Use `--insecure` (dev only, never production) |
| Stale sessions after crash | `mcpc clean sessions` |
| Can't tell if stateful or stateless | Check `mcpc --json @session \| jq .protocolVersion` — 2025-11-25+ is streamable |
| Tool args parsed wrong type | Force string with `id:='"123"'` (single-quote wrapped JSON string) |
| Bridge process orphaned | `mcpc clean sessions` clears PIDs and sockets |

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
| `references/guides/async-tasks.md` | Async tool execution: `--task`, `--detach`, polling, cancel, crash recovery, task lifecycle |

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

## Guardrails

- Always verify mcpc is installed before running commands
- Use `--json` when scripting — never parse human-readable colored output
- Use unique session names for parallel testing — collisions cause errors
- Close sessions after testing — orphaned bridges consume resources
- Never use `--insecure` in production — only for local dev with self-signed certs
- Never hardcode tokens in scripts — use environment variables (`$MCP_TOKEN`)
- Test stdio server commands manually before connecting via mcpc
- Check exit codes in scripts: 0=success, 1=client error, 2=server error, 3=network, 4=auth
- Do not run `mcpc clean all` without confirming — it deletes saved OAuth profiles
