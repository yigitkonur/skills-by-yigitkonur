# Decision tree — response format

Pick text, structured content, mixed, or a paginated/Resource path. The shape of a tool's response determines token cost, agent comprehension, and what the next tool can do with the output. Wrong shape burns context budget.

## Decision branches

```
START: Who consumes the result and what shape is the data?
|
+-- The agent will act on the data (call another tool, branch, decide)
|   --> structured (declare outputSchema; return structuredContent + text)
|   --> ../patterns/tools.md (response-shape section)
|
+-- The user reads prose; the agent only narrates
|   --> text content; keep it short, project to relevant fields
|   --> ../patterns/tools.md
|
+-- Both an agent and a user read the response
|   --> mixed: text content for narrative, structuredContent for data
|   --> use `audience: ["user","assistant"]` annotations to label intent
|   --> ../patterns/tools.md, ../patterns/resources-and-prompts.md
|
+-- The result is a large dataset (rows, pages, files)
|   +-- < 100 items   --> return all, no pagination
|   +-- 100-5000 items --> paginate with first-page-plus-summary
|   +-- 5000+ items   --> truncate with signal + Resource exposure
|   --> ../patterns/resources-and-prompts.md
|
+-- The result includes rich media (images, audio, files)
    --> embed only when the agent needs to see/hear it; otherwise expose as Resource
    --> ../patterns/advanced-protocol.md, ../patterns/resources-and-prompts.md
```

## Schema-content vs result-content

MCP carries two distinct shapes in a tool result:

- **Result content** — what the LLM reads. Either text content or `structuredContent` (a JSON-shaped object). Always include text content for backward compatibility, even when `structuredContent` is set.
- **Output schema (`outputSchema`)** — declared on the tool definition. Tells the agent (and SDK) the exact shape `structuredContent` will follow. Agents lean on `outputSchema` to chain tool calls; without it, they fall back to brittle string parsing.

Use `structuredContent` when the next tool will consume this tool's output. Use text content when the user or the LLM narrates over the result. Use both — with the same data, formatted differently — when the audience is mixed.

## Format choice for tabular and structured data

| Data shape | Default | Why |
|---|---|---|
| Rows + flat columns | TSV | 30–40% fewer tokens than JSON; no quotes/braces noise |
| Rows + nested cells | YAML or JSON | TSV cannot represent nesting cleanly |
| Hierarchical objects, agent-internal | YAML | ~30% fewer tokens than JSON; LLMs read both equally |
| Hierarchical objects, piped to next tool | JSON | Programmatic interop wins over token savings |
| Schema-guaranteed payload | `structuredContent` + `outputSchema` | SDK validates at runtime; agent knows shape pre-call |

Offer `response_format` enums (e.g., `yaml | json | tsv`) on tools where the agent's downstream use varies — make the tradeoff explicit instead of guessing for the user.

## Detail levels — concise vs detailed

When a tool serves both browse-style and act-style calls, add a `response_format: concise | detailed` enum.

- `concise` (default) — about 70 tokens per item. Enough to scan, search, route.
- `detailed` — about 200 tokens per item. IDs, metadata, foreign keys for follow-up calls.

Empirically about 65% token reduction when `concise` is the default and the agent opts into `detailed` only when it needs to chain.

## Pagination

Past 100 items, paginate. Two-fold rule:

1. Return page 1 with `total_results`, `page_size`, `has_more`, and `next_cursor`.
2. Return a one-line summary string: *"showing 50 of 1240 results; call again with `cursor='...'` for the next page or narrow `query`."*

This lets the agent decide in one turn whether page 2 is worth the call. Without it, agents either always-fetch or never-fetch — both wrong.

Past 5000 items, hard-cap with a truncation signal:

```
[...truncated — 4,512 chars omitted; narrow query or paginate.]
```

## Audience annotations

When the response serves the user **and** the agent (e.g., human-readable narrative + structured data the agent will consume), annotate:

```
content: [
  { type: "text", text: "Refunded $24.00 to card ending 4242.",
    annotations: { audience: ["user","assistant"], priority: 1.0 } },
  { type: "text", text: "<diagnostic dump>",
    annotations: { audience: ["assistant"], priority: 0.3 } }
]
```

The model sees everything. The user sees only `audience: ["user", ...]` items. Use this when debug or telemetry helps the model recover but should not surface to the user.

## When to embed images, audio, files

MCP supports embedded image/audio/file content, but embedding adds complexity and token cost. Default to **expose as Resource**; embed only when:

- The agent must analyze the media (vision tasks, audio classification).
- The image is a chart or diagram the agent will reason over.
- The artifact is small and the workflow is one-shot.

Otherwise return a Resource URI — `file://...`, `https://...`, or a server-hosted resource — and let the agent fetch only if needed. Background: `../patterns/resources-and-prompts.md`.

## Worked examples

### Example 1 — `list_pull_requests` (browsing)

Default `response_format: concise`:

```
TSV with columns: id, title, author, state, updated_at
```

Detailed:

```
JSON with full author info, branch refs, mergeable_state, requested_reviewers
```

Pagination after 25 PRs.

### Example 2 — `create_invoice` (act-on-result)

`structuredContent` with `outputSchema`:

```
{ "invoice_id": "in_...", "amount_cents": 2400, "status": "open" }
```

Plus text content: `"Created invoice in_... for $24.00 (status: open)."`

The agent reads the text to narrate to the user; the next tool reads `structuredContent.invoice_id` to chain.

### Example 3 — `query_logs` (variable size)

```
{
  "structuredContent": {
    "matches": [...],            // first 50
    "total_matches": 1240,
    "has_more": true,
    "next_cursor": "..."
  },
  "content": [
    { "type": "text", "text": "50 of 1240 matches; call again with cursor=... or narrow window." }
  ]
}
```

## Anti-patterns

- **Returning raw API JSON.** The agent loses budget on noise; the tool feels untrustworthy.
- **Guessing on detail level.** Don't pre-pick `concise` or `detailed` — expose the enum and document the tradeoff.
- **Over-using `structuredContent`.** When the agent doesn't need to chain, structured-only payloads are harder for the LLM to narrate; include text.
- **Forgetting `outputSchema`.** Without it, downstream tools and SDKs cannot validate; chaining becomes brittle.
- **Embedding large media.** Resource exposure costs ~zero tokens; embedding burns the budget for every call.
- **Skipping pagination on unbounded queries.** A single 5000-row return blows past every model's window.

## When to re-evaluate

- Token cost per session climbs — switch responses from JSON to YAML / TSV.
- Agents request page 2 on >50% of calls — increase default page size.
- Agents never request `detailed` — drop the enum; `concise` becomes the only shape.
- Downstream tools start consuming the response — declare `outputSchema` and switch to `structuredContent`.
- Users complain about noise — add audience annotations.

## Cross-references

- Tool response patterns and shape: `../patterns/tools.md`.
- Resources and prompts (large datasets, templated workflows): `../patterns/resources-and-prompts.md`.
- Output contracts cross-surface: `../../common/output-contracts.md`.
- Schema design (input shape for follow-up tools): `../patterns/schema-design.md`.
