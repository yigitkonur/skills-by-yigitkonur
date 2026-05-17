# Multi-Tenant and ChatGPT Patterns

A single MCP `Mcp-Session-Id` does not always equal a single user. The most important case: **ChatGPT establishes one shared MCP session for many end users.** Identity comes from the per-invocation client context, not the transport session.

## The two identifiers

| Identifier | Source | Lifetime | Use for |
|---|---|---|---|
| `ctx.session.sessionId` | Transport (`Mcp-Session-Id` header) | Until idle timeout / DELETE | Stream routing and transport correlation |
| `ctx.client.user()` | Per-invocation user context (e.g. ChatGPT user) | Per request | User identity, conversation scoping, locale |

Use the **session** for transport-level concerns (which SSE stream). Use **`ctx.client.user()`** for application-level personalization and scoping (which user's data, which conversation history). For full client introspection details, see `../16-client-introspection/05-extension-and-user.md`.

## `ctx.client.user()` shape

```typescript
const caller = ctx.client.user();
// {
//   subject?:               string
//   conversationId?:        string
//   locale?:                string
//   userAgent?:             string
//   timezoneOffsetMinutes?: number
//   location?: {
//     city?: string; region?: string; country?: string;
//     timezone?: string; latitude?: string; longitude?: string;
//   }
// }
```

All fields are optional and client-reported. Always guard:

```typescript
const userId = ctx.client.user()?.subject ?? null;
if (!userId) return text("No caller metadata");
```

## ChatGPT shared-session pattern

```typescript
import { MCPServer, object } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "chatgpt-app", version: "1.0.0" });

server.tool(
  { name: "identify-caller", schema: z.object({}) },
  async (_args, ctx) => object({
    mcpSession:   ctx.session?.sessionId ?? null,    // shared transport session
    user:         ctx.client.user()?.subject ?? null, // individual user
    conversation: ctx.client.user()?.conversationId ?? null,
    locale:       ctx.client.user()?.locale ?? null,
  }),
);
```

In ChatGPT, every user invoking your server hits the same `mcpSession` but yields different `user.subject` / `conversationId` values. **Never key tenant-scoped data by `sessionId`** in this environment — you would mix users.

## Tenant-scoped data: correct keying

```typescript
server.tool(
  { name: "list-my-notes", schema: z.object({}) },
  async (_args, ctx) => {
    const userId = ctx.client.user()?.subject;
    if (!userId) return object({ scopeKey: null, notes: [] });

    // CORRECT: use this key for your own tenant-scoped datastore.
    return object({ scopeKey: `user:${userId}`, notes: [] });
  },
);
```

| Key choice | Right for | Wrong for |
|---|---|---|
| `ctx.session.sessionId` | Stream routing, per-connection caches | Tenant data — leaks across users in shared-session hosts |
| `ctx.client.user()?.subject` | User-owned business data | Anonymous edge tools |
| `ctx.client.user()?.conversationId` | Chat-scoped scratchpads, transient state | Anything that should outlive the chat |

## Combining with OAuth

`ctx.client.user()` is unverified host metadata. When OAuth is configured (see `../11-auth/`), use `ctx.auth` for authorization and verified identity; keep `ctx.client.user()` for personalization or ChatGPT conversation scoping.

```typescript
server.tool(
  { name: "whoami", schema: z.object({}) },
  async (_args, ctx) => {
    const user = ctx.client.user();
    return text(`Hello, ${user?.subject ?? "anonymous"}`);
  },
);
```

## Rules

1. Never assume one session = one user.
2. Read advisory host identity from `ctx.client.user()`, not from `ctx.session`.
3. Scope persistent data by `subject`, transient data by `conversationId`, transport state by `sessionId`.
4. Always guard `ctx.client.user()` with `?.` — anonymous calls are valid.
5. In stateless mode, `ctx.session` is `undefined`; `ctx.client.user()` may still be present if the host supplied it.
