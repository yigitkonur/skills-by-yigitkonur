---
name: convert-mcp-server-sdk-v1-to-v2
description: "Use skill if you are porting an existing MCP TypeScript server from @modelcontextprotocol/sdk v1.x to the v2 split-package SDK with package renames, ServerContext, and Zod v4."
---

# Convert MCP Server (SDK v1 → v2)

Port an existing MCP TypeScript server from `@modelcontextprotocol/sdk` v1.x (single package) to the v2 split-package SDK: `@modelcontextprotocol/server`, `/client`, `/node`, `/express`, `/hono`. The v2 surface changes are package split, `extra → ctx` handler-context mapping, Zod v3→v4 with raw-shape removal, `McpError → ProtocolError`, method-string request-handler keys, framework adapter packages, and OAuth-router removal.

**v2 is currently a pre-release alpha.** Latest published: `2.0.0-alpha.2` (verified on npm, 2026-05-09). Most production servers should stay on `@modelcontextprotocol/sdk@^1.x` and use this skill to plan, test, and stage the migration — not to flip a production switch.

## When to use this skill

Trigger on actual migration intent applied to an existing v1 codebase. Italicized phrases below are concrete tells:

- *"port my MCP server to v2"*, *"upgrade @modelcontextprotocol/sdk to the new split packages"*
- *"replace `@modelcontextprotocol/sdk/server/mcp.js` imports with `@modelcontextprotocol/server`"*
- *"my handlers use `extra.signal`/`extra.authInfo` and I need the v2 equivalent"*
- *"convert `inputSchema: { name: z.string() }` raw shapes to v2"*, *"upgrade Zod v3 to v4 in MCP tools"*
- *"replace `mcpAuthRouter` / `requireBearerAuth` / `OAuthServerProvider`"*
- *"swap `StreamableHTTPServerTransport` for `NodeStreamableHTTPServerTransport`"*
- *"`McpError`/`ErrorCode` → `ProtocolError`/`ProtocolErrorCode` rename"*
- *"`setRequestHandler(CallToolRequestSchema, ...)` → method-string keys"*

### Detection signals (all should be true)

- `package.json` contains `@modelcontextprotocol/sdk` (the v1 single package).
- The user states intent to migrate, upgrade, port, or convert — not just maintain v1.
- There is existing handler/transport/auth code to transform — not a greenfield build.

### Do NOT use this skill for

- **New v1 server** (no existing code) → use `build-mcp-server-sdk-v1`.
- **New v2 server** (greenfield on v2 alpha) → use `build-mcp-server-sdk-v2`.
- **Maintaining or bug-fixing a v1 server** with no migration intent → use `build-mcp-server-sdk-v1`.
- **Already on v2** and just need to extend it → use `build-mcp-server-sdk-v2`.
- **Using the `mcp-use` wrapper** (not the official SDK) → use `build-mcp-use-server`.

## Core rules — load-bearing

- **Pick a strategy before touching files.** Full rewrite, meta-package shim (only if the target alpha actually publishes one), HTTP-layer auth transition, or stay on v1. Verify package availability on npm before committing.
- **Never mix v1 and v2 packages in the same module graph** except deliberately during a staged migration. Two `McpServer` classes from two packages do not interoperate; types silently diverge and `instanceof` checks break at runtime.
- **Pin to exact alpha versions** (`@modelcontextprotocol/server@2.0.0-alpha.2`). `^` ranges across alphas surface breaking changes mid-migration. Always use `--save-exact` (or pnpm/yarn equivalents).
- **Migrate handler context (`extra → ctx`) and schemas (`ZodRawShape → z.object`) together** for any tool you touch. Half-migrated handlers are the single biggest source of runtime errors.
- **Replace OAuth deliberately.** Server-side OAuth (`mcpAuthRouter`, `requireBearerAuth`, `OAuthServerProvider`) is removed from v2. If `@modelcontextprotocol/server-auth-legacy` is published for the target alpha, use it as a transition; otherwise stay on v1 or move auth to the HTTP layer (Bearer middleware, Passport, jose) and forward identity via `req.auth`.
- **Upgrade Node to 20+ and add `"type": "module"` to `package.json`.** v2 is ESM-only — CommonJS dual-publish is unsupported.
- **Keep a working v1 branch alive until v2 graduates from alpha.** v2 is a delivery target; v1 is the running production until then.

