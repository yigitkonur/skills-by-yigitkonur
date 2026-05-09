# Schema design

How to design MCP tool input schemas that LLMs fill correctly on the first try, across Claude, ChatGPT, Cursor, and Goose. Schemas are the second-most-read text on a tool — after the description — and the model's compliance rate is bounded by them. Cross-link to `tools.md` for tool-shape decisions and `client-compatibility.md` for which features each client actually honors.

---

## The ≤6 top-level params rule

Every additional top-level parameter measurably degrades tool-call accuracy. Community telemetry and production audits converge on the same numbers: 3-6 parameters is the sweet spot, 6-15 is the upper bound, 15-40 needs a split, and 40+ is mandatory split.

| Param count | Behavior |
|---|---|
| 1-3 | Highest accuracy. Trivial schemas. |
| 4-6 | Sweet spot. Enough expressiveness without overload. |
| 7-15 | Acceptable if the schema stays flat. Watch for missed args on small models. |
| 16-40 | Split into 2-3 tools or use the action-routed facade pattern below. |
| 40+ | Mandatory split. Frontier models drop arguments; smaller models hallucinate. |

The same rule applies recursively. If a parameter is a nested object with its own 8 fields, the model still has to fill 8 things — the count it's compiling against is total leaves, not top-level keys. Flatten.

GPT-style models are especially prone to "self-checking" on nested schemas: they construct a valid input, then second-guess themselves and refuse to call the tool entirely. A flat 6-parameter version of the same schema lands the call. Source: r/mcp community discussion, 2025-07.

---

## Flatten over nest

Two-level nesting is acceptable, three or more breaks reliability. The fix is almost always to lift nested fields up and prefix their names.

Bad — nested object:

```typescript
server.tool("search", {
  query: z.string(),
  filters: z.object({
    dateRange: z.object({
      start: z.string(),
      end: z.string(),
    }),
    status: z.enum(["active", "archived"]),
    tags: z.array(z.string()),
  }),
});
```

Good — flat schema, same capability:

```typescript
server.tool("search", {
  query: z.string(),
  startDate: z.string().optional().describe("Start date (ISO 8601)"),
  endDate: z.string().optional().describe("End date (ISO 8601)"),
  status: z.enum(["active", "archived"]).optional(),
  tags: z.string().optional().describe("Comma-separated tags"),
});
```

Rules of thumb:

- Treat `z.array()` of primitives as acceptable; `z.array(z.object())` as risky.
- Never nest two or more levels.
- When the workload needs real complexity, split into multiple tools rather than one mega-schema.
- If the nested object is genuinely repeating (rows in a batch), pass it as TSV or JSON inside a single `string` field and parse server-side.

---

## Zod vs JSON Schema vs typed wrappers

The MCP wire format is JSON Schema, but most servers author against a typed wrapper.

| Authoring layer | Strengths | Pitfalls |
|---|---|---|
| Raw JSON Schema | No translation step; what you write is what the model sees. | Verbose; easy to drift from server-side validation. |
| Zod (TypeScript) | Single source of truth for runtime + schema; rich coercion primitives. | Generators may emit non-deterministic key order — re-emit at every cold start invalidates prompt cache. Pin a deterministic serializer. |
| Pydantic (Python) | Same single-source-of-truth advantages as Zod. | Same drift risk; double-check that `BaseModel` field order is preserved by the wrapper. |
| ts-rest / typia / etc. | Codegen pipelines; clean type story. | Often generate `oneOf`/`anyOf` constructs that break Gemini (see cross-model rules below). |

The portability rule: whichever layer you use, log the **emitted JSON Schema** at server boot. Lint it against the cross-model rules. Don't trust the wrapper to do this for you.

---

## Type coercion at the schema layer

LLMs serialize all tool arguments as JSON. Type coercion bugs are the single largest source of silent tool failures: the model sends `"3"` instead of `3` or `"false"` instead of `false`, the server crashes with a Zod / Pydantic validation error, and the model gets a cryptic message it can't recover from.

Fix it at the schema, not at the handler.

Coerced number:

