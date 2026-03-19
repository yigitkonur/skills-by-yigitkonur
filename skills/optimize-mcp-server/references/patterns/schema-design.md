# Schema Design Patterns

How to design MCP tool input schemas that work reliably across models, handle type coercion gracefully, and stay simple enough for LLMs to fill correctly. These 8 patterns cover validation, naming, complexity limits, and cross-model portability.

## Pattern 1: Use `z.coerce` and `z.preprocess` for Type Safety

LLMs frequently send `"3"` instead of `3`, or `"false"` instead of `false`. Your server crashes with a Zod validation error, the LLM sees a cryptic message, and the user's request fails silently.

Fix it at the schema level.

### Coerced Number

```typescript
// Breaks when LLM sends "3"
count: z.number().describe("Number of results")

// Handles "3", 3, "3.5" gracefully
count: z.coerce.number().describe("Number of results")
```

### Coerced Boolean

The Sequential Thinking server uses this pattern to handle every boolean variant an LLM might send:

```typescript
const coercedBoolean = z.preprocess((val) => {
  if (typeof val === "boolean") return val;
  if (typeof val === "string") {
    if (val.toLowerCase() === "true") return true;
    if (val.toLowerCase() === "false") return false;
  }
  return val;
}, z.boolean());
```

Then use it in your tool schemas:

```typescript
server.tool("search", {
  query: z.string(),
  includeArchived: coercedBoolean.optional().default(false)
    .describe("Include archived results"),
}, async ({ query, includeArchived }) => {
  // includeArchived is always a real boolean here
});
```

### Why This Matters

- LLMs serialize all tool arguments as JSON — type coercion bugs are the #1 cause of silent tool failures
- `z.coerce` is zero-cost at runtime and eliminates an entire class of errors
- The alternative — sending back a validation error — wastes a round-trip and confuses the model

**Source:** `modelcontextprotocol/servers` — Sequential Thinking server; GitHub code search findings

---

## Pattern 2: Pair Regex Validation with Human-Readable Examples

When you use `.regex()` in Zod, the LLM never sees your regex pattern — it only sees the error message on failure. Make that error message a working example the model can copy.

**Bad: Opaque Regex**
```typescript
// LLM gets: "Invalid input" — no idea what format is expected
nodeId: z.string().regex(/^I?\d+[:|-]\d+/)
```

**Good: Regex + Example in Error Message**
```typescript
// LLM gets: "Node ID must be like '1234:5678' or 'I5666:180910;1:10515'"
nodeId: z.string()
  .regex(
    /^I?\d+[:|-]\d+/,
    "Node ID must be like '1234:5678' or 'I5666:180910;1:10515'"
  )
```

The Figma Context MCP server uses this exact pattern — Figma node IDs have a non-obvious format, and providing examples in error messages lets the LLM self-correct on the next attempt.

### Apply This to Any Format Constraint

```typescript
// Hex color
color: z.string()
  .regex(/^#[0-9a-fA-F]{6}$/, "Must be hex color like '#FF5733' or '#00aa99'")

// Semver
version: z.string()
  .regex(/^\d+\.\d+\.\d+$/, "Must be semver like '1.2.3' or '0.10.0'")

// Cron expression
schedule: z.string()
  .regex(/^(\S+\s){4}\S+$/, "Must be cron like '0 9 * * 1' (every Monday 9am)")
```

The error message is your teaching interface with the LLM. When validation fails, the model reads the error, adjusts, and retries. A good example in the error message means the retry almost always succeeds.

**Source:** `GLips/Figma-Context-MCP`; GitHub code search findings

---

## Pattern 3: Keep Schemas Flat, Under 6 Parameters

Schema complexity directly impacts tool-call accuracy. Community experience consistently shows flat schemas with 3-6 parameters achieve significantly higher parse success rates than nested schemas. GPT models are especially prone to "self-checking" on nested schemas — they construct a valid input, then second-guess themselves and refuse to call the tool entirely.

