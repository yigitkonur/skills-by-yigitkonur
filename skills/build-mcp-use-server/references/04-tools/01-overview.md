# Tools Overview

*Read this when you're learning to register and return tool results in mcp-use v2.*

Tools are server-side functions that clients call with validated input and get structured results back. mcp-use v2 enforces a definition-first architecture: **separate the tool contract from the handler**.

## Definition-First Model

Every tool has two parts:

1. **Definition** — the shape `{ name, description, inputSchema, outputSchema?, annotations?, view? }`
2. **Callback** — async handler that receives parsed input and context

```typescript
export const getTool = server.tool(
  {
    name: "tool-name",
    description: "What the tool does",
    inputSchema: z.object({ /* fields */ }),
    outputSchema: z.object({ /* result shape */ }),  // required for views
  },
  async (input, ctx) => ({
    content: [{ type: "text", text: "..." }],
    structuredContent: { /* matches outputSchema */ },
  })
);
```

**Always export static tools as `const`** — `mcp-env.d.ts` (auto-generated) derives view types from exported `ToolRef` names.

## Input & Output Validation

- **Input:** SDK validates against `inputSchema` **before** the callback runs. Invalid input → error response (callback never fires).
- **Output:** When `outputSchema` is set, SDK validates `structuredContent` **after** the callback returns. Mismatch → error response.

## Context & Capabilities

Every callback receives `ctx: RequestContext<TUser, HasOAuth, TEnv>`, which provides:
- `ctx.signal` — AbortSignal from client
- `ctx.client` — capability queries (`can()`, `capabilities()`, `supportsViews()`, etc.)
- `ctx.auth` — user & token (if OAuth configured)
- `ctx.sendLog()` — async logging to client
- `ctx.reportProgress()` — async progress reporting
- `ctx.sendNotification()` — async one-way notification

## Response Envelopes

Handlers return raw MCP result shapes, **never helpers**. The SDK converts to wire format automatically.

- **Success:** `{ content: [{ type: "text", text: "..." }], structuredContent?: {...} }`
- **Error:** `{ isError: true, content: [{ type: "text", text: "error message" }] }`
- **Input required** (elicitation): `{ type: "input_required", inputRequest: { ... } }`

## Key Files

- `02-registering-a-tool.md` — tool definition shape and export requirements
- `03-schemas-standard-schema-and-zod-v4.md` — Standard Schema v1, Zod v4 patterns
- `04-describe-and-annotations.md` — field descriptions and behavioral hints
- `05-the-ctx-object.md` — full RequestContext surface
- `06-validation-pipeline.md` — when validation runs, error shapes
- `07-input-schema-vs-output-schema.md` — when to use each
- `08-tool-anti-patterns.md` — common mistakes (thrown errors, z.any(), undescribed fields)
- `canonical-anchor.md` — one complete, runnable example
