---
name: build-mcp-use-client
description: Use skill if you are building or auditing MCP client apps with mcp-use TypeScript, including MCPClient, sessions, React hooks, code mode, auth, CLI.
---

# Build MCP Use Client

Build or audit TypeScript MCP client applications with `mcp-use`: `MCPClient`, `MCPSession`, `mcp-use/browser`, `mcp-use/react`, code mode, authentication, and `npx mcp-use client`.

Run from the concrete package, fixture, or app path the user wants changed. If the user named a subdirectory, inspect that path directly instead of starting with a repo-wide scan.

## When To Use This Skill Vs Neighbors

| Use case | Route |
|---|---|
| Implementing or auditing `mcp-use` TypeScript client code with `MCPClient`, `MCPSession`, `mcp-use/browser`, `mcp-use/react`, or `npx mcp-use client` | Stay in this skill |
| `MCPAgent`, LLM orchestration, streaming agents, structured output, LangChain integration | `build-mcp-use-agent` |
| `mcp-use/server`, tools/resources/prompts, transports, OAuth server, MCP Apps widgets | `build-mcp-use-server` |
| Raw Model Context Protocol SDK implementation, not the `mcp-use` wrapper | `build-mcp-server-sdk-v1` or `build-mcp-server-sdk-v2` |
| Headless CLI testing/debugging of MCP servers with `mcpc` | `test-by-mcpc-cli` |

Do not merge the client, agent, and server scopes. Route across them when a project has multiple halves.

## Workflow

### 1. Detect What Exists

Inspect the target path:

```bash
tree -L 3 2>/dev/null || find . -maxdepth 3 -type f | sort
```

Look for:

- `package.json` with `"mcp-use"` as a dependency
- imports from `"mcp-use"`, `"mcp-use/browser"`, or `"mcp-use/react"`
- `MCPClient`, `MCPSession`, `useMcp`, `McpClientProvider`, `useMcpClient`, `useMcpServer`
- `npx mcp-use client` scripts, `mcp.json`, `mcp.config.*`, `.vscode/mcp.json`
- direct imports from `@modelcontextprotocol/sdk` that should route to raw SDK skills

Then run the version preflight when Node/npm are available:

```bash
bash skills/build-mcp-use-client/skills/build-mcp-use-client/scripts/check-mcp-use-version.sh <target-path>
```

Read `scripts/check-mcp-use-version.sh.md` before changing the script or interpreting non-obvious output.

### 2A. Existing Client Found

Run the diagnostic script first:

```bash
bash skills/build-mcp-use-client/skills/build-mcp-use-client/scripts/diagnose-client.sh <target-path>
```

Read `scripts/diagnose-client.sh.md` for the diagnostic categories and exit-code contract.

Audit the live implementation before editing:

| Audit surface | Read | Check |
|---|---|---|
| constructor, config files, sessions, imports | `references/guides/client-configuration.md`, `references/guides/environments.md` | correct entry point, current Node/package baseline, awaited session creation, cleanup |
| tools, resources, prompts, completion | `references/guides/tools.md`, `references/guides/resources.md`, `references/guides/prompts.md`, `references/guides/completion.md` | discovery before calls, `isError`, `structuredContent`, pagination, capability checks, timeouts/abort |
| callbacks, auth, notifications | `references/guides/sampling.md`, `references/guides/elicitation.md`, `references/guides/authentication.md`, `references/guides/notifications-and-logging.md` | callback names, browser secret boundary, token expiry/re-auth, list-changed handlers |
| React | `references/guides/usemcp-and-react.md` | `state` not `status`, one provider for multi-server apps, StrictMode-safe `addServer`, cleanup, all states handled |
| code mode | `references/guides/code-mode.md` | executor isolation, `executeCode()`, `search_tools()`, `client.close()` |
| production and troubleshooting | `references/patterns/production-patterns.md`, `references/patterns/anti-patterns.md`, `references/troubleshooting/common-errors.md` | reconnection, 404 recovery, idle proxy timeout, process shutdown, dropped connections |

Apply focused fixes directly. Do not rebuild a working client from scratch.

### 2B. No Client Found

If repo context gives the environment, server target, and auth shape, skip the questionnaire and build the smallest working client integration.

Pick the server target before coding:

- Existing MCP server in the repo: connect to it and discover actual tools/resources/prompts.
- Client mechanics only, no domain server: use `@modelcontextprotocol/server-everything` for a smoke test.
- Domain-specific tool required but no server exists: route to `build-mcp-use-server` first.