```typescript
// Breaks when the LLM sends "3"
count: z.number().describe("Number of results")

// Handles "3", 3, "3.5" gracefully
count: z.coerce.number().describe("Number of results")
```

Coerced boolean (the canonical pattern from the Sequential Thinking server):

```typescript
const coercedBoolean = z.preprocess((val) => {
  if (typeof val === "boolean") return val;
  if (typeof val === "string") {
    const v = val.toLowerCase();
    if (v === "true") return true;
    if (v === "false") return false;
  }
  return val;
}, z.boolean());

server.tool("search", {
  query: z.string(),
  includeArchived: coercedBoolean.optional().default(false)
    .describe("Include archived results"),
}, async ({ query, includeArchived }) => {
  // includeArchived is always a real boolean here
});
```

`z.coerce` is zero-cost at runtime and eliminates an entire class of round-trip failures.

---

## Defaults, optional fields, enums, unions

### Defaults

Apply defaults only to optional fields. Required-with-default confuses several model implementations — they treat the field as "must be supplied" and refuse to omit it.

```typescript
// Wrong
maxResults: z.number().default(10)  // looks required

// Right
maxResults: z.number().optional().default(10)
```

Defaults that match the most common case reduce token cost. If 95% of calls want `limit=20`, default to 20 — most invocations skip the parameter entirely.

### Optional vs required

Required fields force the model to think about them. Each one extends decision time and the chance of getting the wrong value. Optional + default is almost always the better choice unless the parameter genuinely has no sensible default.

The required count is usually 1-3. With 5+ required fields, reread the tool boundary — you're probably wrapping an API endpoint when you should be wrapping an intent.

### Enums

Enums dramatically improve valid call rates compared to free-form strings. Two rules:

1. Cap each enum at 10 values. Larger enums degrade accuracy across all models. Split with a leading "mode" enum that narrows the scope.
2. Describe each value inline so the model gets semantics, not just labels.

Bad — enum without context:

```typescript
livecrawl: z.enum(["fallback", "preferred"])
```

Good — enum with inline descriptions:

```typescript
livecrawl: z.enum(["fallback", "preferred"]).describe(
  "Live crawl mode — 'fallback': use live crawling as backup if the cached " +
  "version is unavailable; 'preferred': always prioritize live crawling over " +
  "cache (default: 'fallback')."
)
```

The Exa MCP server uses this pattern — without the inline description, models defaulted to `"preferred"` (sounds better) and burned crawl budget. With the description, they default to `"fallback"` correctly.

### Unions — avoid

Union types (`z.union()`, `anyOf` in JSON Schema) are the single most-mishandled construct. LLMs frequently pick the wrong branch or produce malformed hybrid output.

Bad — union for dates:

```typescript
date: z.union([
  z.string().datetime(),
  z.number().describe("Unix timestamp"),
  z.enum(["today", "yesterday", "last_week"]),
])
```

Good — flexible string + server-side parsing:

```typescript
date: z.string().describe(
  "Date in any format: ISO 8601, Unix timestamp, or relative ('yesterday', 'last week')."
)
```

Then normalize in the handler:

```typescript
import { parseDate } from "chrono-node";

async function handler({ date }: { date: string }) {
  const parsed = parseDate(date) ?? new Date(date);
  if (!parsed || isNaN(parsed.getTime())) {
    return {
      content: [{ type: "text", text: "Could not parse date. Try ISO 8601 like '2024-01-15'." }],
      isError: true,
    };
  }
  // Use `parsed` — guaranteed valid Date
}
```

Return the normalized form in the response (`tools.md` § Return normalized inputs) so the agent learns the canonical format.

---

## Format constraints — express in description, not validators

JSON Schema's `format` keyword is inconsistently supported. Claude honors most of it; GPT ignores almost all; Gemini ignores nearly all of it. Don't rely on `format: "uri"` for validation.

Pair regex constraints with example error messages instead:

```typescript
// Bad — opaque
nodeId: z.string().regex(/^I?\d+[:|-]\d+/)

// Good — regex + working example in the error
nodeId: z.string().regex(
  /^I?\d+[:|-]\d+/,
  "Node ID must be like '1234:5678' or 'I5666:180910;1:10515'."
)
```

