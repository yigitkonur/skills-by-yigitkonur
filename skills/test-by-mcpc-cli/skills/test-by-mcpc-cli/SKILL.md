---
name: test-by-mcpc-cli
description: Use skill if you are testing or debugging MCP servers with mcpc CLI across stdio, HTTP stateless, and HTTP stateful transports — tool calling, schema validation, and automated test scripts.
---

# Test MCP Server with mcpc

Use `mcpc` as the default CLI contract test harness for MCP servers across stdio, HTTP stateless (SSE), and HTTP stateful (streamable) transports.

## Trigger boundary

Use this skill when you need to:

- Verify MCP server connectivity and capabilities
- Validate tool schemas and tool-call behavior
- Debug transport/session/auth failures
- Script regression checks in CI
- Compare stateless vs stateful server behavior

Do not use this skill when building server/client code from scratch:

- `build-mcp-use-server` for server implementation
- `build-mcp-use-client` for client implementation

## Prerequisites

```bash
mcpc --version
```

If missing, install via `references/guides/installation.md`.
This skill targets **mcpc 0.1.11** behavior.

## Core decision tree

```
What are you testing?
├── Local process server
│   └─► stdio workflow (references/guides/stdio-testing.md)
├── Remote HTTP server
│   ├── Sessionless behavior expected
│   │   └─► HTTP stateless workflow (references/guides/http-testing.md)
│   └── Session continuity expected
│       └─► HTTP stateful workflow (references/guides/http-testing.md)
├── OAuth login or token reuse issues
│   └─► references/guides/authentication.md + references/troubleshooting/common-errors.md
└── Need command syntax quickly
    └─► references/commands/quick-reference.md
```

## Session-first rule (OAuth and long-running tests)

Before any new `connect`, check existing state:

```bash
mcpc
mcpc --json | jq '.profiles'
```

- If active session exists: reuse it.
- If session crashed but profile exists: reconnect (no re-login).
- Only run `mcpc login <server>` when no reusable profile exists.

Details: `references/guides/session-management.md`, `references/guides/authentication.md`.

## Transport workflow

### 1) Connect

Examples:

```bash
# stdio
mcpc --config /path/to/mcp.json my-server connect @test

# http
mcpc https://mcp.example.com connect @test

# http + bearer token
mcpc https://mcp.example.com connect @test --header "Authorization: Bearer $MCP_TOKEN"
```

### 2) Verify handshake/session

```bash
mcpc @test ping
mcpc --json @test | jq '{protocolVersion, _mcpc, serverInfo}'
```

If stateful behavior matters, explicitly test that state survives within the same session.

### 3) Discover capabilities

```bash
mcpc @test tools
mcpc @test tools --full
mcpc @test resources
mcpc @test prompts
```

### 4) Validate tool schemas before calling

```bash
mcpc @test tools-get my-tool --json | jq '.inputSchema'
```

Rule: if args include arrays/objects, use JSON input; do not rely on scalar-only `key:=value`.

### 5) Execute tool/resource/prompt checks

```bash
mcpc @test tools-call my-tool '{"arg":"value"}' --json
mcpc @test resources-read "file:///path/to/resource"
mcpc @test prompts-get my-prompt arg:=value
```

### 6) Script regression in JSON mode

```bash
RESULT=$(mcpc @test tools-call my-tool '{"arg":"value"}' --json)
echo "$RESULT" | jq '.isError // false'
```

Important: CLI exit code does not reliably signal server-side tool failures; inspect `isError`.

### 7) Cleanup

```bash
mcpc @test close
mcpc --clean=sessions
```

## High-signal debugging rules

1. **Always verify schema before first tool call.**
2. **Use real dependency data across chained tools** (no fabricated placeholders).
3. **Treat structured error payloads as failures**, even when command exits 0.
4. **Check port conflicts before OAuth login** (`lsof -i :8000-8010 | grep LISTEN`).
5. **Prefer full JSON output in exploratory runs**; only truncate in CI summaries.

## Common pitfalls

| Pitfall | Fix |
|---|---|
| `mcpc: command not found` | Install using `references/guides/installation.md` |
| Re-authenticating every run | Reuse existing profile/session via `mcpc` and `mcpc --json | jq '.profiles'` |
| Wrong arg types on tool call | Inspect schema first, then send JSON for arrays/objects |
| Assuming non-zero exit code for MCP server errors | Check `isError` field in JSON output |
| OAuth callback failures | Check local port conflicts and OAuth metadata first |
| Ambiguous transport failures | Use `--verbose` and inspect bridge/session diagnostics |

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

- Always verify `mcpc --version` before testing.
- Use `--json` for scripted checks.
- Close or clean sessions when finishing a run.
- Never hardcode secrets; use env vars.
- Check tool schema before first call.
- Validate server-side errors via JSON payload, not shell exit code alone.
- Confirm before `mcpc --clean=all` (destructive to profiles/log state).