If no context answers the basics, ask only the missing questions:

1. Environment: Node CLI, Node service, browser app, React app, or `npx mcp-use client`.
2. Server count: one server or multiple.
3. Transport: stdio, Streamable HTTP, or mixed.
4. Auth: none, bearer token, OAuth, custom public headers.
5. React: standalone `useMcp` or provider-based multi-server app.
6. Callbacks: sampling, elicitation, notifications/logging, or none.
7. Code mode: no, trusted-local VM, E2B, or custom isolation.
8. Production hardening: basic cleanup, reconnect/health checks, or full production setup.

### 3. Build Or Fix

Use this order:

1. Install or align prerequisites with current `npm view mcp-use` metadata; do not keep old Node 18 guidance for current releases.
2. Use the right import path: `mcp-use` for Node, `mcp-use/browser` for browser, `mcp-use/react` for React.
3. Configure real server IDs and discover capabilities before hardcoding tool/resource/prompt names.
4. Add auth without printing or committing secrets.
5. Add timeouts, abort handling, cleanup, and reconnection before calling the work production-ready.
6. Validate with type/lint/tests and, when possible, a real connect/list/call/read smoke test.

## Core Surface Map

| Trigger | File | Reason |
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

### Runtime And Version

- Treat `npm view mcp-use version engines peerDependencies --json` as the source of truth for current install guidance.
- Use the bundled version script before copying examples into a project.
- Prefer examples that use the current major/minor line verified by npm metadata. Avoid stale `^1.21.0` pins.

### React

- Use one `McpClientProvider` for multi-server apps.
- Dynamic `addServer()` calls inside `useEffect` must be idempotent under React StrictMode; clean up temporary servers with `removeServer()` when appropriate.
- Gate UI and effects on all states: `discovering`, `authenticating`, `pending_auth`, `ready`, `failed`.
- Resource-reading effects must avoid setting state after unmount or after a newer request supersedes the old one.

### Code Mode

- Use the VM executor only for trusted local code.
- Use E2B or custom isolation for untrusted or multi-tenant code.
- Call `client.close()` when code mode may allocate external resources.

### Streaming And Reconnection

- Prefer Streamable HTTP for new HTTP clients; use legacy SSE only for compatibility.
- Do not build WebSocket clients for MCP.
- Route long-running tools to timeout/progress/abort guidance in `references/guides/tools.md` and production reconnection guidance in `references/patterns/production-patterns.md`.

## Non-Negotiables

1. Import from `mcp-use`, `mcp-use/browser`, or `mcp-use/react`; do not hand-roll raw SDK calls in wrapper-library client code.
2. Await `createSession()` or `createAllSessions()` before using sessions.
3. Always clean up with `closeAllSessions()` or `client.close()`; use `client.close()` for code mode.
4. Discover tools/resources/prompts before hardcoding names.
5. Handle `CallToolResult.isError`, `content`, `structuredContent`, and `_meta` deliberately.
6. Set `timeout`, `maxTotalTimeout`, and `AbortSignal` for long-running tools.
7. Put sensitive tokens server-side or in OAuth flows; browser headers are only for public/non-secret values.
8. Use `mcp.state`, not `mcp.status`; use `storageProvider`, not `persistenceProvider`.
9. Check optional capabilities such as completion before calling them.
10. Report exactly what validation ran; do not imply runtime coverage from type checks alone.

## Validation

Use the smallest honest set:

```bash
npm run typecheck
npm run lint
npm test
npx tsx src/client.ts
npx mcp-use client connect --stdio "npx -y @modelcontextprotocol/server-everything" --name smoke
```

For React, also exercise the rendered states: `discovering`, `authenticating`, `pending_auth`, `ready`, and `failed`. For auth issues, test 401/403, expired refresh token, popup blocked, redirect callback failure, and `pending_auth` loops against `references/guides/authentication.md` plus `references/troubleshooting/common-errors.md`.

## Output Contract

When finishing a client task, report:

1. target path and environment: Node, browser, React, or CLI
2. servers discovered or configured
3. key APIs used: `MCPClient`, `MCPSession`, `useMcp`, provider hooks, code mode, CLI
4. validation commands actually run
5. whether runtime behavior was exercised or only type/lint checks passed
6. references consulted
7. auth/secrets caveat without printing secret values
