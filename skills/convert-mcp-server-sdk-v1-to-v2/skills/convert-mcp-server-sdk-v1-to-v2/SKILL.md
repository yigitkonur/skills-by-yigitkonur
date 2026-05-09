---
name: convert-mcp-server-sdk-v1-to-v2
description: "Use skill if you are porting an existing MCP TypeScript server from @modelcontextprotocol/sdk v1.x to the v2 split-package SDK — package renames, ServerContext, Zod v4."
---

# Convert MCP Server (SDK v1 → v2)

Port an existing MCP TypeScript server from `@modelcontextprotocol/sdk` v1.x to the v2 split-package SDK (`@modelcontextprotocol/server`, `/client`, `/node`, `/express`, `/hono`). Covers package split, import rewrites, the `extra → ctx` handler-context mapping, Zod v3→v4 with raw-shape removal, error-class rename, request-handler key strings, framework adapter packages, and the OAuth-router replacement story.

**v2 is currently a pre-release alpha.** As of 2026-05-08, the latest published version is `2.0.0-alpha.2`; the milestone is `v2.0.0-bc` (backwards-compat PR series). Most production servers should stay on `@modelcontextprotocol/sdk@^1.x` for now and use this skill to plan, test, and stage the migration — not to flip a production switch.

**When to use a different skill instead:**

- Building a *new* server on v1.x (no existing code) → `build-mcp-server-sdk-v1`
- Building a *new* server on v2 (no existing code) → `build-mcp-server-sdk-v2`
- Maintaining or bug-fixing an existing v1 server with no plans to upgrade → `build-mcp-server-sdk-v1`
- Already on v2 and just need help extending it → `build-mcp-server-sdk-v2`
- Using the `mcp-use` wrapper library (not the official SDK) → `build-mcp-use-server`

**How to detect this is the right skill:** the project has `@modelcontextprotocol/sdk` (v1, single package) in `package.json`, the user wants to move to `@modelcontextprotocol/server` (v2, split packages), and there is existing handler/transport/auth code to port — not a greenfield build.

## Core rules

- Pick a migration strategy *before* touching files — full rewrite, meta-package shim if published for the target alpha, HTTP-layer auth transition, or stay on v1. Do not assume the v2 alpha meta-package exists; verify package availability before relying on it.
- Never mix v1 and v2 packages in the same module graph except deliberately during a staged migration. Two `McpServer` classes from two packages will not interoperate; types will silently diverge.
- Pin to an exact alpha version (`@modelcontextprotocol/server@2.0.0-alpha.2`) — `^` ranges across alphas will surface breaking changes mid-migration.
- Migrate handler context (`extra` → `ctx`) and schemas (`ZodRawShape` → `z.object`) together for any tool you touch. Half-migrated handlers are the single biggest source of runtime errors during a port.
- Replace `mcpAuthRouter` / `requireBearerAuth` / `OAuthServerProvider` deliberately — server-side OAuth is removed from v2. If a target alpha publishes `@modelcontextprotocol/server-auth-legacy`, treat it as a transition; otherwise stay on v1 or integrate at the HTTP layer (custom Bearer middleware, Passport, jose) and forward `authInfo` via `req.auth`.
- Upgrade Node to 20+ and add `"type": "module"` to `package.json` — v2 is ESM-only; CommonJS dual-publish is not supported.
- Keep a working v1 branch alive until v2 graduates from alpha. The v2 branch is a delivery target; the v1 branch is the running production until then.

## Workflow

### 1 — Inventory the v1 server

Read `package.json`, `tsconfig.json`, and every file under `src/`. Record:

- Every `@modelcontextprotocol/sdk/*` import path used (subpath exports are the migration unit).
- Every `extra.*` field accessed in handlers (`signal`, `authInfo`, `sessionId`, `requestId`, `requestInfo`, `_meta`, `sendNotification`, `sendRequest`, `closeSSEStream`, `taskId`, `taskStore`).
- Every transport class instantiated (`StdioServerTransport`, `StreamableHTTPServerTransport`, `SSEServerTransport`, `WebStandardStreamableHTTPServerTransport`).
- Every Zod schema shape: raw-object shorthand vs full `z.object()`.
- Every error throw: `McpError(ErrorCode.X, ...)` call sites and the codes used.
- Every `setRequestHandler(SomeRequestSchema, ...)` call (schema-based registration).
- Every framework wiring point: `createMcpExpressApp`, `requireBearerAuth`, `mcpAuthRouter`, custom `app.use` middleware that depends on the SDK.

