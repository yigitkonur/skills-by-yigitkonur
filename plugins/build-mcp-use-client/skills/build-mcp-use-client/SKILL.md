---
name: build-mcp-use-client
description: "Use if writing TypeScript mcp-use MCP client code — MCPClient, MCPSession, useMcp, mcp-use/react."
---

# Build mcp-use Client

Build or audit deterministic TypeScript MCP **client** code using the `mcp-use` SDK: `MCPClient`, `MCPSession`, `mcp-use/browser`, `mcp-use/react` (`useMcp`, `McpClientProvider`, `useMcpClient`, `useMcpServer`), code mode, and the `npx mcp-use client` CLI.

The client is the half that **connects to** an MCP server, lists/calls tools, reads resources, manages sessions, and handles auth — without an LLM choosing what to call.

## When to use this skill

Use this skill when *any* of these are true:

- *the user imports from `"mcp-use"`, `"mcp-use/browser"`, or `"mcp-use/react"`*
- *the code constructs `new MCPClient(...)`, calls `createSession()`/`createAllSessions()`, or uses `client.close()`/`closeAllSessions()`*
- *a React app uses `useMcp`, `McpClientProvider`, `useMcpClient`, or `useMcpServer`* (note: `state` not `status`; `storageProvider` not `persistenceProvider`)
- *the project runs `npx mcp-use client` or has `mcp.json`, `mcp.config.json`, or `.vscode/mcp.json` config files*
- *the work is connecting to existing MCP servers, listing tools/resources/prompts, calling them deterministically, or wiring up auth/sampling/elicitation callbacks on the client side*
- *the request involves code mode via `executeCode()`/`search_tools()` from a client*
- *the task is fixing client-side issues: 404 session recovery, idle proxy timeouts, dropped reconnects, OAuth re-auth loops, or React StrictMode duplicate sessions*

Do **NOT** use this skill if:

- *an LLM picks and orchestrates tools via `MCPAgent`* — route to `build-mcp-use-agent`
- *the work imports from `"mcp-use/server"`, defines `server.tool`/`server.resource`/`server.prompt`, or builds widgets/transports/server auth* — route to `build-mcp-use-server`
- *the code imports directly from `@modelcontextprotocol/sdk` without the `mcp-use` wrapper* — route to `build-mcp-server-sdk-v1` or `build-mcp-server-sdk-v2`
- *the only goal is headless CLI verification of an already-running MCP server with `mcpc`* — route to `test-by-mcpc-cli`

Inspect the path the user named directly. Do not start with a repo-wide scan when a subdirectory is given.

## Non-Negotiable Rules

These rules are load-bearing — violating them is the most common source of client bugs.

| # | Rule | Why |
|---|---|---|
| 1 | Import from `mcp-use`, `mcp-use/browser`, or `mcp-use/react` only | Hand-rolling raw `@modelcontextprotocol/sdk` calls inside a wrapper-library project re-implements features and breaks reconnection/auth integration |
| 2 | `await` `createSession()` / `createAllSessions()` before use | Sessions are async; using an unresolved promise yields runtime errors that look like config bugs |
| 3 | Always cleanup: `closeAllSessions()` for normal clients; `client.close()` for code mode | Code mode allocates external executors (VM/E2B) that leak without `close()` |
| 4 | Discover before hardcoding: list tools/resources/prompts before assuming names | Server schemas drift; hardcoded names break silently when the server adds optional args |
| 5 | Handle `CallToolResult.isError`, `content`, `structuredContent`, and `_meta` deliberately | The shape is union-like; assuming `content[0].text` exists masks real tool errors |
| 6 | Set `timeout`, `maxTotalTimeout`, and `AbortSignal` for long-running tools | Defaults will hang on slow tools; production work needs explicit cancellation |
| 7 | Tokens belong server-side or in OAuth flows; browser headers carry only public values | `mcp-use/browser` headers are visible to anyone who opens devtools |
| 8 | Use `mcp.state` (not `status`) and `storageProvider` (not `persistenceProvider`) | These names changed; older docs and AI-generated code still ship the old ones |
| 9 | Check optional capabilities (e.g. completion) before calling them | Servers advertise capabilities — calling unsupported ones throws confusing errors |
| 10 | Report what validation actually ran; do not imply runtime coverage from `tsc` alone | Type checks are necessary but not sufficient for client behavior verification |

## Workflow

### 1. Detect what exists

Inspect the target path and look for client-side signals:

