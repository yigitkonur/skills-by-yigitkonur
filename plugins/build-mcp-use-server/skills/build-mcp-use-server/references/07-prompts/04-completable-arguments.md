# Completable Arguments

*Read this when you need to provide autocomplete suggestions for prompt arguments or resource template variables.*

## What it does

`completable()` wraps a schema field (Zod, ArkType, Valibot, etc.) so the server provides argument suggestions to clients during the `completion/complete` flow. The user gets typeahead on the argument; validation works the same way.

---

## Static completion (fixed list)

Use a static array when values are known and small:

```typescript
import { MCPServer, completable } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "example", version: "1.0.0" });

server.prompt(
  {
    name: "code-review",
    description: "Review code with language completion",
    schema: z.object({
      language: completable(
        z.string().describe("Programming language"),
        ["python", "typescript", "go", "rust", "java"]
      ),
      code: z.string().describe("Code to review"),
    }),
  },
  async ({ language, code }, ctx) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `Review this ${language} code:\n\`\`\`${language}\n${code}\n\`\`\``,
      },
    }],
  })
);
```

The server applies **case-insensitive prefix filtering** automatically. Do not filter the list yourself.

---

## Dynamic completion (callback)

Use a callback for values that depend on DB lookups, API calls, or already-resolved arguments:

```typescript
server.prompt(
  {
    name: "analyze-project",
    description: "Analyze a project",
    schema: z.object({
      userId: z.string().describe("User ID"),
      projectId: completable(
        z.string().describe("Project ID"),
        async (value, context) => {
          // Fetch projects for the user
          const userId = context?.arguments?.userId as string | undefined;
          if (!userId) return [];
          
          const projects = await db.query(
            "SELECT id, name FROM projects WHERE user_id = ?",
            [userId]
          );
          
          // Filter by current partial input
          return projects
            .filter((p) => p.id.startsWith(value))
            .map((p) => p.id);
        }
      ),
    }),
  },
  async ({ projectId }, ctx) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `Analyze project ${projectId}`,
      },
    }],
  })
);
```

Callback receives:

| Argument | Type | Purpose |
|---|---|---|
| `value` | `string` | Current partial input the user has typed |
| `context.arguments` | `Record<string, unknown> \| undefined` | Already-resolved argument values for this prompt invocation |

Use `context.arguments` to chain completions — a later field's suggestions can depend on an earlier field's value.

---

## Signature

```typescript
import { completable } from "mcp-use";

completable<T extends StandardSchemaV1>(
  schema: T,
  complete: ReadonlyArray<string | number | boolean> | CompletionCallback
): ReturnType<typeof sdkCompletable<T>>
```

| Parameter | Type | Purpose |
|---|---|---|
| `schema` | Zod / ArkType / Valibot | The field schema (any Standard Schema v1) |
| `complete` | `ReadonlyArray<string \| number \| boolean>` or `CompletionCallback` | Static values (mixed types allowed in one array) or a dynamic suggestion function |

---

## Important rules

- **Apply refinements to the schema, not the completable result.** Zod refinements (`.describe()`, `.default()`, etc.) that clone the schema will drop the completion marker if applied after `completable()`:

```typescript
// ✓ Correct
language: completable(
  z.string().describe("Language"),
  ["python", "typescript"]
)

// ✗ Wrong (describe after completable loses completion)
language: completable(z.string(), [...]).describe("Language")
```

- **`.optional()` is an exception** — the SDK unwraps optionals when looking for completions, so it's safe:

```typescript
language: completable(z.string(), ["python", "typescript"]).optional()
```

- **Server truncates at 100 items.** The SDK's completion handler slices the result to `values.slice(0, 100)` and sets `hasMore: true` when the source list is longer — suggestions beyond the 100th are dropped before they reach the client, not just visually clipped by the client.
- **The static array accepts `string | number | boolean`** — mixed types are fine (`createPrefixCompletion` normalizes them). A `CompletionCallback` must return `string[]` (or `Promise<string[]>`) regardless of the field's underlying type.

---

## Use for prompts only

`completable()` works for prompt schemas. For resource template variable completion, use the separate `complete` field on the template definition instead (see `references/06-resources/03-resource-templates.md`).

| You want completion for | Use |
|---|---|
| Prompt argument | `completable()` in the prompt schema |
| Resource URI template variable | `complete` on the template definition |

---

## v2 Note

In v2, the completable function requires `StandardSchemaV1` (the base Standard Schema spec), not the full `StandardSchemaWithJSON`. The prompt schema itself is `StandardSchemaWithJSON`, but individual completable fields use the lighter standard. This is automatic and transparent when you call `completable(z.string(), ...)`.
