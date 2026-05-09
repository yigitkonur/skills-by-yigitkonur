# agent-cognitive-load — token budgets, tool counts, and progressive disclosure

The agent has limited context and limited attention. Every tool you register, every flag you expose, every byte you return either advances the task or burns budget. Design for both bounds. Source: `optimize-agentic-mcp/references/patterns/context-engineering.md` (6 patterns) and `optimize-agentic-mcp/references/patterns/progressive-discovery.md`, generalized to cover CLIs.

## The two budgets, and how they couple

Every agent call spends from two distinct accounts.

| Budget | What it covers | Hidden cost |
|---|---|---|
| Context tokens | Tool definitions, descriptions, prior responses, the user's prompt | Tool definitions inject on EVERY message, not only when invoked |
| Attention | The model's capacity to pick the right tool from a list and fill the right schema | Falls off a cliff past per-model thresholds, not a slope |

Tool definitions in particular eat ~15% of a typical Claude Code session's input tokens. A single complex tool like Playwright MCP can push that to 50%. Across a 30-turn conversation, 20 tools at 100 tokens each is 60,000 tokens gone before the agent has done a single useful thing. Source: community measurement on r/ClaudeAI; `optimize-agentic-mcp/references/patterns/context-engineering.md` Pattern 1.

The two budgets couple: more tools means more tokens AND more attention pressure. Past the model's tool-count cliff, accuracy drops while cost rises. Both vectors point the same direction — fewer, sharper tools.

## Tool-count heuristics — the three bands

Pick the band that matches the surface count today.

### 5–15 tools (sweet spot)

The model holds the entire catalog in working memory. Selection accuracy is high. Token cost is modest. This is the right size for almost every CLI and the right size for an MCP server unless you've consolidated thoughtfully.

What to verify in this band:

- Tool names are intent-based (`deploy_project`, `archive_message`), not API-based (`POST_v2_projects`, `DELETE_messages_id`).
- Descriptions lead with verb + resource in the first 5 words.
- No 3+ tools always called together for one task — those should be one consolidated tool.

### 15–30 tools (needs progressive discovery)

Past Gemini's sweet spot (~10) and approaching GPT-4's hard ceiling (~20). Claude tolerates this band, but only if descriptions are surgical. Take action:

- Cap the active tool set per model: Gemini 10, GPT-4 20, Claude 30.
- Group by intent and add a tool-set selector at connect time (Sentry's OAuth-consent grouping; Supabase's URL query param `?features=database,docs`).
- Consolidate CRUD into action-enum tools (`manage_ticket(action: enum)` instead of 5 per-entity tools).
- Consider progressive discovery — `list_tools(domain)` → `get_tool_schema(name)` — see `../mcp/patterns/progressive-discovery.md`.

### 30+ tools (almost always wrong granularity)

Two recovery paths:

1. **Consolidate aggressively to <20.** Best when most tools are CRUD wrappers that should collapse into action-enum tools.
2. **Switch to meta-tools / Codemode.** Best when the catalog is genuinely diverse. Cloudflare's published benchmark: 2,594 endpoints with full schemas = ~1,170,000 tokens; the same surface via 2-tool Codemode = ~1,000 tokens. 99.9% reduction. Source: `optimize-agentic-mcp/references/patterns/exemplar-servers.md` Copy #3.

The cliff isn't gentle. GPT-4 starts hallucinating tool calls past 50; Claude ignores tools beyond position 30. Adding a 31st tool doesn't add capacity — it removes it.

### Per-model thresholds

| Model | Sweet spot | Hard degradation |
|---|---|---|
| Gemini 1.5 Pro | 10 | ~100 |
| GPT-4 / 4.1 | 15–20 | 128 (API hard limit) |
| Claude 3.5 / 4 / 4.5 | 20–30 | ~50 |

If the server targets multiple models, design for the lowest cap.

## Token budget per response category

Different tool categories carry different size expectations. Cap proactively; don't wait for the agent to truncate.

