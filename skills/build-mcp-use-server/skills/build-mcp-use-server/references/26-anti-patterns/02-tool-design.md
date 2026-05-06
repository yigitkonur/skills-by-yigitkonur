# Tool design

Common tool-design mistakes. For schema-specific anti-patterns see `03-schemas.md`; for response shape see `04-responses.md`.

## Don't write god-tools

One tool, one job. A tool that takes an `action` enum and dispatches internally hides what the server can actually do — the model sees a single ambiguous entry in `tools/list` and has to guess.

```typescript
// ❌ one tool does CRUD + list — model can't tell what's possible
server.tool({
  name: "manage-users",
  schema: z.object({
    action: z.enum(["create", "read", "update", "delete", "list"]),
    id: z.string().optional(),
    data: z.any().optional(),
  }),
}, handler);
```

```typescript
// ✅ one tool per operation — each has its own schema and description
server.tool({
  name: "create-user",
  description: "Register a new user account.",
  schema: z.object({
    name: z.string().describe("Full display name"),
    email: z.string().email().describe("Valid email address"),
  }),
}, createUserHandler);

server.tool({
  name: "get-user",
  description: "Retrieve a user profile by ID.",
  schema: z.object({ userId: z.string().uuid().describe("User UUID") }),
}, getUserHandler);
```

## Don't return free-form text when structure is possible

If the result has shape, return shape. Free-form `text(JSON.stringify(...))` makes downstream parsing fragile and loses MIME signaling.

```typescript
// ❌ stringifies an object as text — model has to re-parse
return text(JSON.stringify({ name, stars, language }));
```

```typescript
// ✅ object() — proper MIME, structured surface, parseable
return object({ name, stars, language });
```

For when to combine `content` and `structuredContent` (so both content-first and structured-first clients see the answer), see `05-responses/08-content-vs-structured-content.md`.

## Don't omit `outputSchema` when consumers will parse the response

If callers (clients, downstream tools) parse `structuredContent`, give them a schema. Without `outputSchema`, the response shape is implicit — a refactor silently breaks consumers.

```typescript
// ❌ no outputSchema — consumers parse blind
server.tool({
  name: "get-user",
  schema: z.object({ id: z.string() }),
}, async ({ id }) => object({ id, name: "..." }));
```

```typescript
// ✅ outputSchema declares the contract
const UserOut = z.object({
  id: z.string(),
  name: z.string(),
  createdAt: z.string().datetime(),
});

server.tool({
  name: "get-user",
  description: "Get a user by ID. Returns id, name, createdAt.",
  schema: z.object({ id: z.string() }),
  outputSchema: UserOut,
}, async ({ id }) => object(await db.findUser(id)));
```

See `04-tools/07-input-schema-vs-output-schema.md`.

## Don't omit `.describe()` on fields

The description string is the model's only signal for what to put in a field. Without it, the model relies on the field name alone — `id` could mean a user ID, an order ID, or a UUID; it has no way to tell.

```typescript
// ❌ unlabeled fields
schema: z.object({
  id: z.string(),
  type: z.string(),
  amount: z.number(),
})
```

```typescript
// ✅ describe every field
schema: z.object({
  id: z.string().describe("Order UUID"),
  type: z.enum(["refund", "charge", "credit"]).describe("Transaction type"),
  amount: z.number().int().describe("Amount in cents"),
})
```

## Don't omit `description` on the tool itself

Tool descriptions guide selection across the tool registry. A missing description means the model picks based on the name alone — which collides easily with similar names from other tools.

```typescript
// ❌
server.tool({ name: "search", schema: ... }, handler);

// ✅
server.tool({
  name: "search",
  description: "Search internal docs by keyword. Returns at most 20 hits with title and URL.",
  schema: ...,
}, handler);
```

## Don't return raw API responses

External APIs return 100+ fields, most irrelevant. Dumping them costs the model tokens to read and increases the chance of confusion. Filter on the server.

```typescript
// ❌ entire GitHub API response
const data = await fetch(`https://api.github.com/repos/${repo}`).then((r) => r.json());
return text(JSON.stringify(data));
```

```typescript
// ✅ only what the model needs
return object({
  name: data.full_name,
  stars: data.stargazers_count,
  language: data.language,
  description: data.description,
});
```

## Don't use generic names

| Generic | Specific |
|---|---|
| `process` | `process-payment`, `process-refund` |
| `run` | `run-migration`, `run-export` |
| `handle` | `handle-webhook` (still vague — prefer `receive-stripe-webhook`) |
| `data` | `get-user-stats`, `get-billing-history` |
| `manage` | one tool per management action |

Generic names collide across servers and force the model to read every description before picking. Action-verb + noun (`search-issues`, `create-ticket`) makes selection obvious.

Use kebab-case names. Camel/snake case violate MCP convention and cause ecosystem inconsistency.

## Don't take 8+ parameters

Once a tool has more than 5–7 parameters, the model starts hallucinating arguments or omitting required ones. If your schema is sprawling, the tool is doing too much — split it.

| Smell | Fix |
|---|---|
| Long flat parameter list (8+) | Split into focused sibling tools |
| Several mutually exclusive groups | Each group is its own tool |
| Optional flags that change return shape | Each shape is its own tool |

## Don't lie about annotations

| Annotation | Truth |
|---|---|
| `readOnlyHint: true` | The tool genuinely has no side effects. Setting it on a mutating tool to skip confirmation is a trust violation. |
| `destructiveHint: true` | The tool deletes/destroys/cancels something. Always set it on those. |

Clients trust annotations to decide whether to ask the user before invoking. Lying causes destructive actions to fire without confirmation.

## Quick checklist

| Don't | Do | Why |
|---|---|---|
| God-tool with `action` enum | One tool per operation | Model can see what's possible |
| Free-form text for structured data | `object()` / `outputSchema` | Parseable, schema'd |
| Missing `.describe()` | Describe every field and tool | Model's only signal |
| Raw API passthrough | Filter to needed fields | Token cost, confusion |
| Generic name (`process`, `run`) | `verb-noun` (`process-payment`) | Selection clarity |
| 8+ parameters | Split tool | Hallucination risk |
| `readOnlyHint` on mutating tool | Set accurately | Trust contract |
