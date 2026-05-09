# output-contracts — outputs an agent can parse and reason about

Cross-surface principles for tool output. The agent reads every response; what's in the response either advances the task or burns context budget. Schema-version it, name fields stably, project to agent-relevant fields, and never dump raw API payloads. Source: `optimize-agentic-cli/references/output-contracts.md` (cross-surface principles) and `optimize-agentic-mcp/patterns/tool-responses.md`.

## Universal principles

### Schema versioning is mandatory for long-lived tools

Every long-lived tool returns a `schema_version` field at the envelope's top level. Agents that have learned the v1 shape need a way to detect v2 and switch parsing.

```json
{ "ok": true, "result": { ... }, "schema_version": "1" }
```

Versioning rules:

- **Stable field names within a version.** Don't rename `customer_id` to `userId` mid-version.
- **Additive changes are non-breaking.** New optional fields can be added without bumping the version.
- **Removing or renaming fields requires a major bump.** Bump from `"1"` to `"2"`; never silently change.
- **Document the version explicitly** in the tool description and in `--help`.
- **Never reuse a version number** for an incompatible shape. Once `"1"` ships, that schema is `"1"` forever.

For ephemeral or experimental tools, omit the field — but state in the description that the shape is unstable.

### Stable field names

The agent learns names. Renaming them forces re-learning. Cardinal sins:

- Renaming `id` to `uuid` (or vice versa) between versions.
- Renaming `created_at` to `createdAt` because a new code reviewer prefers camelCase.
- Renaming `error.message` to `error.detail` because the upstream API changed.

Pick a casing convention and hold it. Most tools use `snake_case` (matches MCP exemplar consensus, matches most CLI ecosystems). Atlassian Rovo ships `camelCase` — coherent within the server but harder to interop. Pick one; be ruthless about consistency within the tool.

### Forward compatibility: additive only

New fields are additive. Old fields stay. Old fields can be deprecated (mark them in the description) but must keep returning correct data within the same major version.

```json
{
  "ok": true,
  "result": {
    "id": "ord_123",          // stable since v1
    "status": "shipped",       // stable since v1
    "ship_date": "2026-05-08", // added in v1.1 (additive, non-breaking)
    "tracking_url": "..."      // deprecated in v1.2; will remain through v1.x; removed in v2
  },
  "schema_version": "1.2"
}
```

### Project to agent-relevant fields — don't dump raw API noise

The agent's context window is finite. Every byte that isn't directly useful is byte that crowds out the next thought. Raw API JSON typically includes timestamps, auth metadata, tracking IDs, and pagination plumbing the agent doesn't need.

Bad — Linear's `list_users` returning `createdAt`, `updatedAt`, `avatarUrl`, `isAdmin`, `isGuest` when the agent only wants assignment IDs (source: `optimize-agentic-mcp/patterns/exemplar-servers.md` Avoid #4):

```json
{
  "users": [
    {
      "id": "usr_a",
      "name": "Alice",
      "email": "alice@co.com",
      "avatarUrl": "https://...",
      "createdAt": "2024-...",
      "updatedAt": "2025-...",
      "isAdmin": false,
      "isGuest": false,
      "timezone": "America/New_York",
      "...": "..."
    }
  ]
}
```

Good — projected to the fields agents actually use:

```json
{
  "users": [
    { "id": "usr_a", "name": "Alice", "email": "alice@co.com" }
  ]
}
```

Decide what the agent will do with each field. If the answer is "nothing", drop it. The CLI / MCP author owns the projection — don't make every agent re-engineer it.

### Distinguish data-the-agent-acts-on from progress-noise

Two channels, every time:

- **Data channel** — the result the agent will reason about. Stable shape. Versioned. Projected.
- **Progress channel** — what the agent doesn't need to remember after the call returns.

```
CLI:    stdout  =  data channel
        stderr  =  progress channel
        exit    =  classification

MCP:    result.content (or structuredContent) = data channel
        progress notifications                 = progress channel (advanced protocol)
        isError                                = classification
```

Mixing them is a classic agent footgun. The model parses the data channel; if progress noise is in there, parse fails and the tool gets abandoned.

### Token budget discipline

Cap response sizes proactively. Heuristics for typical envelopes (see also `agent-cognitive-load.md`):

| Tool category | Target response size | Strategy if larger |
|---|---|---|
| Scan / list | < 500 tokens | Pagination with `has_more` and cursor; first-page-plus-summary. |
| Fetch / describe | 500 — 3,000 tokens | Project to relevant fields; offer a `?fields=` selector if larger detail is sometimes needed. |
| Operate (create / update / delete) | < 500 tokens | Status + `next_action`; not the full record (ask for it via fetch if needed). |
| Iterate (multi-phase workflow) | < 1,500 tokens per phase | Validation errors + progress + `next_action`; full state via separate `status` call. |

