# Error handling

*Read this when a tool call fails validation, runtime, or auth.*

## Error envelope (isError: true)

Return error **without throwing**:

```typescript
return {
  isError: true,
  content: [{ type: "text", text: "User not found: user_123" }],
};
```

Never throw exceptions from tool callbacks; return error envelopes instead.

## When to error vs throw

| Scenario | Action | Example |
|----------|--------|---------|
| Validation failed (caught before callback) | SDK auto-errors | Invalid input schema |
| Auth denied (token expired) | Return error | `{ isError: true, content: [...] }` |
| Dependency unavailable (API down) | Return error | `isError: true` + helpful message |
| Unhandled exception in callback | Logs, SDK wraps as error | Crash in async handler |

## Example: graceful degradation

```typescript
server.tool(
  {
    name: "get-user",
    inputSchema: z.object({ id: z.string() }),
    outputSchema: z.object({ id: z.string(), name: z.string() }),
  },
  async ({ id }, ctx) => {
    try {
      const user = await db.users.get(id);
      if (!user) {
        return {
          isError: true,
          content: [{ type: "text", text: `User not found: ${id}` }],
        };
      }
      return {
        content: [{ type: "text", text: `Found user: ${user.name}` }],
        structuredContent: { id: user.id, name: user.name },
      };
    } catch (err) {
      return {
        isError: true,
        content: [{
          type: "text",
          text: `Database error: ${err instanceof Error ? err.message : "unknown"}`,
        }],
      };
    }
  }
);
```

**Pattern:** Catch, log (if needed), return error envelope.

## Error in structured context

Errors **do not** include `structuredContent`; keep messages plain text:

```typescript
// Wrong
return {
  isError: true,
  content: [{ type: "text", text: "..." }],
  structuredContent: { code: 404 },  // SDK ignores
};

// Right
return {
  isError: true,
  content: [{ type: "text", text: "Not found (error code 404)" }],
};
```

## Auth errors

When `ctx.auth` is missing or insufficient:

```typescript
server.tool(
  { name: "admin-action", inputSchema: z.object({ id: z.string() }) },
  async ({ id }, ctx) => {
    if (!ctx.auth) {
      return {
        isError: true,
        content: [{ type: "text", text: "Unauthenticated. Please log in." }],
      };
    }
    if (!ctx.auth.permissions.includes("admin")) {
      return {
        isError: true,
        content: [{ type: "text", text: "Insufficient permissions (requires admin)" }],
      };
    }
    // Continue...
  }
);
```

Do not throw; return error.