```bash
tree -L 3 2>/dev/null || find . -maxdepth 3 -type f | sort
```

Confirm:

- `package.json` has `"mcp-use"` as a dependency
- imports from `"mcp-use"`, `"mcp-use/browser"`, or `"mcp-use/react"`
- presence of `MCPClient`, `MCPSession`, `useMcp`, `McpClientProvider`, `useMcpClient`, `useMcpServer`
- `npx mcp-use client` scripts, `mcp.json`, `mcp.config.*`, `.vscode/mcp.json`
- direct imports from `@modelcontextprotocol/sdk` — these route to raw SDK skills, not here
- imports from `"mcp-use/server"` — these route to `build-mcp-use-server`
- `MCPAgent` usage — that routes to `build-mcp-use-agent`

Run the version preflight when Node/npm are available:

```bash
bash skills/build-mcp-use-client/skills/build-mcp-use-client/scripts/check-mcp-use-version.sh <target-path>
```

Read `scripts/check-mcp-use-version.sh.md` before changing the script or interpreting non-obvious output.

### 2A. Existing client found — audit then fix

Run the diagnostic script first:

```bash
bash skills/build-mcp-use-client/skills/build-mcp-use-client/scripts/diagnose-client.sh <target-path>
```

Read `scripts/diagnose-client.sh.md` for the diagnostic categories and exit-code contract.

Audit the implementation against the surface map below before editing. Apply focused fixes — do not rebuild a working client from scratch.

| Audit surface | Read | Check for |
|---|---|---|
| constructor, config files, sessions, imports | `references/guides/client-configuration.md`, `references/guides/environments.md` | correct entry point, current Node/package baseline, awaited session creation, cleanup |
| tools, resources, prompts, completion | `references/guides/tools.md`, `references/guides/resources.md`, `references/guides/prompts.md`, `references/guides/completion.md` | discovery before calls, `isError` handling, `structuredContent`, pagination, capability checks, timeouts/abort |
| callbacks, auth, notifications | `references/guides/sampling.md`, `references/guides/elicitation.md`, `references/guides/authentication.md`, `references/guides/notifications-and-logging.md` | callback names, browser secret boundary, token expiry/re-auth, list-changed handlers |
| React | `references/guides/usemcp-and-react.md` | `state` not `status`, one provider for multi-server apps, StrictMode-safe `addServer`, cleanup, all states handled |
| code mode | `references/guides/code-mode.md` | executor isolation, `executeCode()`, `search_tools()`, `client.close()` |
| production hardening | `references/patterns/production-patterns.md`, `references/patterns/anti-patterns.md`, `references/troubleshooting/common-errors.md` | reconnection, 404 recovery, idle proxy timeout, process shutdown, dropped connections |

### 2B. No client found — build the smallest working integration

If repo context already gives the environment, server target, and auth shape, skip the questionnaire and build directly.

Pick the server target before coding:

- Existing MCP server in the repo: connect to it and discover real capabilities.
- Client mechanics only, no domain server: use `@modelcontextprotocol/server-everything` for a smoke test.
- Domain-specific tool required but no server exists: route to `build-mcp-use-server` first.

If context is missing, ask only the questions you cannot answer:

1. Environment — Node CLI, Node service, browser app, React app, or `npx mcp-use client`.
2. Server count — one server or multiple.
3. Transport — stdio, Streamable HTTP, or mixed.
4. Auth — none, bearer token, OAuth, or custom public headers.
5. React shape — standalone `useMcp` or provider-based multi-server app.
6. Callbacks — sampling, elicitation, notifications/logging, or none.
7. Code mode — no, trusted-local VM, E2B, or custom isolation.
8. Production hardening — basic cleanup, reconnect/health checks, or full setup.

### 3. Build or fix in this order

1. Align prerequisites against current `npm view mcp-use` metadata; do not keep old Node 18 guidance for current releases.
2. Use the right import path: `mcp-use` for Node, `mcp-use/browser` for browser, `mcp-use/react` for React.
3. Configure real server IDs and discover capabilities before hardcoding tool/resource/prompt names.
4. Add auth without printing or committing secrets.
5. Add timeouts, abort handling, cleanup, and reconnection before calling the work production-ready.
6. Validate with type/lint/tests and, when possible, a real connect/list/call/read smoke test.

## Core Surface Map

Route to the reference file matching the user's intent. Do not load files speculatively.