## v1 → v2 surface map

The most-used renames at a glance. Detailed per-area guides linked below.

| Area | v1 | v2 |
|---|---|---|
| Server class import | `@modelcontextprotocol/sdk/server/mcp.js` | `@modelcontextprotocol/server` |
| Stdio transport | `@modelcontextprotocol/sdk/server/stdio.js` | `@modelcontextprotocol/server` |
| HTTP transport | `StreamableHTTPServerTransport` from `…/server/streamableHttp.js` | `NodeStreamableHTTPServerTransport` from `@modelcontextprotocol/node` |
| SSE transport | `SSEServerTransport` | removed (clients must move to Streamable HTTP first) |
| Express adapter | `createMcpExpressApp` from SDK subpath | `createMcpExpressApp` from `@modelcontextprotocol/express` |
| Hono adapter | _(none)_ | `createMcpHonoApp` from `@modelcontextprotocol/hono` |
| Client | `@modelcontextprotocol/sdk/client/index.js` | `@modelcontextprotocol/client` |
| Errors | `McpError` / `ErrorCode` from `…/types.js` | `ProtocolError` / `ProtocolErrorCode` from `@modelcontextprotocol/server` |
| Request-handler key | `setRequestHandler(CallToolRequestSchema, …)` | `setRequestHandler("tools/call", …)` |
| Zod | `import { z } from "zod"` (v3) | `import * as z from "zod/v4"` |
| Tool input schema | `inputSchema: { name: z.string() }` raw shape | `inputSchema: z.object({ name: z.string() })` full schema |
| Handler signature | `(args, extra) => …` | `(args, ctx) => …` |
| Auth router | `mcpAuthRouter`, `requireBearerAuth`, `OAuthServerProvider` | removed (HTTP-layer auth or transition package) |

## extra → ctx (most-frequent moves)

| v1 | v2 |
|---|---|
| `extra.signal` | `ctx.mcpReq.signal` |
| `extra.requestId` | `ctx.mcpReq.id` |
| `extra.sendNotification(n)` | `ctx.mcpReq.notify(n)` |
| `extra.sendRequest(r, s)` | `ctx.mcpReq.send(r, s)` |
| `extra.authInfo` | `ctx.http?.authInfo` |
| `extra.requestInfo` | `ctx.http?.req` |
| `extra.closeSSEStream?.()` | `ctx.http?.closeSSE?.()` |
| `extra.sessionId` | `ctx.sessionId` (top-level, unchanged) |

`ctx.http?` is **nullable** — stdio transport leaves it `undefined`. Any code that assumed `extra.authInfo` was always defined needs an explicit branch.

## Workflow

### 1 — Inventory the v1 server

Read `package.json`, `tsconfig.json`, and every file under `src/`. Record:

- Every `@modelcontextprotocol/sdk/*` import path (subpath exports are the migration unit).
- Every `extra.*` field accessed in handlers.
- Every transport class instantiated.
- Every Zod schema shape: raw-object shorthand vs full `z.object()`.
- Every `McpError(ErrorCode.X, …)` call site and the codes used.
- Every `setRequestHandler(SomeRequestSchema, …)` call.
- Every framework wiring point: `createMcpExpressApp`, `requireBearerAuth`, `mcpAuthRouter`, custom middleware that depends on the SDK.

For a deterministic first pass, run `bash scripts/check-v2-feasibility.sh <project-dir>` from this skill directory and read `scripts/check-v2-feasibility.md`. Use the report to focus the manual inventory; do not treat it as a substitute for reading the code.

### 2 — Choose the migration strategy