| Tool category | Target response size | Strategy if larger |
|---|---|---|
| Scan / list | <500 tokens | Pagination with `has_more` and cursor; first-page-plus-summary hybrid |
| Fetch / describe | 500–3,000 tokens | Project to relevant fields; offer a `?fields=` selector for full payload when needed |
| Operate (create / update / delete) | <500 tokens | Status + `next_action`, not the full record |
| Iterate (multi-phase workflow) | <1,500 tokens per phase | Validation errors + progress + `next_action`; full state via separate `status` call |

A tool that routinely returns >5,000 tokens has the wrong shape. Project, paginate, or split. Cross-link `output-contracts.md` for the full envelope-sizing rules.

### Tiered verbosity — shrink as context fills

Optional but high-leverage: vary response size by remaining context budget. Three tiers from `optimize-agentic-mcp/references/patterns/context-engineering.md` Pattern 3:

| Remaining context | Tier | Response shape |
|---|---|---|
| >70% | Full | Complete records, all fields, pagination metadata |
| 40–70% | Summary | Count + top 5 + `detail_available: true` hint |
| <40% | Minimal | Count only + "Narrow your query or call get_details(id)" |

A tool that returns 10,000 rows at turn 40 silently degrades model performance. Tiered verbosity gives the model a graceful off-ramp.

## The "fewer tools beat more tools" principle

Granularity is intent-based, not API-based.

API-shaped tools mirror endpoints: `list_users`, `get_user`, `create_user`, `update_user`, `delete_user`, `list_user_roles`, `add_user_role`, `remove_user_role`, ... Five users, eight tools, and the agent still has to chain them to do "make alice an admin."

Intent-shaped tools mirror the user's verb: `manage_user(action: create|read|update|delete|search)`, `assign_role(user, role)`, `find_user(query)`. Three tools. The agent picks the right one without composing a sequence.

When 3+ tools always get called together for one user task, consolidate them into a single intent-based tool. Notion's own post-mortem (`notion.com/blog/notions-hosted-mcp-server-an-inside-look`, 2026): "1:1 API-to-tool mapping produced poor agent experiences, including high token use from hierarchical JSON block data." v2 added hand-written AI-first tools and abandoned the auto-generated 1:1 surface.

The same principle holds for CLIs. A CLI with 47 commands wrapping 47 endpoints fragments the agent's intent. A CLI with 8 verbs (`apply`, `delete`, `get`, `list`, `describe`, `auth`, `wait`, `version`) and well-designed nouns covers the same surface in less working memory.

## Surface mappings

### CLI — flag count, command count, sub-command discoverability via `--help`

The CLI's cognitive surface lives in three places:

| Surface | Read by | Cap |
|---|---|---|
| Top-level `--help` | First thing the agent reads | <80 lines; one-liner per subcommand |
| Per-command `--help` | When agent composes the call | <60 lines; required flags + 1–2 examples + exit codes |
| Flag count per command | When agent reads `--help` | <12 flags per command; >15 means split |

Heuristics:

- **>15 flags on a single command** is a sign that command is doing too many things. Split into multiple commands or accept a config file (`mytool apply -f config.yaml`).
- **>40 commands at the top level** is the CLI equivalent of a 40-tool MCP. Group by noun (`mytool app create` instead of `mytool create-app`) or split into separate binaries.
- **Sub-command nesting past 2 levels** loses the agent. `mytool resource app create` is worse than `mytool app create`.

The agent reads `<cmd> --help` once at the start of a task. Whatever's on that page is the contract. Anything past the help text is an error the description should have prevented.

### MCP — tool count, description length, response size, progressive discovery

The MCP cognitive surface lives in `tools/list`:

| Surface | Read by | Cap |
|---|---|---|
| Tool count | `tools/list` at session start | Per-model sweet spot (above) |
| Tool name | At every selection | snake_case; verb + resource; namespaced |
| Tool description | At every selection | <100 tokens; first 5 words = verb + resource |
| Parameter description | When filling args | Type + unit + range + 1 example |
| Response payload | After every call | Per-category cap (above) |
| Server `instructions` (init) | Once per session | Capabilities map; recommended workflows |