The Figma Context MCP server uses this exact pattern — Figma node IDs have a non-obvious format, and providing examples in error messages lets the model self-correct on the next call. Apply the principle to every regex:

```typescript
color: z.string().regex(/^#[0-9a-fA-F]{6}$/, "Must be hex like '#FF5733'.")
version: z.string().regex(/^\d+\.\d+\.\d+$/, "Must be semver like '1.2.3'.")
schedule: z.string().regex(/^(\S+\s){4}\S+$/, "Must be cron like '0 9 * * 1'.")
```

The error message is the model's teaching surface. A good example in the error message means the retry almost always succeeds.

---

## Cross-model portability — 7 hard rules

If the server is consumed by Claude, ChatGPT, Cursor, and Goose, schemas that work in one client can silently disappear in another. Each model has a different JSON Schema subset; a schema that crashes Gemini drops the tool from that client's context entirely.

The hard rules:

1. **No `oneOf` / `anyOf` / `allOf`.** Gemini ignores tools containing them. When the workload needs a sum type, accept a permissive string and route server-side.
2. **Max 3 levels of nesting.** GPT-class models degrade beyond 3; Gemini breaks at 5.
3. **No `$ref`.** Most clients don't resolve schema references. Inline every definition.
4. **No `format` validators beyond `date-time` and `email`.** GPT and Gemini ignore the rest. Describe the format in the `description` field.
5. **No `default` on required fields.** Apply defaults only to optional fields.
6. **Keep enums under 10 values.** Larger enums measurably reduce accuracy. Split with a leading mode enum.
7. **Use `additionalProperties: false`.** Helps every model interpret the schema as strict.

Compatibility matrix (community testing, 2025-09):

| Feature | Claude | GPT-class | Gemini |
|---|---|---|---|
| `oneOf` / `anyOf` | Supported | Supported | Ignored — drops the tool |
| `$ref` | Supported | Varies | Ignored |
| `format` constraints | Supported | Ignored | Ignored |
| 5+ levels nesting | Supported | Degraded | Breaks |
| Enum >20 values | Supported | Degraded | Degraded |
| `additionalProperties: false` | Supported | Supported | Supported |

A 30-line lint script catches the common violations:

```typescript
function validatePortability(schema: any): string[] {
  const issues: string[] = [];
  if (schema.oneOf || schema.anyOf) issues.push("Remove oneOf/anyOf for Gemini compatibility");
  if (schema.$ref) issues.push("Inline $ref for cross-client compatibility");
  if (countNestingDepth(schema) > 3) issues.push("Nesting too deep (>3) for GPT reliability");
  if (Array.isArray(schema.enum) && schema.enum.length > 10) issues.push("Large enum (>10) degrades accuracy");
  return issues;
}
```

Run it in CI on every tool registration.

---

## Tool name characters

Use only `[a-z0-9_]` in tool names. Slashes, hyphens, dots, spaces, and unicode have caused complete connection failures in production MCP clients — not validation errors, silent crashes.

Confirmed breaking characters from community reports:

- `/` — crashes early Claude Desktop silently
- `-` — breaks some tool-router middleware
- `.` — breaks OpenAI function-calling adapters
- spaces — universally rejected, error message varies
- unicode — works in some, silent failure in others

Lint at registration time:

```typescript
const SAFE_TOOL_NAME = /^[a-z][a-z0-9_]{0,63}$/;

function registerTool(name: string, ...rest: any[]) {
  if (!SAFE_TOOL_NAME.test(name)) {
    throw new Error(
      `Invalid tool name "${name}". Use only lowercase letters, digits, underscores. ` +
      `Must start with a letter. Max 64 characters.`
    );
  }
  server.tool(name, ...rest);
}
```

Add it to CI. A broken tool name takes down the entire MCP connection, not just the offending tool.

Source: anthropics/claude-code#2257 (tool name validation); modelcontextprotocol/typescript-sdk#1512 (SEP-986 tool name spec); community reports from r/mcp.