This inventory drives the strategy choice in step 2.

For a deterministic first pass, run `bash scripts/check-v2-feasibility.sh <project-dir>` from this skill directory and read `scripts/check-v2-feasibility.md`. Use the report to focus the manual inventory; do not treat it as a substitute for reading the code.

### 2 — Choose the migration strategy

| Strategy | When | Effort | Trade-off |
|---|---|---|---|
| **Full rewrite** | Small server (≤200 LOC tools, ≤2 transports, no OAuth router) | Hours | Cleanest end state, full v2 API access |
| **Meta-package shim** | Medium server, many subpath imports, and target alpha publishes the shim | Hours | Keeps v1 import paths working under v2; defer rewrites tool-by-tool |
| **HTTP-layer auth transition** | Production OAuth server using `mcpAuthRouter` | Days | Replace SDK OAuth with app/framework middleware in a separate auth migration |
| **Stay on v1** | OAuth-heavy, large, or alpha-allergic | Zero | No code change; revisit when v2 reaches stable |

Read `references/guides/migration-strategy.md` before committing. Record the choice in the change description so future maintainers know what state the server is in.

### 3 — Rewrite packages and imports

Per `references/guides/package-and-imports.md`. Smallest unit: one import line at a time.

- `@modelcontextprotocol/sdk/server/mcp.js` → `@modelcontextprotocol/server`
- `@modelcontextprotocol/sdk/server/stdio.js` → `@modelcontextprotocol/server`
- `@modelcontextprotocol/sdk/server/streamableHttp.js` → `@modelcontextprotocol/node` (renamed `NodeStreamableHTTPServerTransport`)
- `@modelcontextprotocol/sdk/server/express.js` → `@modelcontextprotocol/express`
- `@modelcontextprotocol/sdk/client/index.js` → `@modelcontextprotocol/client`
- `@modelcontextprotocol/sdk/types.js` (errors only) → `@modelcontextprotocol/server`

If using the meta-package shim, this step is a no-op until you choose to migrate a specific module.

For direct-package migrations, preview the mechanical import portion with `bash scripts/migrate-imports.sh <project-dir>` and read `scripts/migrate-imports.md`; rerun with `--write` only after reviewing the dry-run. Avoid it for schema, `ctx`, auth-router, request-handler-key, or transport-lifecycle rewrites.

### 4 — Rewrite schemas

Per `references/guides/schema-and-errors.md`.

- `import { z } from "zod"` → `import * as z from "zod/v4"`
- `inputSchema: { name: z.string() }` (raw shape) → `inputSchema: z.object({ name: z.string() })` (full schema). v2 rejects raw shapes outright.
- Drop `zod-to-json-schema` — v2 emits JSON Schema 2020-12 natively via `z.toJSONSchema()`.

### 5 — Rewrite handlers (extra → ctx)

Per `references/guides/handler-context-mapping.md`. Most-frequent moves:

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

No-args tool handler: `(extra) => ...` becomes `(ctx) => ...` — same shape, renamed.

### 6 — Rewrite errors and request-handler keys

Per `references/guides/schema-and-errors.md`.

- `McpError` / `ErrorCode` (from `/types.js`) → `ProtocolError` / `ProtocolErrorCode` (from `@modelcontextprotocol/server`).
- `setRequestHandler(CallToolRequestSchema, ...)` → `setRequestHandler("tools/call", ...)` (method string instead of Zod schema).

### 7 — Replace auth

Per `references/guides/auth-replacements.md`.

- If using `mcpAuthRouter` and the target alpha publishes `@modelcontextprotocol/server-auth-legacy`, keep the v1 router through that transition package; otherwise stay on v1 until auth can move out of the SDK.
- If integrating fresh: do auth at the HTTP layer (Express/Hono middleware) and forward the user's identity into `authInfo` via `req.auth`. The Express adapter passes `req.auth` through to `ctx.http?.authInfo` automatically when set by upstream middleware.
- The `better-auth` MCP plugin currently targets v1 import paths and is flagged for deprecation in favor of better-auth's OAuth Provider Plugin — do not adopt it new for a v2 migration.

