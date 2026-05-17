# Client Introspection Overview

`ctx.client` is the surface for inspecting the connected client. Different MCP hosts negotiate different capabilities and send different metadata. Tools that branch on host behavior (widget rendering, sampling, elicitation, locale-aware UX) read from `ctx.client`.

Most `ctx.client` methods reflect the initialize handshake and are stable for the MCP session. `ctx.client.user()` is different: it is built from per-request `_meta` and can change on each tool call.

## The full surface

| Method | Returns | Purpose |
|---|---|---|
| `info()` | `{ name?: string, version?: string }` | Client name + version from the initialize handshake |
| `can(capability)` | `boolean` | Probe a top-level capability key (for example sampling, elicitation, roots) |
| `capabilities()` | `Record<string, any>` | Full raw capabilities object as negotiated |
| `supportsApps()` | `boolean` | Convenience: does this client render MCP Apps widgets (SEP-1865)? |
| `extension(id)` | `object \| undefined` | Read raw MCP extension metadata by ID |
| `user()` | `UserContext \| undefined` | Per-invocation caller metadata (locale, location, subject, etc.) |

## Where each section lives

| Topic | File |
|---|---|
| `info()` and protocol version | `02-info-and-version.md` |
| `can()` capability gates | `03-can-capabilities.md` |
| `supportsApps()` for widgets | `04-supports-apps.md` |
| `extension()` and `user()` | `05-extension-and-user.md` |
| Reference example repo | `canonical-anchor.md` |

## Why this exists

MCP hosts vary widely. Do not maintain a host allow-list in tool code; feature-detect the actual connection:

- Use `ctx.client.can("sampling")` before `ctx.sample()`.
- Use `ctx.client.can("elicitation")` before `ctx.elicit()`.
- Use `ctx.client.supportsApps()` before returning a widget.
- Use `ctx.client.user()` only for per-invocation personalization, never auth.

## Minimal example

```typescript
import { MCPServer, text, widget } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "smart-tool", version: "1.0.0" });

server.tool(
  {
    name: "show-dashboard",
    schema: z.object({}),
    widget: {
      name: "dashboard",
      invoking: "Loading dashboard...",
      invoked: "Dashboard loaded",
    },
  },
  async (_args, ctx) => {
    const { name, version } = ctx.client.info();

    if (ctx.client.supportsApps()) {
      return widget({
        props: { ready: true },
        output: text("Dashboard loaded."),
      });
    }

    if (ctx.client.can("sampling")) {
      const r = await ctx.sample("Generate a one-line dashboard summary.", { maxTokens: 50 });
      return text(r.content.text);
    }

    const label = [name, version].filter(Boolean).join(" ") || "unknown client";
    return text(`Hello from ${label}; no widget or LLM support.`);
  }
);
```

## Trust boundary

Most `ctx.client.*` data is **client-reported and unverified**. Treat it as advisory. For verified identity, use OAuth (`ctx.auth`) — see `../11-auth/`.

| Source | Trust |
|---|---|
| `info()`, `capabilities()` | From the MCP initialize handshake — generally honest, but not signed |
| `extension()` | Client-set metadata — informational only |
| `user()` | Client-reported request metadata — **never** for access control |
| OAuth-verified `ctx.auth` | Cryptographically verified — use for security |

## Related

- Capability flags drive elicitation: `../12-elicitation/01-overview.md`
- Capability flags drive sampling: `../13-sampling/01-overview.md`
- Widget responses gate on `supportsApps()`: `../18-mcp-apps/`
