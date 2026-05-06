# `.describe()` and Annotations

Two separate signals to the client and the model: `.describe()` on each schema field tells the model what to put there; `annotations` on the tool definition tell the client how to treat the tool.

## `.describe()` discipline

The Zod schema becomes JSON Schema on the wire. JSON Schema's `description` field is what the model reads to decide what value to send. Without `.describe()`, the model guesses from the field name alone.

```typescript
// Bad — model guesses
z.object({
  query: z.string(),
  status: z.enum(["open", "closed"]),
})

// Good — model has explicit guidance
z.object({
  query: z.string().min(1).describe("Search keyword. 1-200 chars."),
  status: z.enum(["open", "closed"]).describe("Filter by ticket status."),
})
```

Rules:

- Every field gets `.describe()`. No exceptions.
- Describe purpose, format, and constraints — not the type.
- Mention what happens when the field is omitted if it has `.default()` or `.optional()`.
- For enums, describe what each value means if it isn't obvious from the literal.

```typescript
z.enum(["created", "updated", "priority"])
  .default("created")
  .describe("Sort field. Defaults to creation date.")
```

## Tool annotations

Annotations are behavioral hints clients use for confirmation dialogs, tool filtering, and execution policy. They go in the `annotations` object on the tool definition.

| Annotation | Type | Default | Meaning |
|---|---|---|---|
| `readOnlyHint` | `boolean` | `false` | Tool does not modify any state. |
| `destructiveHint` | `boolean` | `true` | Tool may delete or irreversibly alter data. Only meaningful when `readOnlyHint` is `false`. |
| `idempotentHint` | `boolean` | `false` | Repeated calls with same args produce the same result. Only meaningful when `readOnlyHint` is `false`. |
| `openWorldHint` | `boolean` | `true` | Tool interacts with external/unbounded systems (web, third-party APIs). |

These four are the only standard MCP annotation fields. Do **not** use `requiresAuth`, `rateLimit`, or `deprecated` — they are not part of the MCP SDK `ToolAnnotations` type. Express auth and rate-limit in the description and enforce them in the handler.

## When to set each

**`readOnlyHint: true`** — every read/search/get/list tool. Clients can run these without confirmation.

```typescript
annotations: {
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false,
}
```

**`destructiveHint: true`** — every delete/remove/drop tool, plus `update` operations that overwrite without history. Clients may prompt the user before invoking.

```typescript
annotations: {
  readOnlyHint: false,
  destructiveHint: true,
  idempotentHint: false,
  openWorldHint: false,
}
```

**`idempotentHint: true`** — operations safe to retry: PUT-style updates, upserts, "ensure exists" tools. Lets clients retry on transport errors without user confirmation.

**`openWorldHint: false`** — tool acts only on internal data the server controls (your DB, your filesystem). Set `true` for tools that hit third-party APIs, the public web, or any system the server doesn't fully own.

## Why this matters

Clients use these hints to:

- Skip confirmation for read-only tools (faster UX).
- Prompt before destructive tools (safety).
- Retry idempotent tools automatically on transport failure.
- Filter tool lists by capability for restricted contexts.

A delete tool without `destructiveHint: true` is a foot-gun. A search tool without `readOnlyHint: true` annoys users with confirmation dialogs.

## Combined example

```typescript
server.tool(
  {
    name: "delete-ticket",
    description: "Permanently delete a support ticket by ID.",
    schema: z.object({
      ticketId: z.string()
        .regex(/^TKT-\d+$/)
        .describe("Ticket ID like TKT-12345. Hard delete — not recoverable."),
    }).strict(),
    annotations: {
      readOnlyHint: false,
      destructiveHint: true,
      idempotentHint: true,   // deleting an already-deleted ticket is a no-op
      openWorldHint: false,   // internal database only
    },
  },
  async ({ ticketId }) => {
    await db.deleteTicket(ticketId);
    return text(`Deleted ${ticketId}`);
  }
);
```