If a tool routinely returns > 5,000 tokens, the response is probably wrong shape. Look at `agent-cognitive-load.md` for paginate / truncate / project options.

## Surface mappings

### CLI — JSON envelope on stdout

The canonical CLI envelope:

```json
{
  "ok": true,
  "command": "deploy apply",
  "schema_version": "1",
  "result": {
    "id": "deploy_123",
    "status": "succeeded",
    "resources_created": 3
  },
  "meta": {
    "truncated": false,
    "total_count": 3,
    "duration_ms": 1234
  }
}
```

| Field | Type | Description |
|---|---|---|
| `ok` | boolean | `true` for success, `false` for error. The first thing the agent checks. |
| `command` | string | The command that was executed (debugging aid). |
| `schema_version` | string | Output schema version. Required for long-lived tools. |
| `result` | object / array | The actual operation result. Type varies by command. |
| `meta` | object | Pagination, timing, request ID, truncation flag. Optional but useful. |

Error envelope (`ok: false`):

```json
{
  "ok": false,
  "schema_version": "1",
  "error": {
    "class": "conflict",
    "code": "RESOURCE_EXISTS",
    "message": "Resource 'foo' already exists",
    "retryable": false,
    "suggestion": "Use --force to overwrite or pick a different name",
    "details": { "existing_id": "res_abc123" }
  }
}
```

See `error-strategy.md` for the error class taxonomy.

**Streaming variant** — use JSONL (newline-delimited JSON) when operations are long-running:

```jsonl
{"type":"progress","phase":"downloading","percent":25,"timestamp":"2026-05-08T10:00:00Z"}
{"type":"progress","phase":"downloading","percent":50}
{"type":"phase","phase":"downloading","status":"completed","duration_ms":5000}
{"type":"phase","phase":"installing","status":"started"}
{"type":"completed","status":"succeeded","result":{"id":"build_123"}}
```

Required fields per event: `type` (one of `progress`, `phase`, `log`, `completed`, `error`, `heartbeat`), and a UTC ISO 8601 `timestamp`. Flush after each line — unbuffered output is mandatory for real-time consumption. Heartbeat every 30s for ops over a minute. See `../cli/output-envelope.md` for the canonical CLI envelope deep dive.

**Pagination envelope:**

```json
{
  "ok": true,
  "result": [{"id":"r_001"},{"id":"r_002"}],
  "pagination": {
    "total": 150,
    "page": 1,
    "per_page": 20,
    "has_more": true,
    "next_cursor": "eyJpZCI6MTIzfQ=="
  },
  "schema_version": "1"
}
```

`has_more` is required when paginating. Total count is optional (often expensive to compute).

**Quiet-mode variant** — `--quiet` produces bare values for pipeline use:

```bash
$ myco list resources --quiet
res_001
res_002
res_003

$ myco create resource --name foo --quiet
res_004
```

Quiet mode is for shell pipelines. Don't use it for agent integration; use `--json`.

### MCP — content blocks and structured content

MCP tool responses use the result shape:

```json
{
  "content": [
    { "type": "text", "text": "..." }
  ],
  "structuredContent": { ... },
  "isError": false
}
```

Three patterns:

1. **Text-only** — JSON-stringified into `content[0].text`. Common (Linear, Stripe, GitHub) but loses structured-content benefits. Spec discourages but ecosystem mixed.
2. **`structuredContent`** — typed JSON in a dedicated field; clients that respect the spec parse it as structured data. Pair with text fallback for clients that don't.
3. **Mixed** — both text (human-readable summary) and `structuredContent` (machine-parseable). Recommended; works for all clients.

