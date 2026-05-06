# `ctx.client.supportsApps()`

`ctx.client.supportsApps()` is the convenience check for **MCP Apps Extension** support (SEP-1865) — i.e. whether the connected client can render widgets returned via `widget({ ... })`.

```typescript
if (!ctx.client.supportsApps()) {
  return text("This client cannot render widgets.");
}
return widget({ props: {...}, message: "..." });
```

It reflects the current session's initialize capabilities. Different clients connecting to the same server may return different values within the same `MCPServer` instance.

## Why this exists

`widget(...)` responses carry structured props and widget-facing metadata that only MCP Apps-capable hosts can interpret.

`supportsApps()` is the gate.

## What it checks

In mcp-use 1.26.0, `supportsApps()` returns `true` only when the raw client capabilities include:

```typescript
capabilities.extensions?.["io.modelcontextprotocol/ui"]?.mimeTypes
  ?.includes("text/html;profile=mcp-app")
```

Always feature-detect. Do not infer widget support from `ctx.client.info().name`.

## Pattern: widget-or-text

```typescript
import { MCPServer, text, widget } from "mcp-use/server";
import { z } from "zod";

server.tool(
  { name: "show-dashboard", schema: z.object({}), widget: { name: "dashboard" } },
  async (_args, ctx) => {
    if (!ctx.client.supportsApps()) {
      return text("Dashboard data: load via the dashboard URL.");
    }
    return widget({
      props:   { ready: true, items: await loadItems() },
      output:  text("Dashboard loaded."),
    });
  }
);
```

## Pattern: tiered fallback

```typescript
server.tool(
  { name: "summarize-and-show", schema: z.object({ data: z.string() }) },
  async ({ data }, ctx) => {
    // Tier 1 — widget if supported
    if (ctx.client.supportsApps()) {
      return widget({
        props:  { data },
        output: text("View loaded."),
      });
    }
    // Tier 2 — sampling for rich text if supported
    if (ctx.client.can("sampling")) {
      const r = await ctx.sample(`Summarize: ${data}`, { maxTokens: 200 });
      return text(r.content.text);
    }
    // Tier 3 — plain pass-through
    return text(`Data: ${data.slice(0, 200)}...`);
  }
);
```

## Relationship to `can("sampling")` and `can("elicitation")`

`supportsApps()` is independent of sampling and elicitation. A widget-capable client may or may not support sampling; an LLM-capable client may not render widgets. Always check each capability separately.

## Underlying MCP extension

`supportsApps()` is short for checking the `io.modelcontextprotocol/ui` extension. You can also query the extension directly:

```typescript
const ui = ctx.client.extension("io.modelcontextprotocol/ui");
// e.g. { mimeTypes: ["text/html;profile=mcp-app"] } | undefined
```

For most code, prefer `supportsApps()` — it's the readable shortcut. Use `extension(id)` if you need the raw metadata (for example to inspect supported MIME profiles). See `05-extension-and-user.md`.

## CSP and base URL

When you do return a widget, the server's `baseUrl` is automatically included in the widget's CSP. Configuration of CSP and `baseUrl` is documented under MCP Apps — see `../18-mcp-apps/` (specifically the server-surface CSP metadata reference).

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Returning `widget(...)` without `supportsApps()` guard | Guard or fall back to `text()` |
| Branching on `info().name === "chatgpt"` instead of `supportsApps()` | Feature-detect |
| Caching `supportsApps()` at module scope | It's per-connection — read inside the handler |
