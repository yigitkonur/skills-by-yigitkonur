# `completable()` — Argument Autocomplete

This is the canonical home for `completable()`. In `mcp-use@1.26.0`, use it for prompt arguments. Resource template variable completion uses `callbacks.complete` instead.

## What it does

`completable()` wraps a Zod type so the server provides prompt argument suggestions to the client during the `completion/complete` flow. The user gets typeahead on the argument; the schema still validates final input the same way.

## Signature

```typescript
import { completable } from "mcp-use/server";

completable(zodType, valuesOrCallback)
```

| `valuesOrCallback` | Behavior |
|---|---|
| Primitive array | Static list — server filters case-insensitively by prefix |
| `(value, context?) => Promise<T[]> \| T[]` | Dynamic — your callback returns suggestions |

## List-based completion

Use a static array when the valid values are known and small:

```typescript
import { z } from "zod";
import { completable } from "mcp-use/server";

server.prompt(
  {
    name: "code-review",
    description: "Review code with language completion",
    schema: z.object({
      language: completable(z.string(), ["python", "javascript", "typescript", "java", "cpp"]),
      code: z.string().describe("The code to review"),
    }),
  },
  async ({ language, code }) => text(`Review this ${language} code: ${code}`),
);
```

The server applies **case-insensitive prefix filtering** automatically. You do not need to filter the list yourself.

## Callback-based completion

Use a callback for dynamic values — DB lookups, API calls, values that depend on already-resolved arguments:

```typescript
server.prompt(
  {
    name: "analyze-project",
    description: "Analyze a project with dynamic completion",
    schema: z.object({
      userId: z.string(),
      projectId: completable(z.string(), async (value, context) => {
        const userId = context?.arguments?.userId;
        const projects = await fetchUserProjects(userId);
        return projects.filter((p) => p.id.startsWith(value)).map((p) => p.id);
      }),
    }),
  },
  async ({ projectId }) => text(`Analyzing project ${projectId}...`),
);
```

The callback receives:

| Argument | Description |
|---|---|
| `value` | The current partial input the user has typed |
| `context.arguments` | Map of already-resolved argument values for this invocation |

Use `context.arguments` to chain completions — the second argument's suggestions can depend on the first argument's value.

## Tool schemas

Do not teach `completable()` for `server.tool()` schemas in this skill. The published `mcp-use@1.26.0` completion helper is documented for prompts and resource templates, and the MCP completion refs wired by the package are prompt refs and resource-template refs, not tool refs.

## URI template completion is different

Resource template variable completion uses `callbacks.complete` on the **template definition**, not `completable()`:

```typescript
server.resourceTemplate(
  {
    name: "user",
    uriTemplate: "users://{userId}",
    callbacks: {
      complete: { userId: ["user-1", "user-2", "user-3"] },
    },
  },
  async (uri, { userId }) => object(await db.getUser(userId)),
);
```

See `../06-resources/03-resource-templates.md`. Same prefix-filter semantics, different surface.

## Decision matrix

| You want completion for | Use |
|---|---|
| Prompt argument | `completable()` in the prompt schema |
| Resource URI template variable | `callbacks.complete` on the template definition |

## Filtering rules

- Static lists: server applies case-insensitive prefix filter on the user's partial input
- Callback returns: server passes the user's partial as `value`; you return the already-filtered list
- Don't return more than ~100 suggestions — clients clip the list
- Suggestions must be `string[]` — no objects, no labels
