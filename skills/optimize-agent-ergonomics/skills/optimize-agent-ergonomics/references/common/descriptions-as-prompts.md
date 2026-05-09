# descriptions-as-prompts — names and descriptions ARE the prompt

Tool descriptions are prompt engineering, not documentation. The model reads the description at decision time — `tools/list` for MCP, `--help` for CLI — and decides whether and how to call your tool. Write for the model, not for a human reading docs once. Source: primarily `optimize-agentic-mcp/patterns/tool-descriptions.md` (11 patterns), generalized to cover CLI.

## What the model reads, and when

| Surface | What the model reads | When it reads it |
|---|---|---|
| MCP | Tool `name`, `description`, parameter `description` fields, optional `instructions` field | At every `tools/list` call (typically once per session, sometimes more). Full schema is in context for every message. |
| CLI | The first line of `--help`; per-flag `--help` blocks; the synopsis line; environment-variable docs | When the agent runs `<cmd> --help` to discover what to do. Output becomes part of the agent's context until cleared. |

Both surfaces share the same property: the description is the only signal the model has when deciding *whether* to call the tool. The schema (what's valid) and the description (what's wise) play complementary roles — schema enforces structure; description tells the model what happens when each option is picked.

## Universal principles

### Lead with intent, not API shape

The first 5 words decide whether the model selects the tool. Lead with **verb + resource + key scope**, then stop the headline. Save the explanation for the body.

Bad: "This tool provides the ability to search through the customer database using various criteria including but not limited to..."
Good: "Search customers by name, email, or account ID. Returns top 20 matches with account status."

The bad form burns 50 tokens before the model learns what the tool does. The good form earns the selection in 15.

### Include 1-2 inline examples

Models learn calling conventions from examples faster than from prose. One happy-path example and one common-mistake example handle the long tail without bloating the description.

```json
{
  "description": "Search orders by customer, date range, or status. Max 50 results.\n\nExample: {\"customer_id\": \"cust_123\", \"after\": \"2024-01-01\"}\nDates must be ISO 8601 (YYYY-MM-DD). Natural-language dates fail."
}
```

CLI equivalent (in `--help`):

```
search-orders — search orders by customer, date range, or status

EXAMPLE
  myco search-orders --customer cust_123 --after 2024-01-01 --json

COMMON MISTAKE
  --after "Jan 1 2024"   # fails: dates must be ISO 8601 (YYYY-MM-DD)
```

### State side effects explicitly

If the tool writes, deletes, sends a message, or changes state in a way that's not reversible, say so in the description. The schema can't carry this signal; the description must.

Good: "Send the invoice to the customer's email. **Side effect: not reversible.** Use `preview-invoice` to see the rendered version first."
Bad: "Send the invoice." (model has no way to know whether this is destructive)

### Be concrete about parameter shapes

Avoid `string` / `number` without context. Say what kind of string, what unit of number.

```json
{
  "deadline": {
    "type": "string",
    "description": "ISO 8601 date or datetime, UTC. Example: '2026-12-01' or '2026-12-01T15:30:00Z'."
  },
  "timeout_ms": {
    "type": "integer",
    "description": "Request timeout in milliseconds. Range: 100-30000. Default: 5000.",
    "minimum": 100,
    "maximum": 30000
  }
}
```

Type plus enum plus inline description plus example — the model has nothing to guess. CLI equivalent: per-flag `--help` blocks with the same content.

### Avoid over-narrowing language

Phrases like "only use this for X" make the model unsure whether the current case fits. The model errs toward not calling the tool, and the agent ends up reasoning in chat instead.

Bad: "Only use this tool when the user explicitly asks to delete a record."
Better: "Delete a record by ID. The agent should confirm with the user before calling for any production environment."

The first form encodes a behavior policy that's better expressed as a schema gate (a `confirm: true` parameter) or a server-side approval flow than as language the model has to interpret.

### Avoid hedging

"May be useful for..." or "Sometimes used to..." make the model uncertain. The model needs a verb sentence — what the tool *does*, not what it *might* do.

Bad: "This tool may be useful for searching customers when you have specific criteria."
Good: "Search customers by name, email, or account ID."

### Tell the model when NOT to use a tool

Positive descriptions are necessary but insufficient when multiple tools have overlapping scope. Add explicit negative routing.

```
get_customer:    "Fetch a single customer by ID. Returns full profile.
                  Do NOT use for searching — use search_customers."

search_customers:"Search customers by name or email. Top 20 matches.
                  Do NOT use for bulk export; use export_customers for >100 rows."

export_customers:"Export all customers matching a filter as CSV. Async — returns a job ID.
                  Do NOT use for single lookups; use get_customer instead."
```

