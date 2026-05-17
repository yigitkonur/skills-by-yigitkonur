# Host Capability Detection

Different MCP clients support different feature sets. A tool that returns a widget against a CLI client returns nothing useful. Detect capability before deciding what to send.

## `ctx.client.supportsApps()`

The tool handler receives a `ctx` argument with a `client` introspection surface. `supportsApps()` returns `true` when the connected client advertises MCP Apps (or ChatGPT Apps) support during the initialize handshake.

```typescript
import { widget, text } from "mcp-use/server";

server.tool(
  {
    name: "show-dashboard",
    description: "Show the analytics dashboard",
    schema: z.object({}),
    widget: { name: "dashboard" },
  },
  async (_params, ctx) => {
    if (!ctx.client.supportsApps()) {
      return text(
        "Your client does not support interactive widgets. " +
        "Visitors today: 12,453. Page views: 45,231."
      );
    }

    const data = await loadDashboard();
    return widget({
      props: data,
      output: text(`Dashboard loaded — ${data.visitors} visitors today.`),
    });
  }
);
```

For the full client introspection API (other capabilities, host name/version, structured `client.info`), see `../16-client-introspection/04-supports-apps.md`.

## Graceful fallback patterns

### Pattern 1 — Branch at the top

Cleanest. Good when the text version is meaningfully different (compressed, more verbose, etc.).

```typescript
async (params, ctx) => {
  if (!ctx.client.supportsApps()) return text(buildPlainTextSummary(data));
  return widget({ props: data, output: text(buildShortSummary(data)) });
}
```

### Pattern 2 — Always send `widget()` with a meaningful `output`

Simpler. The `output` text is the fallback — text-only clients see only that field via `content`. Works because `widget()` always populates `content`.

```typescript
async (params) => {
  const data = await fetch(params.id);
  return widget({
    props: data,
    output: text(formatPlainText(data)),  // ← non-widget clients see this
  });
}
```

This is the recommended default unless you have a strong reason to compute different data for text-only clients.

### Pattern 3 — Conditional widget config

Skip the widget entirely when unsupported. Useful when computing the props is expensive and useless without rendering.

```typescript
async (params, ctx) => {
  if (!ctx.client.supportsApps()) {
    return text("Use a widget-capable client to see the chart.");
  }
  const expensiveData = await aggregate();
  return widget({ props: expensiveData, output: text("Chart loaded.") });
}
```

## When `uiResource` alone is enough vs. widget + tool

| Goal | Use |
|---|---|
| Purely presentational widget, props from URL params | `server.uiResource({ exposeAsTool: true })` and stop |
| Server fetches/computes data; widget renders it | Custom tool with `widget` config + `widget()` helper |
| Same UI, multiple data sources / parameter shapes | One `uiResource`, many tools that link to it via `widget.name` |

## Test the fallback

Run your server in the MCP Inspector with widgets disabled, or hit it from a CLI client (`mcpc`, plain `curl` to `tools/call`). Confirm the `content` field is human-readable on its own. If the text fallback says "See widget for details", the fallback is broken.
