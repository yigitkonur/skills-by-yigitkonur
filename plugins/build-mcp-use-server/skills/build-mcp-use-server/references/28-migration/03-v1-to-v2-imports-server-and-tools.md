# Imports, Server, and Tool Registration

*Read this when migrating tool registration syntax from v1 to v2.*

## Step 1: Update imports

**v1**:
```typescript
import { MCPServer, text, object, error } from "mcp-use/server";
```

**v2**:
```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";
```

`mcp-use/server` no longer exists. Import `MCPServer` from root. Response helpers (`text`, `object`) are deprecated shims; prefer raw MCP envelopes.

## Step 2: Server constructor

**v1**:
```typescript
const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth: oauthAuth0Provider(...), // import from "mcp-use/server"
});
```

**v2**:
```typescript
import { MCPServer } from "mcp-use";
// OAuth moved to separate imports — see 05-v1-to-v2-auth.md

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  // oauth config here if used (see section 05)
});
```

## Step 3: Tool registration — definition-first callback

**v1** — Inline schema + callback as `cb` field:
```typescript
server.tool({
  name: "weather",
  description: "Get weather",
  schema: z.object({ city: z.string() }),
  cb: async ({ city }) => text(await fetchWeather(city)),
});
```

**v2** — Separate definition (arg 1) and callback (arg 2):
```typescript
export const weather = server.tool(
  {
    name: "weather",
    description: "Get weather",
    inputSchema: z.object({ city: z.string() }),
    outputSchema: z.object({ forecast: z.string() }),
  },
  async ({ city }) => {
    const forecast = await fetchWeather(city);
    return {
      content: [{ type: "text", text: JSON.stringify({ forecast }) }],
      structuredContent: { forecast },
    };
  }
);
```

**Changes**:
- `schema` → `inputSchema` (matches MCP wire field name; `schema` still works as alias but is deprecated)
- **Add `outputSchema`** (required if tool has a View; enables client-side validation)
- **Export as const** (required for `mcp-env.d.ts` View type generation)
- Callback is **2nd argument**, not `cb` field
- Return raw `{ content, structuredContent }` instead of `text(...)` helper

## Step 4: Export every static tool

All tools declared at module level must be exported:

```typescript
// ✓ Correct
export const search = server.tool({ name: "search", ... }, async (...) => {...});
export const details = server.tool({ name: "details", ... }, async (...) => {...});

// ✗ Not exported — View typing breaks
const dynamic = server.tool({ name: "dynamic", ... }, async (...) => {...});

// ✓ Re-export from other modules
export { getTrending } from "./tools/trending.js";
```

Dynamic tools (from loops, config, OpenAPI) cannot be exported as `ToolRef`. Call them from Views with:
```typescript
import { useDynamicTool } from "mcp-use/react";
const lookup = useDynamicTool<InputType, OutputType>("tool-name");
```

## Step 5: Response shape — raw MCP envelopes

**v1** — Helpers:
```typescript
return text("Result");
return object({ count: 5, items: [] });
return error("Something failed");
return widget({ props: {...}, output: text("...") });
```

**v2** — Raw envelopes:
```typescript
// Text result
return {
  content: [{ type: "text", text: "Result" }],
  structuredContent: { /* structured data matching outputSchema */ },
};

// Error
return {
  content: [{ type: "text", text: "Something failed" }],
  isError: true,
};

// Multiple content blocks (markdown + object)
return {
  content: [
    { type: "text", text: "## Summary\n..." },
    { type: "text", text: JSON.stringify({ data: [...] }) },
  ],
  structuredContent: { data: [...] },
};
```

**Why**: Raw envelopes are type-safe and align with MCP spec. Helpers (`text()`, `object()`, etc.) remain as **deprecated upgrade shims only**; beta.66 does not specify a removal release.

## Step 6: Deprecated helpers — if you must use them

Helpers are exported for backward compatibility only:

```typescript
import { text, object, array, error, markdown, mix, image, audio, binary } from "mcp-use";

// These work but are deprecated:
return text("Hello");  // Alias for { content: [{ type: "text", text: "Hello" }] }
return error("Failed"); // Alias for { content: [...], isError: true }
```

Migrate away from them and prefer raw envelopes; beta.66 does not specify when the shims will be removed.

## Step 7: Tool annotations (unchanged)

Annotations remain, no syntax change:

```typescript
export const destructive = server.tool(
  {
    name: "delete-item",
    inputSchema: z.object({ id: z.string() }),
    outputSchema: z.object({}),
    annotations: {
      destructiveHint: true,
      readOnlyHint: false,
      openWorldHint: false,
      idempotentHint: true,
    },
  },
  async ({ id }) => ({ content: [...], structuredContent: {} })
);
```

## Step 8: What about `visibility`?

**New in v2**: Tool `visibility` field (for MCP Apps):

```typescript
export const hidden = server.tool(
  {
    name: "internal",
    visibility: "app", // model-hidden, View-callable only
    inputSchema: z.object({}),
    outputSchema: z.object({}),
  },
  async () => ({ content: [...], structuredContent: {} })
);
```

Values: `"model"` (default, model-visible) | `"app"` (View-callable only).

---

**Next**: See `04-v1-to-v2-responses-and-helpers.md` for detailed response envelope patterns.