**Bad: Nested Object Schema**
```typescript
// Nested — LLMs struggle with this structure
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

**Good: Flat Schema**
```typescript
// Flat — same capability, much higher accuracy
server.tool("search", {
  query: z.string(),
  startDate: z.string().optional().describe("Start date (ISO 8601)"),
  endDate: z.string().optional().describe("End date (ISO 8601)"),
  status: z.enum(["active", "archived"]).optional(),
  tags: z.string().optional().describe("Comma-separated tags"),
});
```

### Rules of Thumb

1. **3-6 params** is the sweet spot — high accuracy, enough expressiveness
2. **Never nest 2+ levels** — accuracy drops significantly
3. If you need complexity, **split into multiple tools** rather than one complex schema
4. Treat `z.array()` of primitives as acceptable; `z.array(z.object())` as risky

**Source:** Community consensus from [r/mcp](https://reddit.com/r/mcp) discussions on schema complexity

---

## Pattern 4: Accept Flexible Formats, Normalize Server-Side

LLMs express the same concept in many formats. Don't force a specific one in the schema — accept a loose string and parse it yourself.

Community experience shows flexible string inputs achieve higher accuracy than union types (`anyOf`), which LLMs frequently mishandle. Union types (`z.union()`, `anyOf` in JSON Schema) are especially problematic — LLMs often pick the wrong branch or produce malformed hybrid output.

**Bad: Union Type for Dates**
```typescript
// LLMs frequently mishandle union types
date: z.union([
  z.string().datetime(),
  z.number().describe("Unix timestamp"),
  z.enum(["today", "yesterday", "last_week"]),
])
```

**Good: Flexible String, Server-Side Parsing**
```typescript
// Higher accuracy — let the LLM express naturally
date: z.string().describe(
  "Date in any format: ISO 8601, Unix timestamp, or relative ('yesterday', 'last week')"
)
```

Then normalize in your handler:

```typescript
import { parseDate } from "chrono-node"; // or your preferred parser

async function handler({ date }: { date: string }) {
  const parsed = parseDate(date) ?? new Date(date);
  if (!parsed || isNaN(parsed.getTime())) {
    return { content: [{ type: "text", text: "Could not parse date. Try ISO 8601 like '2024-01-15'." }] };
  }
  // Use `parsed` — it's always a valid Date
}
```

### Applies Beyond Dates

- **File paths / Identifiers:** Accept loose formats, resolve server-side

**Source:** Community patterns from [r/mcp](https://reddit.com/r/mcp); production experience with union type failures

---

## Pattern 5: Describe Each Enum Value Inline

Don't just list enum values — explain what each one means in the `.describe()` text. The LLM gets semantics, not just labels.

Using enums with inline descriptions significantly improves valid call rates compared to free-form strings. Adding inline descriptions of each value pushes accuracy even higher and reduces cases where the model picks the wrong value.

**Bad: Enum Without Context**
```typescript
// LLM knows the options but not when to use each
livecrawl: z.enum(["fallback", "preferred"])
```

**Good: Enum with Inline Descriptions**
```typescript
// LLM understands the semantics of each option
livecrawl: z.enum(["fallback", "preferred"]).describe(
  "Live crawl mode - 'fallback': use live crawling as backup if cached " +
  "version is unavailable, 'preferred': always prioritize live crawling " +
  "over cache (default: 'fallback')"
)
```

The Exa MCP server uses this pattern — without the inline description, LLMs defaulted to `"preferred"` (sounds better), wasting crawl budget. With the description, they correctly default to `"fallback"`.

### More Examples

```typescript
// Log level with behavior descriptions
level: z.enum(["error", "warn", "info", "debug"]).describe(
  "'error': only critical failures, 'warn': errors + potential issues, " +
  "'info': general operational events, 'debug': verbose output for troubleshooting"
)

// Output format with use-case guidance
format: z.enum(["json", "csv", "markdown"]).describe(
  "'json': structured data for programmatic use, 'csv': tabular data " +
  "for spreadsheets, 'markdown': human-readable formatted output"
)
```

**Source:** [exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server); community best practices from [r/mcp](https://reddit.com/r/mcp)

---

## Pattern 6: Break Tools Over 40 Parameters

LLMs struggle increasingly as parameter count rises. The community consensus is to keep tools under 6 parameters for best results, and to split any tool exceeding 15-20 parameters.

### Strategy 1: Split by Workflow Stage

Break one mega-tool into sequential steps:

```typescript
// One tool with 30+ params
server.tool("deploy", { env, region, scaling, healthCheck, rollback, ... })

// Three focused tools
server.tool("deploy_configure", {
  env: z.enum(["staging", "production"]),
  region: z.string(),
});
server.tool("deploy_execute", {
  configId: z.string().describe("ID from deploy_configure"),
  strategy: z.enum(["rolling", "blue-green"]),
});
server.tool("deploy_verify", {
  deploymentId: z.string().describe("ID from deploy_execute"),
});
```

### Strategy 2: Action-Routed Facade

```typescript
server.tool("database", {
  action: z.enum(["query", "insert", "schema"]),
  table: z.string(),
  where: z.string().optional().describe("Only for 'query'"),
  data: z.string().optional().describe("Only for 'insert'"),
});
```

### Rules

1. **Under 6:** ideal
2. **6-15:** acceptable if flat
3. **15-40:** split into 2-3 tools
4. **40+:** mandatory split

**Source:** [r/mcp discussion on tools with 40+ inputs](https://reddit.com/r/mcp/comments/1lv46oh/); community best practices

---

## Pattern 7: Safe Tool Name Characters Only

Use only `[a-z0-9_]` characters in tool names. Special characters, hyphens, and slashes have caused complete connection failures in production MCP clients — not validation errors, but silent crashes.

### The Bug

Several MCP clients (including early versions of Claude Desktop) crash the entire connection when tool names contain characters outside `[a-zA-Z0-9_]`. The slash character (`/`) is particularly dangerous because some clients try to parse tool names as URI path segments.

Confirmed breaking characters from community reports:
- `/` — crashes Claude Desktop connection silently
- `-` — breaks some tool-router middleware
- `.` — causes issues in OpenAI function-calling adapters
- Spaces — universally rejected, but error messages vary
- Unicode — works in some clients, silent failure in others

### Naming Convention

```typescript
// DANGEROUS — will crash some clients
const badNames = [
  "read/file",
  "git-status",
  "search.files",
  "get_user's_data",
];