---

## Bad-vs-good examples

### Example 1 — wrapping a search API

Bad:

```typescript
server.tool("search", {
  options: z.object({
    query: z.object({
      term: z.string(),
      mode: z.enum(["exact", "fuzzy"]),
    }),
    paging: z.object({
      page: z.number(),
      size: z.number(),
    }),
    facets: z.array(z.object({
      field: z.string(),
      values: z.array(z.string()),
    })),
  }),
});
```

3 levels of nesting, 7 leaves, `z.array(z.object())`. Models miss arguments, refuse to call, or pick the wrong branch.

Good:

```typescript
server.tool("search", {
  query: z.string().describe("Search term"),
  mode: z.enum(["exact", "fuzzy"]).optional().default("fuzzy")
    .describe("'exact': literal match. 'fuzzy': edit-distance match (default)."),
  page: z.coerce.number().optional().default(1),
  size: z.coerce.number().optional().default(20),
  facets: z.string().optional()
    .describe("Comma-separated facet filters, e.g. 'category:books,year:2024'."),
});
```

Flat, 5 leaves, all coerced, facets folded into a single string parsed server-side.

### Example 2 — deploy_project with too many params

Bad — 14 required fields stuffed into one tool:

```typescript
server.tool("deploy_project", {
  repo_url: z.string(),
  branch: z.string(),
  build_cmd: z.string(),
  install_cmd: z.string(),
  env_vars: z.record(z.string()),
  domain: z.string(),
  region: z.string(),
  scaling_policy: z.object({ /* ... */ }),
  health_check: z.object({ /* ... */ }),
  rollback_policy: z.object({ /* ... */ }),
  notifications: z.array(z.string()),
  secrets: z.record(z.string()),
  tags: z.array(z.string()),
  metadata: z.record(z.unknown()),
});
```

Good — split by workflow stage, server holds the workflow:

```typescript
server.tool("deploy_configure", {
  repo_url: z.string(),
  branch: z.string().optional().default("main"),
  region: z.enum(["us-east", "us-west", "eu-west"]).optional().default("us-east"),
});

server.tool("deploy_execute", {
  config_id: z.string().describe("ID returned by deploy_configure"),
  strategy: z.enum(["rolling", "blue-green"]).optional().default("rolling"),
});

server.tool("deploy_verify", {
  deployment_id: z.string().describe("ID returned by deploy_execute"),
});
```

Three focused tools, each ≤3 params, parameter-dependency chain enforces ordering. See `agentic-patterns.md` § Parameter dependency chains.

### Example 3 — action-routed facade

Bad — 4 entity types × 4 ops × 4 params = 16+ tools, 60+ schema lines each:

```
manage_users_list, manage_users_get, manage_users_create, manage_users_delete,
manage_projects_list, ...
```

Good — one dispatcher per entity:

```typescript
server.tool("manage_user", {
  action: z.enum(["list", "get", "create", "update", "delete"])
    .describe(
      "'list': filter by role/status. 'get': by user_id. 'create': name+email required. " +
      "'update': user_id + fields to change. 'delete': irreversible."
    ),
  user_id: z.string().optional().describe("Required for get/update/delete"),
  filters: z.string().optional().describe("Used by list, e.g. 'role=admin,status=active'"),
  data: z.string().optional().describe("Used by create/update; JSON object as string"),
});
```

One tool, 4 leaves, action enum carries semantics. The handler dispatches. The combine-vs-separate decision is in `tools.md` § CRUD — combined vs separate decision.

---

## Cross-references

- `tools.md` — tool design, descriptions, response shapes; the action-routed facade pattern; the CRUD combine-vs-separate matrix
- `client-compatibility.md` — which clients honor which JSON Schema features
- `error-handling.md` — turning validation failures into recovery-friendly responses
- `agentic-patterns.md` — parameter dependency chains for ordering
- `progressive-discovery.md` — when to hide tools instead of expanding their schemas
- `../decision-trees/response-format.md` — choosing between flat schema, action enum, and split tools