Recommended:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Created issue #143: Fix login bug. URL: https://co.com/issues/143"
    }
  ],
  "structuredContent": {
    "issue_id": "143",
    "url": "https://co.com/issues/143",
    "schema_version": "1"
  }
}
```

The text is the human-readable summary the agent shows the user. The structured content is what the next tool call consumes. Both are valid; ship both.

**`isError: true`** — for business-logic failures (validation, conflict, not-found). Reserve protocol-level JSON-RPC errors for actual transport failures. See `error-strategy.md` for the rationale.

**Output schemas** — declare `outputSchema` alongside `inputSchema`. Helps clients reason about return shape and helps the model plan downstream calls. Supabase declares both on every tool (source: `optimize-agentic-mcp/patterns/exemplar-servers.md` Copy #1).

```typescript
server.tool("get_order", {
  description: "Fetch an order by ID. Returns id, status, customer, line_items.",
  inputSchema: z.object({ order_id: z.string() }),
  outputSchema: z.object({
    order_id: z.string(),
    status: z.enum(["pending", "shipped", "delivered", "cancelled"]),
    customer_id: z.string(),
    line_items: z.array(z.object({
      sku: z.string(),
      qty: z.number(),
    })),
    schema_version: z.literal("1"),
  }),
}, async ({ order_id }) => { /* ... */ });
```

**Disagreement to know about.** Supabase explicitly opts out of `structuredContent` (their README: "this server does not send `structuredContent`; Vercel AI SDK parses JSON from content text"). Linear ships JSON-in-text with no structured content. Recommendation: send both — structured content + text summary — to maximize client compatibility while honoring the spec direction.

## Cross-cutting choices

### When to project a subset vs. return full payload

Project to a subset when:
- The agent rarely needs the full payload.
- The full payload is > 3,000 tokens.
- The full payload contains data the agent shouldn't consume (PII, secrets, audit metadata).

Return full payload when:
- Tool is a `describe` / `inspect` operation; the user explicitly asked for everything.
- The full payload is < 1,000 tokens.
- A separate `--fields` selector or `?fields=` query param lets the agent narrow when needed.

Always offer a way to narrow even when defaults are full:

```bash
myco get order ord_123 --json --fields id,status,total
```

```typescript
server.tool("get_order", {
  inputSchema: z.object({
    order_id: z.string(),
    fields: z.array(z.string()).optional().describe("Subset of fields to return; defaults to all."),
  }),
  // ...
});
```

### When to paginate vs. return all at once

Paginate when:
- Result set can be > 100 items.
- Total result size can be > 2,000 tokens.
- The agent is likely to want only the first page in most cases.

Return all when:
- Result set is bounded (e.g., listing the user's 5 most recent orders).
- Total fits within the budget for the tool category.
- Forcing the agent to paginate would add round trips for no benefit.

When paginating, always include `has_more`. Optionally include a sample / first-page summary even when the set is large:

```json
{
  "ok": true,
  "result": {
    "total": 1247,
    "sample": [{"id":"r_001"}, {"id":"r_002"}, {"id":"r_003"}, {"id":"r_004"}, {"id":"r_005"}],
    "has_more": true,
    "next_cursor": "eyJpZCI6NX0="
  },
  "schema_version": "1"
}
```

### Truncation with signal

When a single field is too large, truncate and tell the agent so:

```json
{
  "ok": true,
  "result": {
    "log_excerpt": "...first 8000 chars...",
    "truncated": true,
    "truncation_note": "Showing first 8000 of 47000 chars. Call get_log_full(id) for the entire log."
  },
  "schema_version": "1"
}
```

Silent truncation is worse than not truncating — the agent acts on incomplete data without knowing it.

## Tiered verbosity (response shrinks as context fills)

Optional but high-leverage: vary response size by remaining context budget. Three tiers:

| Remaining context | Tier | Response shape |
|---|---|---|
| > 70% | Full | Complete records, all fields, pagination metadata. |
| 40 — 70% | Summary | Count + top 5 + `detail_available: true` hint. |
| < 40% | Minimal | Count only + `Narrow your query or call get_details(id) for a specific record.` |

Source: `optimize-agentic-mcp/patterns/context-engineering.md` Pattern 3. Tiered verbosity gives the model a graceful off-ramp on long sessions; a tool that returns 10,000 rows at turn 40 silently degrades model performance.

## Anti-patterns to refuse

**Mixing prose and JSON on the same channel.** `console.log("Done!"); console.log(JSON.stringify(result));` writes both lines to stdout. The agent's parser fails on the first line.

**Renaming fields between releases.** Stable field names are the contract. Renames break every agent that has learned the old name. If you must rename, bump the major version.

**Returning raw API JSON.** Notion's own post-mortem on v1: "1:1 API-to-tool mapping produced poor agent experiences, including high token use from hierarchical JSON block data." Project to fields the agent will actually use.

**Pagination without `has_more`.** Agents have no way to know if there's more without it. Always include the flag.

**Silent truncation.** Truncating a long field without a `truncated: true` signal tells the agent it has the whole answer when it doesn't.

**Schema version omission on long-lived tools.** Without it, the only way to detect a breaking change is when calls start failing.

**Deeply nested response shape.** If `result.items[0].metadata.shipping.address.line1` requires four hops to reach, the agent burns tokens on every traversal. Flatten or project.

**Shipping more output formats than necessary.** YAML + JSON + TSV + Markdown for the same data forces the agent to learn three contracts. Pick one default; offer one variant if there's a real reason.

## Cross-references

- For error-shape design specifically, read `error-strategy.md`.
- For surface-specific envelope details, read `../cli/output-envelope.md` (CLI) and `../mcp/patterns/tools.md` (MCP).
- For multi-phase iterative outputs, read `iterative-loops.md`.
- For token-budget framing across sessions, read `agent-cognitive-load.md`.
- For exemplars that get response shape right vs. wrong, read `exemplars.md`.