// SAFE — [a-z0-9_] only, underscore_separated
const goodNames = [
  "read_file",
  "git_status",
  "search_files",
  "get_user_data",
];
```

### Lint Rule (TypeScript)

```typescript
const SAFE_TOOL_NAME = /^[a-z][a-z0-9_]{0,63}$/;

function registerTool(name: string, ...rest: any[]) {
  if (!SAFE_TOOL_NAME.test(name)) {
    throw new Error(
      `Invalid tool name "${name}". Use only lowercase letters, digits, and underscores. ` +
      `Must start with a letter. Max 64 characters.`
    );
  }
  server.tool(name, ...rest);
}
```

Add this check to CI to catch violations before deployment — a broken tool name can take down an entire MCP connection, not just the single tool.

**Source:** [anthropics/claude-code#2257](https://github.com/anthropics/claude-code/issues/2257) (tool name validation); [modelcontextprotocol/typescript-sdk#1512](https://github.com/modelcontextprotocol/typescript-sdk/issues/1512) (SEP-986 tool name spec); community reports from [r/mcp](https://reddit.com/r/mcp)

---

## Pattern 8: Cross-Model Portable Schema Rules

If your MCP server is accessed by multiple LLM clients (Claude, GPT-4, Gemini), design your input schemas to work across all of them. Each model has different JSON Schema support, and schemas that work perfectly in Claude can fail silently in GPT or cause Gemini to ignore the tool.

### Compatibility Rules (7 Hard Rules)

```typescript
// Rule 1: No oneOf / anyOf / allOf — Gemini ignores tools with these
// Bad
{ oneOf: [{ type: "string" }, { type: "number" }] }
// Good — pick the most permissive type, coerce server-side
{ type: "string", description: "Can also be a number (will be converted)" }

// Rule 2: Max 3 levels of nesting — GPT-4 degrades beyond this

// Rule 3: No $ref — most clients don't resolve references in tool schemas
// Inline all definitions

// Rule 4: No format validators beyond date-time and email — inconsistently supported
// Bad: { type: "string", format: "uri" }  — GPT-4 ignores format
// Good: describe the format in the description field instead

// Rule 5: No default for required fields — confuses some model implementations
// Only apply defaults to optional fields

// Rule 6: Keep enums under 10 values — larger enums reduce model accuracy
// Split large enums into a separate "mode" tool that narrows the scope

// Rule 7: Use additionalProperties: false — helps all models understand the schema is strict
```

### Compatibility Matrix

| Feature | Claude | GPT-4o | Gemini |
|---|---|---|---|
| `oneOf`/`anyOf` | Supported | Supported | Ignored |
| `$ref` references | Supported | Varies | Ignored |
| `format` constraints | Supported | Ignored | Ignored |
| 5+ levels nesting | Supported | Degraded | Breaks |
| Enum > 20 values | Supported | Degraded | Degraded |
| `additionalProperties: false` | Supported | Supported | Supported |

### Test Your Schema

```typescript
// Quick cross-model schema validator
function validatePortability(schema: JsonSchema): string[] {
  const issues: string[] = [];
  if (schema.oneOf || schema.anyOf) issues.push("Remove oneOf/anyOf for Gemini compatibility");
  if (schema.$ref) issues.push("Inline $ref for cross-client compatibility");
  if (countNestingDepth(schema) > 3) issues.push("Nesting too deep (>3) for GPT-4 reliability");
  if (Array.isArray(schema.enum) && schema.enum.length > 10) issues.push("Large enum (>10) degrades accuracy");
  return issues;
}
```

A schema that crashes Gemini silently drops the tool from that client's context. Cross-model portability rules let you build once and deploy everywhere.

**Source:** [Gemini function calling docs](https://ai.google.dev/gemini-api/docs/function-calling); [OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling); community cross-model testing from [r/mcp](https://reddit.com/r/mcp)
