# Tool Anti-Patterns

*Read this when reviewing your tools for common pitfalls.*

Vendor guardrails and patterns to avoid when designing and implementing tools.

## Schema design

| Don't | Do | Why |
|---|---|---|
| `z.any()` or `z.unknown()` | Specific Zod type with `.describe()` | Defeats validation. Model gets no signal for what to send. |
| Untyped `Record` | `z.record(z.string(), z.string())` with explicit value type | Untyped records hallucinate values. |
| Schema without `.strict()` | `z.object({...}).strict()` on top level | LLMs hallucinate extra fields; make them explicit validation errors. |
| Field without `.describe()` | `.describe(...)` on every field | The description is the model's only signal for what to put there. |
| Deep nesting (>3 levels) | Flatten or split into multiple tools | LLMs handle flat schemas more reliably. |
| More than 6 parameters | Split into focused sibling tools | Schema gets too complex for the model to fill correctly. |

## Description and naming

| Don't | Do | Why |
|---|---|---|
| `description: "Gets data"` | `description: "Look up a user by ID or email. Returns profile..."` | Vague descriptions cause wrong tool selection. |
| Generic name: `process`, `handle`, `data` | Action-verb + noun: `search-users`, `create-ticket` | Names guide tool selection. Generic names collide. |
| Catch-all tool with `mode` parameter | One tool per action | Mode dispatch hides actual capabilities from the model. |
| camelCase or snake_case names | kebab-case names | MCP convention; consistency across the registry. |

## Annotations

| Don't | Do | Why |
|---|---|---|
| Omit `annotations` on read tools | `readOnlyHint: true` on every read/search/get | Clients can skip confirmation dialogs. |
| Omit `destructiveHint` on delete tools | `destructiveHint: true` on every delete/remove | Clients warn the user before invoking. |
| `requiresAuth`, `rateLimit`, `deprecated` | Express in description; enforce in handler | These are not part of MCP `ToolAnnotations` — they will be ignored. |
| Lie about `readOnlyHint` to skip confirmation | Set it accurately | Trust violation; users will hit destructive tools without warning. |

## Handler behavior

| Don't | Do | Why |
|---|---|---|
| Side-effects in `readOnlyHint: true` tools | Make read tools actually read-only | Annotation contract; clients trust it. |
| `throw "Failed"` (string) | Return `{ isError: true, content: [...] }` | Strings aren't `Error` objects; loses stack traces and breaks client error handling. |
| Throw on expected failures (not-found, validation) | Return `{ isError: true, content: [...] }` | Throws become transport/server errors; raw error envelopes report a graceful tool failure. |
| Swallow errors silently | Log with `ctx.sendLog("error", …)` and return an error envelope | Hidden failures look like successful no-ops. |
| Return raw API responses | Return curated `content` and, when schema'd, `structuredContent` | Bloats context; the model wades through irrelevant nesting. |

## Output shape

| Don't | Do | Why |
|---|---|---|
| `structuredContent` contains only metadata | Mirror essential answer into `structuredContent` | Structured-first clients surface "success" with no answer body. |
| Structured-only response (no `content`) | Add readable `content` with the same essential facts | Content-first adapters drop `structuredContent` and lose the answer. |
| `text(JSON.stringify(obj))` | Return `content` text block and `structuredContent` | Makes downstream parsing fragile; loses MIME and structured surface. |
| Serialize binary as `text(base64)` | Use binary MIME types or explicit content blocks | Wrong MIME; clients can't render. |
| Build `CallToolResult` by hand | Return standard envelope `{ content, structuredContent?, isError? }` | Keep envelopes explicit and standard. |
| Import SDK types from wrong path | Import from `mcp-use` or `@modelcontextprotocol/server` | Wrong package; mcp-use exports current SDK types. |

## Composition

| Don't | Do | Why |
|---|---|---|
| `mix()` with one argument | Return the raw envelope directly | Pointless wrapper. |
| Repeat the same payload across multiple content parts | One readable surface, one structured surface | Duplicated information confuses adapters. |
| Cram secrets into `structuredContent` | Put private/UI-only data in `_meta` | Some hosts surface `structuredContent` to the model and the transcript. |

## Logging and progress

| Don't | Do | Why |
|---|---|---|
| `console.log()` in handler | `await ctx.sendLog("info", …)` | `console.log` doesn't reach the client; ctx.sendLog does. |
| Log raw user input verbatim | Log redacted/summarized info | Logs are model-visible; secrets leak into transcripts. |
| No progress for long-running tools | `await ctx.reportProgress(loaded, total, msg)` | Without progress, clients can't show feedback or cancel. |