Without exclusionary hints, models default to the "biggest" tool — the one that could technically handle every case. Real-world example: Figma's MCP server uses `"Do NOT use unless explicitly requested by the user"` on its `depth` parameter to prevent agents from making expensive deep-tree calls by default. Source: `optimize-agentic-mcp/patterns/tool-descriptions.md` Pattern 7.

### Use exact, namespaced names

For MCP tools across multiple servers, namespace with a prefix to avoid collisions. For CLI, use a verb + object name that doesn't collide with system commands.

```
asana_search_tasks       jira_search_issues       github_create_pr
```

Picking `search`, `create`, `update` as bare names guarantees collisions the moment a second tool joins. Bare names also force the model to rely entirely on description text to disambiguate, which fails under context pressure.

## Surface mappings

### MCP — where descriptions live

| Field | Read by | Best practice |
|---|---|---|
| Tool `name` | `tools/list` | `snake_case` (community convention; 14 of 16 exemplars). Verb + resource. Namespaced. |
| Tool `description` | `tools/list`, system prompt, every message | Verb + resource + key scope first. ≤200 tokens. Side effects explicit. 1-2 examples. |
| Parameter `description` | When the model is filling args | Type + unit + range + example. Reference other tools when values come from them. |
| Server `instructions` (init) | Once per session, system-level | Capabilities map, recommended workflows, important constraints. Like a `skills.md` for the server. |
| Response schemas (`outputSchema`) | When the model is parsing return values | Declare them; helps clients and structured-content consumers. |

The `instructions` field is the most reliable place to surface server-wide guidance — major MCP clients (Claude Desktop, Cursor, VS Code) honor it; the spec's `prompts` feature is silently dropped by many clients.

### CLI — where descriptions live

| Surface | Read by | Best practice |
|---|---|---|
| `<cmd> --help` first line | First thing the agent reads | Verb + object + key scope. One line. |
| `<cmd> --help` SYNOPSIS | Quick reference | Required flags, common pattern. |
| `<cmd> --help` EXAMPLES | What to copy | At least one happy-path; one common mistake. |
| Per-flag `--help` blocks | When the agent is composing the command | Type + unit + range + interaction with other flags. |
| `<cmd> <subcmd> --help` | Drill-down discovery | Same structure as top-level help. |
| Man pages / shipped docs | Rare; agent often won't read these | Last-resort reference, not the contract. |

The agent typically runs `<cmd> --help` once at the start of a task. Whatever's on that page is the contract. Anything past the help text is an error the description should have prevented.

## Bad-vs-good examples

### MCP example 1 — too vague

```json
{
  "name": "manage_data",
  "description": "Manages data in the system."
}
```

The agent has no idea what this tool does. "Manage" is the worst possible verb. "Data" is the worst possible noun. The model will not pick this tool over any other; if it does, it'll guess wildly at parameters.

```json
{
  "name": "search_orders",
  "description": "Search orders by customer, date range, or status. Returns up to 50 matches with status, total, and ship date. Side effect: none. Use list_orders for unfiltered pagination."
}
```

Verb + resource in the first 5 words. Constraint stated. Side effect stated. Sister tool referenced.

### MCP example 2 — too narrow

```json
{
  "name": "create_item",
  "description": "Only use this tool when the user explicitly asks to create a new item and has provided all required fields and confirmed they want to proceed."
}
```

The "only use when" framing makes the model err toward not calling. The "confirmed they want to proceed" check should be a schema parameter, not a language gate.

```json
{
  "name": "create_item",
  "description": "Create a new item with the given title and category. Requires title (string) and category (one of: 'task', 'note', 'doc'). Side effect: writes to the database; not reversible. Pair with delete_item if rollback is needed."
}
```

Verb + resource. Required params named. Side effect stated. Recovery path named.

### MCP example 3 — just right

```json
{
  "name": "send_invoice",
  "description": "Send a draft invoice to the customer's email. Requires invoice_id (string).\n\nExample: {\"invoice_id\": \"inv_abc123\"}\n\nSide effect: triggers email delivery; not reversible. Use preview_invoice to see the rendered version first.\n\nDo NOT use to update an existing sent invoice — use update_invoice_status instead."
}
```

Verb + resource. Required param. Example. Side effect. Sister-tool exclusion. Under 200 tokens.

### CLI example 1 — too vague

```
$ myco --help
Usage: myco [options] [command]

Options:
  -h, --help    show help

Commands:
  data          manage data
```

The agent learns nothing. "manage data" is unscannable.