| Strategy | When | Effort | Trade-off |
|---|---|---|---|
| **Full rewrite** | Small server (≤200 LOC tools, ≤2 transports, no OAuth router) | Hours | Cleanest end state, full v2 API access |
| **Meta-package shim** | Medium server, many subpath imports, target alpha publishes the shim | Hours | Keeps v1 import paths working under v2; defer rewrites tool-by-tool |
| **HTTP-layer auth transition** | Production OAuth server using `mcpAuthRouter` | Days | Replace SDK OAuth with app/framework middleware in a separate auth migration |
| **Stay on v1** | OAuth-heavy, large, or alpha-allergic | Zero | No code change; revisit when v2 reaches stable |

Read `references/guides/migration-strategy.md` before committing. Record the choice in the change description.

### 3 — Rewrite packages and imports

Per `references/guides/package-and-imports.md`. Smallest unit: one import line at a time.

For direct-package migrations, preview the mechanical import portion with `bash scripts/migrate-imports.sh <project-dir>` and read `scripts/migrate-imports.md`. Rerun with `--write` only after reviewing the dry-run. Do not use it for schema, `ctx`, auth-router, request-handler-key, or transport-lifecycle rewrites — those need hand edits.

### 4 — Rewrite schemas

Per `references/guides/schema-and-errors.md`.

- `import { z } from "zod"` → `import * as z from "zod/v4"`
- Raw shape `{ name: z.string() }` → full schema `z.object({ name: z.string() })`. v2 rejects raw shapes outright.
- Drop `zod-to-json-schema` — v2 emits JSON Schema 2020-12 natively via `z.toJSONSchema()`.

### 5 — Rewrite handlers (extra → ctx)

Per `references/guides/handler-context-mapping.md`. Use the mapping table above. No-args tool handler: `(extra) => …` becomes `(ctx) => …` — same shape, renamed.

### 6 — Rewrite errors and request-handler keys

Per `references/guides/schema-and-errors.md`. `McpError` / `ErrorCode` → `ProtocolError` / `ProtocolErrorCode`. `setRequestHandler(CallToolRequestSchema, …)` → `setRequestHandler("tools/call", …)`.

### 7 — Replace auth

Per `references/guides/auth-replacements.md`.

- If using `mcpAuthRouter` and the target alpha publishes `@modelcontextprotocol/server-auth-legacy`, keep the v1 router through that transition package; otherwise stay on v1 until auth can move out of the SDK.
- If integrating fresh: do auth at the HTTP layer (Express/Hono middleware) and forward identity into `authInfo` via `req.auth`. The Express adapter passes `req.auth` through to `ctx.http?.authInfo` automatically.
- The `better-auth` MCP plugin currently targets v1 import paths and is flagged for deprecation — do not adopt it new.

### 8 — Replace transports and adapters

Per `references/guides/transports-and-adapters.md`. Use the surface map table above. Hono is new in v2 via `@modelcontextprotocol/hono` (the official SDK package, not the unrelated community `@hono/mcp` package).

### 9 — Validate and stage rollout

Per `references/patterns/validation-and-rollback.md`.

- Add `"type": "module"` to `package.json`. Bump engines to Node 20+.
- Run type-check first, then the existing unit/integration test suite.
- Smoke-test with `npx @anthropic-ai/mcp-inspector` for browser/manual coverage.
- Use `test-by-mcpc-cli` for headless CLI smoke/regression checks when `mcpc` is available.
- Connect at least one real MCP client before production rollout.
- Stage in a non-prod environment for at least one week before flipping production traffic.
- Keep the v1 branch deployable until v2 reaches stable — alpha versions can break.

## Quick diff — minimal hello-world before/after

```typescript
// v1
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({ name: "my-server", version: "1.0.0" });
server.registerTool("greet", {
  inputSchema: { name: z.string() },                // raw shape
}, async ({ name }, extra) => {                     // (args, extra)
  await extra.sendNotification({ method: "...", params: {} });
  return { content: [{ type: "text", text: `Hi ${name}` }] };
});
await server.connect(new StdioServerTransport());

// v2
import { McpServer, StdioServerTransport } from "@modelcontextprotocol/server";
import * as z from "zod/v4";

const server = new McpServer({ name: "my-server", version: "1.0.0" });
server.registerTool("greet", {
  inputSchema: z.object({ name: z.string() }),      // full schema
}, async ({ name }, ctx) => {                       // (args, ctx)
  await ctx.mcpReq.notify({ method: "...", params: {} });
  return { content: [{ type: "text" as const, text: `Hi ${name}` }] };
});
await server.connect(new StdioServerTransport());
```

