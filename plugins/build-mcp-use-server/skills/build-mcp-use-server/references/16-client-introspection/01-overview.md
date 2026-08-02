# Client Introspection Overview

*Read this when detecting client capabilities, views support, or user context in a tool callback.*

Within a tool callback, `ctx.client` provides query methods for the capabilities and features the **current client request** declares. This is per-request metadata, not session-level or user-level state.

## Available Methods

| Method | Returns | Use when |
|--------|---------|----------|
| `can(capability: string)` | `boolean` | Checking if client supports a named feature |
| `capabilities()` | `ClientCapabilities` | Inspecting full capability object |
| `extension(id: string)` | Extension settings \| `undefined` | Detecting MCP app support via `io.modelcontextprotocol/ui` |
| `info()` | Client name/version (partial) | Logging client identity |
| `user()` | OpenAI-specific hints (partial) | Accessing end-user locale, location, etc. (OpenAI clients only) |
| `supportsViews()` | `boolean` | Detecting MCP app / view support |

## Typical Usage

```typescript
export const complexTool = server.tool(
  { name: "analyze", inputSchema: z.object({ data: z.string() }) },
  async ({ data }, ctx) => {
    // Check capabilities
    if (ctx.client.supportsViews()) {
      // Return structured content for MCP app rendering
      return {
        content: [{ type: "text", text: "Analysis result" }],
        structuredContent: { chart: {...} },
      };
    }

    // Fallback for text-only clients
    return {
      content: [{ type: "text", text: "Analysis result (text)" }],
    };
  }
);
```

## What v2 Removed

Old v1 APIs like `ctx.client.can("apps")` or `ctx.client.supportsApps()` do not exist in v2. Use `ctx.client.supportsViews()` or check the `io.modelcontextprotocol/ui` extension instead.

See `references/16-client-introspection/02-capabilities.md` for detailed usage.
