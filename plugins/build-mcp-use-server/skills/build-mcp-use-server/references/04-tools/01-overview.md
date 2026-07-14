# Tools Overview

A tool is a model-callable function exposed by the MCP server. The model picks a tool by `name`, fills in arguments matching `schema`, the server validates them, runs the handler, and returns a response.

## Signature

```typescript
server.tool(
  config: ToolDefinition,
  handler: (args, ctx) => CallToolResult | Promise<CallToolResult>
)
```

`server.tool()` is chainable — each call returns the server.

```typescript
server
  .tool({ name: 'greet', schema: z.object({ name: z.string() }) }, async ({ name }) => text(`Hi ${name}`))
  .tool({ name: 'list', schema: z.object({}) }, async () => object({ items: [] }));
```

## Lifecycle

1. **Register.** Call `server.tool(config, handler)` once at startup. The server stores the definition and forwards the Zod `schema` as the SDK `inputSchema`.
2. **List.** Client calls `tools/list`. In `mcp-use@1.26.0`, the runtime forwards `name`, `title`, `description`, `inputSchema`, `annotations`, and `_meta` to the SDK. It does not forward `outputSchema`.
3. **Call.** Client sends `tools/call` with `name` and `arguments`. Server parses JSON, validates against the Zod `schema`, and invokes the handler with `(args, ctx)`.
4. **Respond.** Handler returns a `CallToolResult` (use response helpers — see `05-responses/01-overview-decision-table.md`). Server emits over the active transport.

## What you write

- A `name` (kebab-case, action-verb + noun).
- A `description` (LLM-facing — what it does, when to use it, what it returns).
- A `schema` (Zod object with `.describe()` on every field — see `03-zod-schemas.md`).
- Optional `annotations` (read-only / destructive hints — see `04-describe-and-annotations.md`).
- Optional `outputSchema` (TypeScript/codegen hint only in `mcp-use@1.26.0` — see `07-input-schema-vs-output-schema.md`).
- A handler `async (args, ctx) => result`.

## What the server does for you

- Converts `schema` to JSON Schema and publishes it on `tools/list`.
- Validates arguments before your handler runs.
- Surfaces validation errors back to the client as a structured error message the model can self-correct against.
- Sets `_meta.mimeType` on the response when you use response helpers.

## Files in this cluster

- `02-registering-a-tool.md` — full `ToolDefinition` field reference.
- `03-zod-schemas.md` — single canonical Zod reference.
- `04-describe-and-annotations.md` — `.describe()` discipline and the four standard annotations.
- `05-the-ctx-object.md` — what handlers get on `ctx`.
- `06-validation-pipeline.md` — what happens between client send and handler run.
- `07-input-schema-vs-output-schema.md` — when to add `outputSchema`.
- `08-tool-anti-patterns.md` — what to never do.
- `canonical-anchor.md` — the reference repo to read.

**Canonical doc:** [manufact.com/docs/typescript/server/tools](https://manufact.com/docs/typescript/server/tools)