```
$ myco --help
Usage: myco <command> [flags]

  Manage customer orders, invoices, and shipments via the agent-friendly API.

Commands:
  orders         search, get, create, update orders
  invoices       create, send, void invoices
  shipments      track, update, cancel shipments

Common flags (all commands):
  --json          structured JSON output (required for agents)
  --quiet         suppress logs to stderr
  --yes           non-interactive: auto-confirm prompts
  --timeout SECS  override default 30s timeout

Run "myco <command> --help" for command-specific docs.
```

### CLI example 2 — too narrow

```
$ myco delete-order --help
Delete an order. Only use when the user explicitly asks to delete and has confirmed
they understand the action is irreversible and has run --dry-run first to see what
will be deleted and has reviewed the dry-run output and decided they want to proceed.
```

The narrowing language is doing what a `--yes` flag and a `--dry-run` flag should be doing. Move the policy into flags; let the description state the action.

```
$ myco delete-order --help
Usage: myco delete-order ORDER_ID [--yes] [--dry-run] [--json]

  Permanently delete an order. Side effect: not reversible.

  --yes       confirm without interactive prompt (required for non-TTY runs)
  --dry-run   preview the deletion; no side effect
  --json      JSON envelope on stdout

EXAMPLE
  myco delete-order ord_123 --dry-run --json
  myco delete-order ord_123 --yes --json
```

### CLI example 3 — just right

```
$ myco apply --help
Usage: myco apply --file FILE [--idempotency-key KEY] [--json] [--dry-run]

  Apply a desired-state config file. Idempotent: re-running with the same input
  converges to the same outcome. Use --idempotency-key for safe retries across
  process restarts.

FLAGS
  --file FILE             path to YAML config; required
  --idempotency-key KEY   client-supplied key for safe retry; optional
  --json                  structured JSON envelope on stdout
  --dry-run               preview changes without applying
  --yes                   non-interactive: skip confirmation prompts

EXAMPLE
  myco apply --file deploy.yaml --json --idempotency-key deploy-2026-05-08

OUTPUT (--json)
  { "ok": true, "result": { "changes": [...] }, "schema_version": "1" }

EXIT CODES
  0  success           5  conflict
  2  usage             6  validation
  3  not-found         7  transient (retry safe)
  4  auth              8  partial
```

Verb on the first line. Idempotency stated explicitly. Required params marked. Example. Output shape. Exit codes documented.

## The "200-token prompt" test

Read the description aloud — once, top to bottom. Now ask: if this were the entire instruction the LLM had, would it know:

1. Whether to call this tool? (verb + resource + scope answer this)
2. What parameters are required, optional, and what their shapes are?
3. Whether the tool has side effects, and what they are?
4. What "success" looks like vs. what failure looks like?
5. Which related tool to use if this one isn't the right fit?

If any answer is "no", the description is missing the corresponding piece. If the description runs over 200 tokens, the model is also less likely to call the tool — community evaluations show over-verbose descriptions reduce call rate, not increase it (source: `optimize-agentic-mcp/patterns/tool-descriptions.md` Pattern 11).

The optimal description is short enough to scan and specific enough to select.

## Anti-patterns to refuse

**Bare types in parameter docs.** `"id": "string"` tells the model nothing. Add the kind, the source, the example.

**"This tool" or "This command" prefixes.** Wastes the first 2 tokens on filler.

**Restating the schema.** If the schema declares `enum: ["a", "b", "c"]`, don't repeat the enum in the description. Use the description for what *happens* when each value is picked.

**Description bloat.** Cramming every edge case into the description. Edge cases belong in errors (see `error-strategy.md` — error-driven learning handles the long tail). Core usage in description; edges in errors.

**Mismatched description and schema.** The description says "accepts ISO 8601 dates" but the schema is `string` with no `format`. The schema is the contract; the description must match it. Drift between them is a guaranteed agent footgun.

**Inconsistent naming across releases.** Renaming `customer_id` to `userId` between versions breaks every agent that learned the old name. Stable field names matter — see `output-contracts.md`.

## Cross-references

- For the schema layer (what's valid; how to flatten and tighten), read `../cli/flags-and-discovery.md` (CLI) or `../mcp/patterns/schema-design.md` (MCP).
- For the response shape paired with the description, read `output-contracts.md`.
- For error messages as continuation prompts, read `error-strategy.md`.
- For where each surface puts the description, read `../cli/output-envelope.md` (CLI) and `../mcp/patterns/tools.md` (MCP).
- For production exemplars and what they got right/wrong on descriptions, read `exemplars.md`.