| Trigger | File | Why |
|---|---|---|
| install, first Node/browser/React/CLI client | `references/guides/quick-start.md` | minimal runnable paths and first calls |
| choose Node/browser/React/CLI entry point | `references/guides/environments.md` | environment matrix, imports, limits |
| configure `MCPClient`, config files, sessions | `references/guides/client-configuration.md` | constructor shape, callbacks, 404 recovery |
| manage multiple servers dynamically | `references/guides/server-manager.md` | server manager and dynamic config patterns |
| list/call tools, set timeouts, abort | `references/guides/tools.md` | result handling, progress, cancellation |
| read resources, templates, subscriptions | `references/guides/resources.md` | pagination, content shapes, notifications |
| list/get prompts | `references/guides/prompts.md` | prompt arguments and prompt updates |
| implement argument/resource completion | `references/guides/completion.md` | capability checks and debounce guidance |
| handle sampling requests | `references/guides/sampling.md` | `onSampling`, model preferences, React callbacks |
| handle elicitation requests | `references/guides/elicitation.md` | `onElicitation`, helpers, form and URL modes |
| handle auth, re-auth, browser secrets | `references/guides/authentication.md` | OAuth, bearer tokens, headers, CLI auth, DCR/manual registration |
| receive list-changed events, roots, logs | `references/guides/notifications-and-logging.md` | notification listeners and logging callbacks |
| build React clients | `references/guides/usemcp-and-react.md` | hook/provider props, lifecycle, states, reconnection |
| use code mode | `references/guides/code-mode.md` | executors, imports, safety, browser/React limits |
| use `npx mcp-use client` | `references/guides/cli-reference.md` | CLI commands, sessions, JSON scripting |
| copy complete examples | `references/examples/client-recipes.md` | Node, browser, React, code mode recipes |
| scaffold project layouts | `references/examples/project-templates.md` | package structures and starter files |
| harden production behavior | `references/patterns/production-patterns.md` | shutdown, retries, reconnect, observability |
| review mistakes before finalizing | `references/patterns/anti-patterns.md` | known bad patterns and fixes |
| diagnose specific errors | `references/troubleshooting/common-errors.md` | connection, auth, React, code mode, import failures |
| verify package baseline | `scripts/check-mcp-use-version.sh` | Node/package/npm drift diagnostics |
| diagnose a stuck client | `scripts/diagnose-client.sh` | config/import/auth/lifecycle scan |

## Decision Rules

### Runtime and version

- Treat `npm view mcp-use version engines peerDependencies --json` as the source of truth for current install guidance.
- Run `scripts/check-mcp-use-version.sh` before copying examples into a project.
- Prefer examples that use the major/minor line npm metadata confirms. Avoid stale `^1.21.0` style pins.

### React

- Use one `McpClientProvider` for multi-server apps.
- Make dynamic `addServer()` calls inside `useEffect` idempotent under StrictMode; clean up temporary servers with `removeServer()` when appropriate.
- Gate UI and effects on every state: `discovering`, `authenticating`, `pending_auth`, `ready`, `failed`.
- Resource-reading effects must avoid setting state after unmount or after a newer request supersedes the old one.

### Code mode

- VM executor for trusted local code only.
- E2B or custom isolation for untrusted or multi-tenant code.
- Always call `client.close()` because code mode may allocate external resources.

### Streaming and reconnection

- Prefer Streamable HTTP for new HTTP clients; legacy SSE only for compatibility.
- Do not build WebSocket clients for MCP — `mcp-use` does not target WebSocket transport.
- Route long-running tools through timeout/progress/abort guidance in `references/guides/tools.md` and reconnection guidance in `references/patterns/production-patterns.md`.

## Validation

Use the smallest honest set:

```bash
npm run typecheck
npm run lint
npm test
npx tsx src/client.ts
npx mcp-use client connect --stdio "npx -y @modelcontextprotocol/server-everything" --name smoke
```

For React, exercise every rendered state: `discovering`, `authenticating`, `pending_auth`, `ready`, `failed`. For auth issues, test 401/403, expired refresh token, popup blocked, redirect callback failure, and `pending_auth` loops against `references/guides/authentication.md` plus `references/troubleshooting/common-errors.md`.

## Output Contract

When finishing a client task, report:

1. Target path and environment: Node, browser, React, or CLI.
2. Servers discovered or configured.
3. Key APIs used: `MCPClient`, `MCPSession`, `useMcp`, provider hooks, code mode, CLI.
4. Validation commands actually run.
5. Whether runtime behavior was exercised or only type/lint passed.
6. References consulted.
7. Auth/secrets caveat — without printing the secret values.
