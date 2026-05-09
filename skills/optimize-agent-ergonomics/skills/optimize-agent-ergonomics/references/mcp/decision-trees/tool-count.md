# Decision tree — tool count and granularity

Decide tool granularity by counting first, then by intent. Past the per-model sweet spot, routing accuracy collapses; before it, the question is intent vs. API shape. This tree routes to the right consolidation, progressive-discovery, or splitting pattern for the count you have.

## Decision branches

```
START: How many tools does the server expose today?
|
+-- < 5 tools
|   +-- Likely under-granular for the workload
|   +-- Can each be split into intent-based tools?
|   |   +-- YES --> split (verb + resource per tool); revisit Q4 of architect-new.md
|   |   +-- NO  --> server is genuinely small; tighten descriptions and stop
|   +-- --> ../patterns/tools.md (granularity + descriptions)
|
+-- 5-15 tools
|   +-- Sweet spot. Verify the granularity is intent-based, not API-based.
|   +-- Are tool names verb+resource (deploy_project, archive_message)?
|   |   +-- YES --> good; check descriptions next
|   |   +-- NO  --> rewrite around user intents; CRUD into action enums
|   +-- Any 3+ tools always called together for one task?
|   |   +-- YES --> consolidate into one intent-based tool
|   |   +-- NO  --> keep separate
|   +-- --> ../patterns/tools.md
|
+-- 15-30 tools
|   +-- Past Gemini's sweet spot (~10) and approaching GPT-4's limit (~20)
|   +-- Match the cap to the target model:
|   |   +-- Claude target  --> safe up to ~30
|   |   +-- GPT-4 target   --> cap active at 20
|   |   +-- Gemini target  --> cap active at 10
|   +-- Consolidate CRUD into action-enum tools
|   +-- Consider progressive discovery (toolsets / session-unlock)
|   +-- --> progressive-discovery and pattern files below
|
+-- 30+ tools
|   +-- Almost certainly wrong granularity OR static-list anti-pattern
|   +-- Two recovery paths:
|   |   1. Consolidate aggressively to <20 (best when most tools are CRUD wrappers)
|   |   2. Progressive discovery / meta-tools (best when the catalog is genuinely diverse)
|   +-- Consider splitting into multiple servers (see "tool count vs server count" below)
|   +-- --> ../patterns/progressive-discovery.md, ../patterns/tools.md
```

## Per-model sweet spots

| Model | Static-list cap | Active-set cap with progressive discovery |
|---|---|---|
| Gemini 1.5 Pro | ~10 | ~10 |
| GPT-4 / GPT-4.1 | ~15–20 | 20 |
| Claude 3.5 / 3.7 / 4 / 4.5 | 20–30 | 30 |

If the server targets multiple models, design for the lowest cap.

## Worked example — 50 tools refactored to 12 intent-based tools

Anti-pattern surface (sourced from a real customer support MCP):

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
- Each tool's description leads with verb + resource; the action enum is documented inline.

The agent now picks from 12 instead of 50; tool-selection accuracy and routing both improve. Schema-design for the action-enum pattern: `../patterns/schema-design.md`.

## Tool count vs server count

Adding tools to a single server is not the only lever. Sometimes the right move is to split.

### When to keep one server

- Domain is genuinely cohesive (one mental model for the agent).
- Tools share auth, session, and rate-limit configuration.
- Total intent-based count fits the model's sweet spot.

### When to split into multiple servers

- Tool count is intrinsically high after consolidation (say, 40+ post-refactor).
- Domains are unrelated (the agent never composes a ticket tool with a payments tool in one task).
- Auth or trust boundaries differ (one server is internal-only; another is exposed to a marketplace).
- Different scaling profiles (one tool fires 100x more than the others).

### Gateway pattern for many servers

When 3+ servers ship together for one user, route through a gateway that:
- Prefixes tool names by server (`tickets__create`, `payments__refund`) to avoid collisions.
- Provides a unified `tools/list`.
- Lazy-starts servers and stops idle ones (e.g., 2-min idle timeout).
- Circuit-breaks on unreachable upstream servers.

Deep dive: `../patterns/transport-and-ops.md` and `../patterns/registry-and-distribution.md`.

## Symptom-driven checks during an audit

| Symptom | Likely cause | Action |
|---|---|---|
| Agent picks wrong tool >5% of the time | Static list past the model's cap | Cap with progressive discovery |
| Agent hallucinates tool names | Description quality + count | `../patterns/tools.md` (descriptions) + cap |
| Initial prompt token estimate >40k | Static schemas for too many tools | Switch to `find_tools` / `execute_tool` meta-pattern |
| Agents call 3+ tools every task in the same order | Under-granular; missing intent tool | Add the intent tool that wraps the sequence |
| Agents abandon mid-task | Description ambiguity OR action enum too dense | Split the densest action enum, or rewrite descriptions |

## Anti-patterns

- **Listing every endpoint as a tool.** REST 1:1 is a guaranteed routing miss past 10 tools.
- **Treating tool count thresholds as hard verdicts.** They are diagnostic cues. A 25-tool MCP for Claude can be fine if the descriptions are surgical and the audience is Claude-only.
- **Adding meta-tools without consolidating first.** Don't wrap a 50-tool catalog with `find_tools` and call it done. Consolidate, then add discovery if still needed.
- **Splitting servers prematurely.** Two servers that share auth, session, and rate-limits should usually be one server.

## When to re-evaluate

- Tool count crosses the next cliff (5 / 15 / 30 / 50 / 100).
- Target model changes (each has a different cap).
- Agent transcripts show wrong-tool selection or hallucinated tool names.
- A new entity type is added — choose now: separate CRUD or fold into the existing action enum.
- Initial prompt context exceeds 40k tokens — compress via discovery.

## Cross-references

- Tool granularity, naming, response shape, descriptions: `../patterns/tools.md`.
- Schema for action-enum tools: `../patterns/schema-design.md`.
- Progressive discovery, toolsets, session-unlocked tools: `../patterns/progressive-discovery.md`.
- Cognitive-load principles across surfaces: `../../common/agent-cognitive-load.md`.
- Architecture lock-ins set at design time: `design-phase.md`.