### 8 — Replace transports and adapters

Per `references/guides/transports-and-adapters.md`.

- `StreamableHTTPServerTransport` → `NodeStreamableHTTPServerTransport` (`@modelcontextprotocol/node`).
- `SSEServerTransport` → removed; clients on legacy SSE must move to Streamable HTTP first.
- `createMcpExpressApp()` from SDK subpath → `createMcpExpressApp()` from `@modelcontextprotocol/express` (same name, different package).
- Hono is new in v2: `createMcpHonoApp()` from `@modelcontextprotocol/hono` (note: the official SDK package, not the unrelated community `@hono/mcp` package).

### 9 — Validate and stage rollout

Per `references/patterns/validation-and-rollback.md`.

- Add `"type": "module"` to `package.json`. Bump engines to Node 20+.
- Run type-check first, then the existing unit/integration test suite.
- Test with `npx @anthropic-ai/mcp-inspector` for browser/manual smoke coverage.
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

- Prefer the meta-package shim for any server with more than ~10 subpath import sites only when the target alpha actually publishes it — otherwise choose direct packages or stay on v1.
- Prefer separating auth from the SDK port — auth is high-stakes; use a verified transition package only when it exists for the target alpha.
- Prefer pinned alpha versions over `^` ranges — alphas can publish breaking changes between any two patches.
- Prefer migrating one handler end-to-end (imports + schema + ctx + errors) rather than one concern across all handlers — it bounds the test surface per PR.
- Treat `ctx.http?` as nullable everywhere — stdio transport leaves it `undefined`. Code that assumed `extra.authInfo` was always present needs an explicit branch.

## Guardrails

- Never run an alpha SDK in production before staging it in a non-prod environment with realistic traffic for at least one week.
- Never mix `@modelcontextprotocol/sdk` and `@modelcontextprotocol/server` in the same compiled bundle without the meta-package shim — TypeScript will accept the duplicate types, but `instanceof` checks and class identity break at runtime.
- Never assume `req.auth` propagates without explicitly wiring HTTP-layer auth middleware — v2 does not provide a server-side OAuth router that does this for you.
- Never delete the v1 branch or `package-lock.json` until v2 has been stable in production for at least one full release cycle. Rollback readiness is the cheapest insurance during alpha.
- Never `npm install` v2 packages without `--save-exact` — Yarn/pnpm equivalents apply.
- Never adopt the `better-auth` MCP plugin as a new dependency in a v2 migration — it's marked for deprecation and currently targets v1 import paths.

## Output contract

When a port finishes, report:

- migration strategy chosen and why
- package/version changes, exact alpha pins, and whether the v2 meta-package remains
- handlers/tools migrated, especially schema and `ctx` rewrites
- auth path chosen: stay on v1, verified transition package, HTTP-layer auth, or no auth
- transports/adapters changed
- validation rung reached: type-check, unit tests, Inspector, `test-by-mcpc-cli`, real client, staging/canary
- rollback status: v1 branch/image/lockfile preserved, or blocker if not verified
- residual risks from v2 alpha status

After the port lands, use `build-mcp-server-sdk-v2` for ongoing v2 maintenance.

## Reference routing

Use the smallest set relevant to the migration step.

### Plan and decide

| Reference | When to read |
|---|---|
| `references/guides/migration-strategy.md` | Choosing between full rewrite, meta-package shim if available, HTTP-layer auth transition, and "stay on v1" |

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

This skill is source-verified against the v1.x branch (latest stable: `@modelcontextprotocol/sdk@^1.x`) and the v2 alpha packages (`@modelcontextprotocol/server@2.0.0-alpha.2`, `@modelcontextprotocol/client@2.0.0-alpha.2`, `@modelcontextprotocol/node@2.0.0-alpha.2`, `@modelcontextprotocol/express@2.0.0-alpha.2`, `@modelcontextprotocol/hono@2.0.0-alpha.2`). npm verification on 2026-05-09 found no published `@modelcontextprotocol/core`, `@modelcontextprotocol/sdk@2.0.0-alpha.2`, or `@modelcontextprotocol/server-auth-legacy`; re-check the v2 changelog and npm package availability before each migration sprint.

After the port lands, the destination skill is `build-mcp-server-sdk-v2` for ongoing v2 work.