## Decision rules

- Prefer the meta-package shim only when the target alpha actually publishes it; otherwise direct packages or stay on v1.
- Prefer separating auth migration from the SDK port — auth is high-stakes; only use a verified transition package.
- Prefer pinned alpha versions over `^` ranges — alphas can publish breaking changes between any two patches.
- Prefer migrating one handler end-to-end (imports + schema + ctx + errors) over one concern across all handlers — bounds the test surface per PR.
- Treat `ctx.http?` as nullable everywhere — stdio leaves it `undefined`.

## Guardrails

- Never run an alpha SDK in production before staging it in a non-prod environment with realistic traffic for at least one week.
- Never mix `@modelcontextprotocol/sdk` and `@modelcontextprotocol/server` in the same compiled bundle without the meta-package shim — TypeScript accepts duplicate types but `instanceof` checks and class identity break at runtime.
- Never assume `req.auth` propagates without explicitly wiring HTTP-layer auth middleware — v2 has no server-side OAuth router.
- Never delete the v1 branch or `package-lock.json` until v2 has been stable in production for at least one full release cycle.
- Never `npm install` v2 packages without `--save-exact`.
- Never adopt the `better-auth` MCP plugin as a new dependency in a v2 migration — flagged for deprecation, currently targets v1 import paths.

## Output contract

When a port finishes, report:

- migration strategy chosen and why
- package/version changes, exact alpha pins, and whether the meta-package shim remains
- handlers/tools migrated, especially schema and `ctx` rewrites
- auth path chosen: stay on v1, verified transition package, HTTP-layer auth, or no auth
- transports/adapters changed
- validation rung reached: type-check, unit tests, Inspector, `test-by-mcpc-cli`, real client, staging/canary
- rollback status: v1 branch/image/lockfile preserved, or blocker if not verified
- residual risks from v2 alpha status

After the port lands, hand off to `build-mcp-server-sdk-v2` for ongoing v2 maintenance.

## Reference routing

Use the smallest set relevant to the migration step.

### Plan and decide

| Reference | When to read |
|---|---|
| `references/guides/migration-strategy.md` | Choosing between full rewrite, meta-package shim, HTTP-layer auth transition, "stay on v1" |

### Rewrite mechanics

| Reference | When to read |
|---|---|
| `references/guides/package-and-imports.md` | Package split table, import-by-import rewriter, meta-package shim usage |
| `references/guides/schema-and-errors.md` | Zod v3→v4, raw shapes, JSON Schema dialect, error class rename, request-handler key strings |
| `references/guides/handler-context-mapping.md` | Full `extra` → `ctx` field mapping, no-args handlers, http nullability, new ctx-only methods |
| `references/guides/transports-and-adapters.md` | Transport renames, Express/Hono adapters, DNS rebinding, hostHeaderValidation |
| `references/guides/auth-replacements.md` | OAuth-router replacement, custom Bearer/Passport/jose patterns, why not better-auth |

### Validate and ship

| Reference | When to read |
|---|---|
| `references/patterns/validation-and-rollback.md` | Migration test plan, dual-version coexistence, rollback playbook, alpha-pinning |

## Compatibility note

Source-verified against the v1.x branch (latest stable: `@modelcontextprotocol/sdk@^1.x`) and the v2 alpha packages (`@modelcontextprotocol/server@2.0.0-alpha.2`, `/client@2.0.0-alpha.2`, `/node@2.0.0-alpha.2`, `/express@2.0.0-alpha.2`, `/hono@2.0.0-alpha.2`). npm verification on 2026-05-09 found no published `@modelcontextprotocol/core`, `@modelcontextprotocol/sdk@2.0.0-alpha.2`, or `@modelcontextprotocol/server-auth-legacy`; re-check the v2 changelog and npm package availability before each migration sprint.
