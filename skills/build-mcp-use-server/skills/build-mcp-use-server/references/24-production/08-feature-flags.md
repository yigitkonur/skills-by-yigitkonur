# Feature flags

Two distinct uses, two distinct mechanisms:

| Use | Mechanism | Effect |
|---|---|---|
| Gate **availability** of a tool | Conditional `server.tool(...)` registration at startup | Tool absent from `tools/list`; model can't see or call it |
| Gate **behavior** inside a tool | Runtime check at call time | Tool visible, but executes a different path or rejects with `error()` |

Pick by who needs to know. If a tier or rollout means a tool simply doesn't exist for a tenant, gate availability. If it exists but does less, gate behavior.

## Conditional registration

Read flags once at startup, register only the enabled tools. The model sees a clean `tools/list` for that deployment.

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const flags = Object.freeze({
  experimental: process.env.ENABLE_EXPERIMENTAL === "true",
  betaSearch: process.env.ENABLE_BETA_SEARCH === "true",
  imageGen: process.env.ENABLE_IMAGE_GEN === "true",
});

const server = new MCPServer({ name: "my-server", version: "1.0.0" });

if (flags.experimental) {
  server.tool(
    {
      name: "experimental-foo",
      description: "Experimental tool. Not yet stable.",
      schema: z.object({ input: z.string() }),
    },
    async ({ input }) => text(`experimental: ${input}`)
  );
}

if (flags.imageGen) {
  registerImageGenTools(server);
}
```

Module-level `if`s are clearer than per-tool registration files; for many flags, group registration by feature module:

```typescript
// src/tools/image-gen.ts
export function registerImageGenTools(server: MCPServer) {
  server.tool({ name: "generate-image", /* ... */ }, handler);
  server.tool({ name: "edit-image", /* ... */ }, handler);
}
```

## Per-tenant rollout

When the same process serves multiple tenants, you can't gate at registration. Gate at call time using `ctx.auth` or a tenant ID from the session:

```typescript
const TENANTS_WITH_IMAGE_GEN = new Set(["acme", "globex"]);

server.tool(
  { name: "generate-image", schema: z.object({ prompt: z.string() }) },
  async ({ prompt }, ctx) => {
    const tenant = ctx.auth?.claims?.tenant ?? "default";
    if (!TENANTS_WITH_IMAGE_GEN.has(tenant)) {
      return error("Image generation not enabled for your account.");
    }
    return await generate(prompt);
  }
);
```

Use `error()` (not `throw`) — this is an expected, recoverable state for the model. See `04-error-strategy.md`.

## Listing tools per tenant

`tools/list` results can vary per session. Use MCP-op middleware on `mcp:tools/list` to filter what each session sees, but **only** if you also gate at the call site (`tools/call`) — a malicious client can call a tool by name even if you hide it from listing.

Two-layer pattern:

```typescript
// Filter what each tenant sees in tools/list
server.use("mcp:tools/list", async (c, next) => {
  const tenant = c.get("auth")?.claims?.tenant ?? "default";
  await next();
  // post-process the result to remove tools this tenant can't use
  // (exact API depends on op-layer interface)
});

// Always re-check at the call site
server.tool({ name: "generate-image", /* ... */ }, async (args, ctx) => {
  const tenant = ctx.auth?.claims?.tenant ?? "default";
  if (!TENANTS_WITH_IMAGE_GEN.has(tenant)) return error("Not enabled.");
  // ...
});
```

For middleware basics, see `08-server-config/05-middleware-and-custom-routes.md`.

## Runtime config refresh

Reading flags from env at startup is final until restart. For runtime-mutable flags (a flag service, Redis config), read on every call — but cache briefly to avoid hammering the source:

```typescript
let flagCache: { value: boolean; expiresAt: number } | null = null;

async function isImageGenEnabled(tenant: string): Promise<boolean> {
  const now = Date.now();
  if (flagCache && now < flagCache.expiresAt) return flagCache.value;
  const value = await flagService.get(`image-gen:${tenant}`);
  flagCache = { value, expiresAt: now + 30_000 };
  return value;
}
```

A 10–60 second TTL is usually right. Shorter spams the flag service; longer makes rollouts feel slow.

## Gradual rollouts

For percentage-based rollouts, hash a stable key (tenant ID, user ID — never IP) and compare to a threshold:

```typescript
import { createHash } from "crypto";

function rolloutBucket(key: string): number {
  const h = createHash("sha256").update(key).digest();
  return h[0] / 255; // 0..1
}

const enabled = rolloutBucket(tenantId) < 0.10; // 10%
```

Hashing the key (not `Math.random()`) means the same tenant gets the same answer every call — no flicker.

## Telling the model what's available

Don't put unused tools in `tools/list` and rely on `error("not enabled")` at the call site. The model wastes tokens trying tools that always fail and may loop. Keep the list aligned with what's actually callable for that session.

## Don't

- Don't register a tool, then `error()` on every call for the wrong tier — hide it instead.
- Don't read flags from inside hot paths without caching.
- Don't gate sensitive behavior on env flags shipped from staging — verify in production logs that the flag has the expected value.
- Don't use `Math.random()` for percentage rollouts — hash a stable key so users get a consistent experience.
- Don't forget the call-site check when filtering `tools/list` — list filtering is UX, not security.
