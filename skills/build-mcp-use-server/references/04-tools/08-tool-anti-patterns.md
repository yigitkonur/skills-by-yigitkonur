# Tool Anti-Patterns

Tight catalog of what not to do. Each entry is a do-X-not-Y rule with the underlying reason.

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
| `throw "Failed"` (string) | `return error("Operation failed: …")` | Strings aren't `Error` objects; loses stack traces and breaks client error handling. |
| Throw on expected failures (not-found, validation) | `return error("…")` | Throws become 500s; `error()` returns a graceful tool failure. |
| Swallow errors silently | Log with `ctx.log("error", …)` and `return error(…)` | Hidden failures look like successful no-ops. |
| Return raw API responses | `object({ … })` with curated fields | Bloats context; the model wades through irrelevant nesting. |

## Output shape

| Don't | Do | Why |
|---|---|---|
| `structuredContent` contains only metadata | Mirror essential answer into `structuredContent` | Structured-first clients surface "success" with no answer body. See `05-responses/08-content-vs-structured-content.md`. |
| Structured-only response (no `content`) | Add readable `content` with the same essential facts | Content-first adapters drop `structuredContent` and lose the answer. |
| `text(JSON.stringify(obj))` | `object(obj)` | Makes downstream parsing fragile; loses MIME and structured surface. |
| Serialize binary as `text(base64)` | `binary(base64, mime)` or `image()` / `audio()` | Wrong MIME; clients can't render. |
| Build `CallToolResult` by hand | Use response helpers (`text`, `object`, `mix`, `error`) | Easy to miss `_meta.mimeType` or `isError`. |
| Import helpers from `@modelcontextprotocol/sdk` | `import { … } from "mcp-use/server"` | Wrong package; mcp-use helpers are different. |

## Composition

| Don't | Do | Why |
|---|---|---|
| `mix()` with one argument | Return the helper directly | Pointless wrapper. |
| Repeat the same payload across multiple `mix()` parts | One readable surface, one structured surface | Duplicated information confuses adapters. |
| Cram secrets into `structuredContent` | Put private/UI-only data in `_meta` | Some hosts surface `structuredContent` to the model and the transcript. |

## Logging and progress

| Don't | Do | Why |
|---|---|---|
| `console.log()` in handler | `await ctx.log("info", …)` | `console.log` doesn't reach the client; ctx.log does. |
| Log raw user input verbatim | Log redacted/summarized info | Logs are model-visible; secrets leak into transcripts. |
| No progress for long-running tools | `ctx.reportProgress?.(loaded, total, msg)` | Without progress, clients can't show feedback or cancel. |