When the catalog token cost exceeds ~5% of the agent's context window, the server should offer a tool-subset selector at connect time. Sentry does this via OAuth consent groups. Supabase does it via URL query params (`?features=database,docs`). GitHub via toolset flags at deploy. Cross-link `../mcp/patterns/progressive-discovery.md` for the full progressive-discovery patterns.

The Code Execution Pattern (Anthropic's published benchmark: 150k tokens → 2k, 98.7% reduction) is the most aggressive form. Replace static tool definitions with a single `execute_code()` tool that does on-demand discovery via `list_servers()` → `list_tools(server)` → `get_tool_schema(server, tool)`. Schemas are fetched only when needed and discarded after the call. Source: `optimize-agentic-mcp/references/patterns/context-engineering.md` Pattern 2; works for stdio/local servers, harder for OAuth-gated remote servers.

## Description token cost — the hidden compounder

Tool descriptions inject on every message, not only when the tool is invoked. Trim aggressively.

A description in the 100–200 token range injected across 30 turns costs 3,000–6,000 tokens for one tool. Twenty tools at that range is 60,000–120,000 tokens of description alone. The agent has not yet done a single useful thing.

Heuristics for description length:

| Description state | Token cost (per tool) | Action |
|---|---|---|
| Verb + resource + 1 example | 50–80 | Sweet spot |
| Verb + resource + multiple examples + side effects | 80–150 | Acceptable for high-stakes tools |
| Long prose explaining when not to use | 150–300 | Trim — over-narrowing reduces call rate |
| Restating the schema in prose | 300+ | Almost always wrong; rewrite |

Over-verbose descriptions reduce call rate; the model interprets length as friction. Cap at 100 tokens; lead with the verb. Source: `optimize-agentic-mcp/references/patterns/tool-descriptions.md` Pattern 11. Cross-link `descriptions-as-prompts.md`.

## ANSI / progress-bar inflation on shell-wrapped tools

When an MCP tool wraps a CLI binary, raw CLI output inflates token cost by 5–95×. Measured reductions from the Pare MCP project:

| CLI command | Raw output (tokens) | Cleaned (tokens) | Reduction |
|---|---|---|---|
| `docker build` (multi-stage) | 373 | 20 | 95% |
| `git log --stat` (5 commits) | 4,992 | 382 | 92% |
| `npm install` (487 packages) | 241 | 41 | 83% |
| `vitest run` (28 tests) | 196 | 39 | 80% |
| `cargo build` (2 errors) | 436 | 138 | 68% |

Strip ANSI escape sequences, carriage-return progress redraws, spinner Unicode, and box-drawing characters before returning CLI output. Set `NO_COLOR=1` and `TERM=dumb` in the subprocess environment to suppress at source. Source: `optimize-agentic-mcp/references/patterns/context-engineering.md` Pattern 4.

For CLI authors: detect non-TTY stdout and auto-suppress ANSI; honor `NO_COLOR=1`. The harness shouldn't have to scrub.

## Concrete examples

### 50-tool MCP server refactored to 12

Anti-pattern surface (from a real customer support MCP):

```
list_tickets, get_ticket, create_ticket, update_ticket, delete_ticket,
list_users, get_user, create_user, update_user, delete_user,
list_orgs, get_org, create_org, update_org, delete_org,
search_tickets, search_users, search_orgs,
... (32 more variants for comments, tags, attachments, audit logs)
```

Refactored intent surface (12 tools):

```
manage_ticket(action: create|read|update|delete|search, ...)
manage_user(action: create|read|update|delete|search, ...)
manage_org(action: create|read|update|delete|search, ...)
list_recent_activity(scope: ticket|user|org, ...)
attach_to_ticket(ticket_id, kind: comment|tag|file, ...)
get_ticket_history(ticket_id, ...)
escalate_ticket(ticket_id, reason, ...)
merge_tickets(source_id, target_id, ...)
search_global(query, kinds[]: ticket|user|org, ...)
get_audit_log(scope_id, kind, ...)
export_report(report_kind, ...)
notify_assignee(ticket_id, message)
```

Key moves:

- CRUD collapsed into `manage_<entity>(action: enum)` — 15 tools to 3.
- Cross-entity searches collapsed to one `search_global` with `kinds[]`.
- Verb-led intents (`escalate_ticket`, `merge_tickets`) added — they were previously implicit multi-step sequences.

Token impact: catalog drops from ~5,000 to ~1,200; tool selection accuracy rises measurably.

### Sprawling CLI with 80 flags simplified to 20

Anti-pattern: `mytool deploy` with 80 flags spanning auth, networking, build options, runtime config, scaling, observability, debug.

```bash
mytool deploy --image=... --tag=... --registry=... --build-context=... \
  --build-arg=... --secrets=... --aws-region=... --aws-profile=... --vpc=... \
  --subnet=... --security-group=... --cpu=... --memory=... --replicas=... \
  --autoscale-min=... --autoscale-max=... --autoscale-cpu=... --healthcheck-path=... \
  --healthcheck-interval=... --healthcheck-timeout=... --log-driver=... ...
```

Agent reads 80 flags, picks 12, fills 5 wrong, gets a validation error.

Refactored:

```bash
mytool apply -f deploy.yaml          # 1 flag; the YAML carries the structure
mytool scale myservice --replicas=3  # 1 flag; targeted to one decision
mytool logs myservice --since=1h     # 2 flags; targeted to one read
mytool wait myservice --status=ready # 2 flags; targeted to one check
```

The 80 flags become structure inside `deploy.yaml`. The CLI exposes 20 flags total across 8 commands. The agent picks the right command first, then fills 1–2 flags. Same surface; vastly less attention pressure.

## Anti-patterns to refuse

- **Adding meta-tools without consolidating first.** Don't wrap a 50-tool catalog with `find_tools` and call it done. Consolidate, then add discovery if still needed.
- **Listing every endpoint as a tool.** REST 1:1 is a guaranteed routing miss past 10 tools.
- **Stuffing every option into one command.** A `mytool do-everything --mode=X` with 30 modes is one tool the agent can't disambiguate.
- **Mid-session tool injection.** Adding tools to `tools/list` mid-session forces the agent to re-read the catalog. Stable surface beats dynamic surface.
- **Verbose descriptions to "be helpful".** Over-verbose descriptions reduce call rate, not increase it. The model interprets length as friction. Cap at 100 tokens; lead with the verb.
- **Returning raw API JSON.** Linear's `list_users` ships `createdAt`, `updatedAt`, `avatarUrl`, `isAdmin`, `isGuest` when the agent only wants assignment IDs. Project to fields the agent will actually use. Cross-link `output-contracts.md`.
- **Pretty-printed JSON in agent responses.** Wastes bytes; some harnesses chunk on newlines. Pretty-print only when stdout is a TTY.
- **Forgetting that descriptions inject EVERY message.** Tool definitions aren't paid for once; they're paid every turn. Trim accordingly.

## Token-budget audit checklist

Before declaring an MCP server or CLI agent-ready on cognitive load, verify:

- [ ] Tool count is at or below the lowest target model's sweet spot.
- [ ] No description exceeds 100 tokens; most under 80.
- [ ] Tool definitions plus first-message catalog cost <5% of context window.
- [ ] No tool routinely returns >5,000 tokens.
- [ ] CLI output is ANSI-stripped on non-TTY.
- [ ] Pagination ships with `has_more` and a cursor.
- [ ] Truncation ships with a `truncated: true` signal.
- [ ] Tiered verbosity is implemented OR documented as "not yet" in `meta`.

## Cross-references

- For description-as-prompt principles that cap description length, read `descriptions-as-prompts.md`.
- For output-shape principles that cap response size, read `output-contracts.md`.
- For progressive discovery on MCP specifically, read `../mcp/patterns/progressive-discovery.md`.
- For the tool-count decision tree on MCP, read `../mcp/decision-trees/tool-count.md`.
- For CLI flag-count and discoverability, read `../cli/flags-and-discovery.md`.
- For exemplars that ship at each band of the cognitive-load spectrum, read `exemplars.md`.
