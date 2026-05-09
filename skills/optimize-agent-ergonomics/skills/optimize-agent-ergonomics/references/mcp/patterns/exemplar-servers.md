# Exemplar MCP servers — what production vendors actually shipped

Sixteen production MCP servers from major vendors, what each does well, what each does poorly, with citations. Use this file as evidence when making design calls — when a sibling pattern says "do X," look here for which vendors validated it in production and how. Cross-link `../../common/exemplars.md` for the cross-surface vendor comparison (production CLIs alongside MCP servers); this file is the MCP-only deep dive.

**Headline findings, 2026-04.** The ecosystem has converged on **remote/hosted transports over stdio**, **OAuth 2.1 + PKCE over long-lived API keys**, and **intent-consolidated tools over 1:1 OpenAPI wrappers**. It has diverged sharply on **tool count philosophy** (Cloudflare 2 → GitHub 56 → Atlassian Rovo 54), **`structuredContent` adoption** (spec-recommended, but Supabase and Linear explicitly opt out), and **naming convention** (mostly `snake_case`, Notion uses `kebab-case`, Atlassian uses `camelCase`).

---

## GitHub MCP — `github/github-mcp-server`

- **Source.** `github.com/github/github-mcp-server`, preview 2025-04-04.
- **Surface.** 56+ tools grouped by toolsets (`actions`, `issues`, `pull_requests`, `repos`, `code_security`, `dependabot`, `discussions`, `gists`, `notifications`, `orgs`, `projects`, `secret_protection`, `security_advisories`, `users`, `copilot`). Dynamic toolset discovery. `snake_case`, resource-prefixed.
- **What to copy.** **Description override at deploy time** via `github-mcp-server-config.json` — operators rewrite tool descriptions per environment without forking. **Lockdown mode filters response content per method** when the caller lacks push access — finer than a binary read-only flag. **Insiders channel** activated via URL suffix `/insiders` OR `X-MCP-Insiders: true` header — two activation vectors for the same flag.
- **What to avoid.** `create_pull_request_with_copilot` was silently removed from the remote surface with no deprecation note in the server `instructions` block (issue #1220, 2025-10-15). When removing or gating tools, announce in `instructions` and return structured errors pointing at replacements.
- **Most interesting tool.** `github_support_docs_search` — the parameter description is itself a behavioral policy: "Input from the user about the question they need answered. This is the latest raw unedited user message. You should ALWAYS leave the user message as it is, you should never modify it." Description-as-enforcement.
- **Auth / transport.** OAuth (GitHub App / OAuth App) or PAT Bearer locally; OAuth remote at `api.githubcopilot.com/mcp/`; Docker, GHE Cloud with data residency via `ghe.com`. No remote endpoint for GHES.

---

## Linear MCP

- **Source.** `linear.app/docs/mcp`; reverse-engineered tool dump at [blog.fiberplane.com/blog/mcp-server-analysis-linear/](https://blog.fiberplane.com/blog/mcp-server-analysis-linear/) (2025).
- **Surface.** 23 tools, remote-only. `list_issues`, `list_projects`, `list_teams`, `list_users`, `list_documents`, `list_cycles`, `list_comments`, `list_issue_labels`, `list_issue_statuses`, `list_project_labels`; `get_issue`, `get_project`, `get_team`, `get_user`, `get_document`, `get_issue_status`; `create_issue`, `create_project`, `create_comment`, `create_issue_label`; `update_issue`, `update_project`; `search_documentation`. Intent-consolidated, explicitly not a 1:1 GraphQL wrapper.
- **What to copy.** **Flatten nested filters.** Linear collapses GraphQL's nested filter objects into flat `assigneeId`, `teamId`, `stateId`. Documents enum values inline in description: `"Priority: 0 = No priority, 1 = Urgent, 2 = High, 3 = Normal, 4 = Low"`. Magic value `"me"` accepted for assignee.
- **What to avoid.** **Tool catalog measures 17.3k tokens after connect** — context jumps 61k → 78k before the agent runs its first tool. Avoid `structuredContent` omission with no compensating shape; Linear ships stringified JSON in `content[].text` and includes noise fields (`createdAt`, `updatedAt`, `avatarUrl`, `isAdmin`, `isGuest`) in `list_users` even though agents almost only want assignment data. Strip noise; offer a tool-subset selector at connect time when catalog cost exceeds ~5% of context window.
- **Auth / transport.** OAuth, hosted Streamable HTTP.

---

## Stripe MCP — `stripe/agent-toolkit`

- **Source.** `github.com/stripe/agent-toolkit`.
- **Surface.** ~25 tools across Payments, Customers, Products, Prices, Invoices, Subscriptions, Refunds, Disputes, Balance, Payment Links, Coupons. `snake_case`, `--tools=` flag selects subsets at launch time.
- **What to copy.** **Reuse existing fine-grained API key permissions as the MCP permissions surface.** Stripe has no MCP-level scope system — Restricted API Keys (`rk_*`) are the permissions surface. For Connect platforms, `context.account = "acct_123"` switches tenant per call. When a fine-grained permissions primitive already exists, reuse it rather than inventing parallel scopes.
- **What to avoid.** Without Restricted Keys, this design forces single-key-fits-all, which leaks more than the agent should be able to do. Don't ship without a permissions primitive comparable in granularity.
- **Ecosystem.** `@stripe/agent-toolkit` (framework helpers), `@stripe/ai-sdk` (Vercel AI SDK bindings), `@stripe/token-meter` (usage metering for LLM-driven Stripe actions).
- **Auth / transport.** Remote OAuth at `https://mcp.stripe.com`; local via `npx -y @stripe/mcp --api-key=...`.

---

## Notion MCP — `makenotion/notion-mcp-server` + hosted

- **Source.** [notion.com/blog/notions-hosted-mcp-server-an-inside-look](https://www.notion.com/blog/notions-hosted-mcp-server-an-inside-look) (2026 post-mortem).
- **Surface.** v1 = 19 tools (1:1 from OpenAPI, auto-generated); v2 = 22 tools (hybrid, AI-first rewrites + wrappers for gap coverage). Naming is **`kebab-case`** — unusual: `query-data-source`, `retrieve-a-data-source`, `create-pages`, `update-page`, `search`, `create-comment`. Body delivered as **"Notion-flavored Markdown"** — introduced specifically because raw JSON blocks were too token-heavy.
- **What to copy.** **Custom Markdown body format.** When the canonical JSON is too verbose for agents, define a Markdown variant tuned for LLM consumption.
- **What to avoid.** **1:1 OpenAPI → MCP generation.** Notion's own post-mortem (verbatim): "1:1 API-to-tool mapping produced poor agent experiences, including high token use from hierarchical JSON block data." v2 added hand-written AI-first tools and Notion-flavored Markdown specifically because v1's auto-generated surface was unusable.
- **Pipeline.** OpenAPI → Zod for schema generation; hand-written tools layered on top.
- **Auth / transport.** OAuth "one-click" shared public integration. Streamable HTTP primary + SSE fallback.

---

## Sentry MCP — `getsentry/sentry-mcp`

- **Source.** [docs.sentry.io/ai/mcp/](https://docs.sentry.io/ai/mcp/).
- **Surface.** ~10–15 tools incl. `search_events`, `search_issues`, `use_sentry`. **Tool groups (Issues / Errors / Projects / Seer / discovery) are selectable at OAuth consent time** — the user picks which groups are exposed during the consent flow, shrinking the post-connect tool catalog per user rather than per tenant.
- **What to copy.** **Tool-group selection at OAuth consent.** Lets a user opt into a smaller, task-specific surface without per-tenant config.
- **What to avoid.** **NL search tools require caller-supplied `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`** via `EMBEDDED_AGENT_PROVIDER` — an embedded LLM inside the MCP. Operationally fragile: the user's keys are routed through Sentry's server. Useful pattern only when the embedded reasoning is genuinely faster than the agent could do; in most cases, return raw data and let the calling agent reason.
- **Response discipline.** Sister `build_sim` pattern returns only `warnings | errors | status | next-step hints` — median 2.1 KB vs raw xcodebuild logs.
- **Auth / transport.** Cloud = OAuth Streamable HTTP at `mcp.sentry.dev/mcp`; device-code for stdio. Self-hosted = access token.

---

## Figma Dev Mode MCP

- **Source.** [developers.figma.com/docs/figma-mcp-server/tools-and-prompts/](https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/); announcements [figma.com/blog/introducing-figma-mcp-server/](https://www.figma.com/blog/introducing-figma-mcp-server/) (2025-06-04 beta) and [figma.com/blog/design-systems-ai-mcp/](https://www.figma.com/blog/design-systems-ai-mcp/) (2025-08-06).
- **Surface.** 15 tools (launched with 3). `snake_case`. Includes `generate_figma_design`, `get_design_context`, `get_variable_defs`, `get_code_connect_map`, `add_code_connect_map`, `get_screenshot`, `create_design_system_rules`, `get_metadata`, `get_figjam`, `generate_diagram`, `whoami`, `get_code_connect_suggestions`, `send_code_connect_mappings`, `use_figma`, `search_design_system`, `create_new_file`.
- **What to copy.** **Server-side repo introspection** via `create_design_system_rules` — scans the caller's codebase from the MCP server side and emits a rules file the agent can consume. Inverts the usual "agent reads repo" flow. **`whoami` returns auth identity** — operationally invaluable for debugging which account the agent is actually acting as.
- **What's distinctive.** `generate_diagram` converts Mermaid → FigJam, a reverse-bridge no other vendor replicates. `get_metadata` returns sparse XML; `get_figjam` returns XML + screenshots.
- **Design thesis** (verbatim from launch blog). "Context > pixels; goal is alignment to design intent, not pixel-matching."
- **Auth / transport.** Figma desktop app session; local stdio with remote tools mixed in.

---

## Cloudflare MCP — `mcp-server-cloudflare` + product mesh

- **Source.** `github.com/cloudflare/mcp-server-cloudflare`; [developers.cloudflare.com/agents/model-context-protocol/mcp-servers-for-cloudflare/](https://developers.cloudflare.com/agents/model-context-protocol/mcp-servers-for-cloudflare/); [blog.cloudflare.com/model-context-protocol/](https://blog.cloudflare.com/model-context-protocol/) (2024-12-20 — earliest public MCP from a major vendor).
- **Surface.** **2 tools total** for the Cloudflare API MCP — `search()` and `execute()`. Plus 16+ product-specific servers (docs, bindings, builds, observability, radar, containers, browser rendering, logpush, AI Gateway, AI Search, audit logs, DNS analytics, DEX, CASB, GraphQL, Agents SDK), each at its own URL.
- **What to copy.** **Codemode pattern** for large APIs. `execute()` accepts JavaScript written against a typed OpenAPI spec, runs it in an isolated Dynamic Worker sandbox. **Published benchmark: 2,594 endpoints × full schemas = ~1,170,000 tokens for native MCP exposure. Required-params-only = 244,000. Codemode = ~1,000 tokens.** The most concrete large-surface cost number publicly available in the ecosystem.
- **What to avoid.** Codemode requires typed bindings; not applicable to event-driven or stateful APIs. Don't reach for it without OpenAPI + JS-runnable client SDKs.
- **Auth / transport.** OAuth or API token. Streamable HTTP `/mcp`; deprecated `/sse`.

---

## Atlassian Rovo MCP

- **Source.** [support.atlassian.com/atlassian-rovo-mcp-server/docs/supported-tools/](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/supported-tools/). GA 2026-02-04.
- **Surface.** 54 tools — Jira (13), Confluence (11), JSM (4), Bitbucket Cloud (23), Rovo code/shared (4), Teamwork Graph (2 beta), Compass (12). **Naming is `camelCase`** — major outlier. `getJiraIssue`, `createConfluencePage`, `searchJiraIssuesUsingJql`. Bitbucket uses dotted sub-action names: `bitbucketPullRequest.approve`, `bitbucketRepoContent.branch.get`.
- **What to copy.** **Cross-product Teamwork Graph tools** (`getTeamworkGraphContext`, `getTeamworkGraphObject`) return entity context spanning Jira + Confluence + Bitbucket for a single object. When your product has multiple surfaces referring to the same entity, expose the graph-walk instead of forcing the agent to join three tool calls.
- **What to avoid.** `camelCase` is a portability risk — clients that assume `snake_case` may render or filter incorrectly. When breaking from `snake_case`, document loudly.
- **Response.** Confluence body delivered as Markdown.
- **Auth.** OAuth; users consent per AI client; admins allowlist clients.

---

## Slack MCP — `modelcontextprotocol/servers` (community + reference impls)

- **Source.** Reference implementation in `github.com/modelcontextprotocol/servers/tree/main/src/slack`; multiple community servers (`@modelcontextprotocol/server-slack`, third-party hosted variants).
- **Surface.** Typically 8–12 tools: `list_channels`, `post_message`, `reply_to_thread`, `add_reaction`, `get_channel_history`, `get_thread_replies`, `get_users`, `get_user_profile`. `snake_case`. Intent-consolidated.
- **What to copy.** **Channel-name-to-ID resolver inside the tool.** Slack's API uses opaque channel IDs (`C04BKGH3L8P`), but agents reason in human names (`#general`). The good Slack MCPs accept either and resolve internally — pair with `tools.md` § "Return semantic identifiers, not opaque UUIDs."
- **What to avoid.** Bot-token-based Slack MCPs require the bot to be invited to every private channel. The tool surface looks complete, but calls to channels the bot hasn't joined return cryptic 404s. Either return a clear "bot not in channel" error with the join command, or use user tokens that follow the user's permissions.
- **Auth / transport.** OAuth bot tokens (default reference) or user tokens; stdio or Streamable HTTP. Cross-link `auth-identity.md` for token-scope hygiene.

---

## Postgres MCP — `modelcontextprotocol/servers` reference + community

- **Source.** Reference at `github.com/modelcontextprotocol/servers/tree/main/src/postgres`; production fork at `github.com/crystaldba/postgres-mcp` adds health checks and advisor tooling.
- **Surface.** 3–5 tools typically: `query` (read-only by default), `list_tables`, `describe_table`, `list_indexes`, optionally `analyze_query` for explain plans. `snake_case`.
- **What to copy.** **Read-only by default; writes behind an explicit flag.** Database tools default `read_only: true`; mutating queries require explicit opt-in. **Wrap returned rows in untrusted-data tags** (Supabase pioneered this — see below). **Stream large results** rather than buffering — Postgres tables can be huge.
- **What to avoid.** A Postgres MCP that returns raw rows in a stringified table format leaks PII, blows context budget, and exposes prompt-injection vectors via row content. Always sanitize, summarize, paginate, and wrap untrusted text.
- **Auth / transport.** Connection string in env var; stdio. For multi-tenant deploys, route through a connection pooler (PgBouncer / RDS Proxy) and keep the MCP stateless.

---

## Filesystem MCP — `modelcontextprotocol/servers/filesystem`

- **Source.** Reference at `github.com/modelcontextprotocol/servers/tree/main/src/filesystem`.
- **Surface.** 6–10 tools: `read_file`, `write_file`, `edit_file`, `list_directory`, `search_files`, `move_file`, `create_directory`, `directory_tree`. `snake_case`.
- **What to copy.** **Roots-based scoping.** The server reads the client's `roots/list` capability to know which directories it's allowed to access. Outside roots, every tool returns an error. Pairs with VS Code, Claude Code, and Cursor's roots support — cross-link `client-compatibility.md`.
- **What to avoid.** **Path traversal protection must be airtight.** A `read_file` that accepts `"../../etc/passwd"` is a security incident. Validate every path against the resolved real-path of the active root.
- **Auth / transport.** None at protocol level; stdio with the user's filesystem access. For remote hosting, gate behind OAuth + per-user filesystem mount.

---

## Google Drive MCP — `modelcontextprotocol/servers/gdrive` + Anthropic-managed

- **Source.** Reference at `github.com/modelcontextprotocol/servers/tree/main/src/gdrive`; Anthropic-managed at `mcp.claude.ai/google-drive`.
- **Surface.** ~6 tools: `search_files`, `read_file`, `create_file`, `update_file`, `share_file`, `list_folders`. Hosted variant adds OAuth-scoped browse.
- **What to copy.** **Mime-type-aware fetching.** `read_file` projects Google Docs to Markdown, Sheets to CSV, Slides to plain-text outline — never returns the raw Google export blob. The agent gets parseable content.
- **What to avoid.** **Don't expose internal Google file IDs as the only handle.** Pair every ID with the human-readable file name in responses (cross-link `tools.md` § "Return semantic identifiers"). The Anthropic-managed version does this; older community implementations don't.
- **Auth / transport.** OAuth 2.0 with Drive scopes; Streamable HTTP for hosted.

---

## Brave Search MCP — `modelcontextprotocol/servers/brave-search`

- **Source.** Reference at `github.com/modelcontextprotocol/servers/tree/main/src/brave-search`.
- **Surface.** 1–2 tools: `brave_web_search` (and sometimes `brave_local_search`). `snake_case`. Minimal surface.
- **What to copy.** **Tight, specific descriptions when the surface is small.** `brave_web_search` description includes example queries and the result shape. Easy for the agent to pick correctly first-time. **Search-frontier response** — returns top results plus suggested next queries, in line with the `tools.md` § "Return a search frontier" pattern.
- **What to avoid.** Search MCPs that return raw HTML or full result-page HTML waste context budget. Always project to title + URL + snippet + score.
- **Auth / transport.** API key in env; stdio.

---

## Time MCP — `modelcontextprotocol/servers/time`

- **Source.** Reference at `github.com/modelcontextprotocol/servers/tree/main/src/time`.
- **Surface.** 2 tools: `get_current_time`, `convert_time`. Minimal.
- **What to copy.** **Single-purpose servers are fine.** Not every MCP needs to be feature-rich. A 2-tool server that does timezones correctly is more useful than a 30-tool server where 28 tools the agent never calls dilute the catalog.
- **What to avoid.** Don't bundle "Time" with unrelated tools just to inflate the surface.
- **Auth / transport.** None; stdio.

---

## Memory MCP — `modelcontextprotocol/servers/memory`

- **Source.** Reference at `github.com/modelcontextprotocol/servers/tree/main/src/memory`.
- **Surface.** ~8 tools for a knowledge graph: `create_entities`, `create_relations`, `add_observations`, `delete_entities`, `delete_observations`, `delete_relations`, `read_graph`, `search_nodes`. `snake_case`.
- **What to copy.** **Persistent agent memory done right.** Graph-shaped, queryable, append-mostly. Cross-link `session-and-state.md` § "Per-user across sessions" — Memory MCP is a worked example of the long-lived state pattern, deliberately external to the conversation context.
- **What to avoid.** Memory MCPs that grow unbounded blow context budget the moment the agent reads them. Set retention policies (TTL on observations, max-entities-per-user) and surface them in tool responses.
- **Auth / transport.** Local file or external graph DB; stdio.

---

## Sequential Thinking MCP — `modelcontextprotocol/servers/sequentialthinking`

- **Source.** Reference at `github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking`.
- **Surface.** 1 tool: `sequentialthinking`. Lets the agent record a structured thought trace with branching and revision.
- **What to copy.** **A single-tool server can be a UX pattern.** Sequential Thinking is not a data tool — it's an externalized scratchpad. Models use it to slow down on hard problems. Counterpart pattern in `agentic-patterns.md` § "Use a planner tool to teach the workflow" — same idea, different framing.
- **What to avoid.** Don't auto-invoke it for trivial tasks. The model should pick it for genuinely complex reasoning, not as a default warm-up.
- **Auth / transport.** None; stdio.

---

## Head-to-head comparison

Compact pivot of the 16 profiles above on the dimensions that actually drive design decisions.

| Server | Tools | Naming | Granularity | Response | Auth | `structuredContent` |
|---|---|---|---|---|---|---|
| GitHub | 56+ | `snake_case` + enum verbs | Hybrid: enum dispatchers | Text + some JSON | OAuth / PAT Bearer | No |
| Linear | 23 | `snake_case` | Intent-consolidated | Stringified JSON in text | OAuth | No |
| Stripe | ~25 | `snake_case` | Intent-consolidated | JSON | OAuth + Restricted Keys | — |
| Notion v2 | 22 | `kebab-case` | Hybrid: AI-first + wrappers | Notion-flavored Markdown | OAuth | — |
| Sentry | ~10–15 | `snake_case` | Intent + embedded LLM | Text | OAuth / Token | — |
| Figma | 15 | `snake_case` | Per-capability | Text / XML / React+TW / screenshots | Desktop session | — |
| Atlassian Rovo | 54 | `camelCase` + dotted | Hybrid: flat + nested | Markdown for pages | OAuth | — |
| Cloudflare API | 2 | `camelCase` (in JS) | Codemode (JS sandbox) | JS result | OAuth / API token | — |
| Slack (community) | 8–12 | `snake_case` | Intent-consolidated | JSON | OAuth bot/user token | — |
| Postgres (reference) | 3–5 | `snake_case` | Read-only by default | TSV / JSON | Connection string | — |
| Filesystem | 6–10 | `snake_case` | Per-action | Text | Roots-scoped | — |
| Google Drive | ~6 | `snake_case` | Mime-type-aware | Markdown / CSV / outline | OAuth | — |
| Brave Search | 1–2 | `snake_case` | Single-purpose | Title + URL + snippet | API key | — |
| Time | 2 | `snake_case` | Single-purpose | JSON | None | — |
| Memory | ~8 | `snake_case` | Graph-shaped | JSON | Local file / DB | — |
| Sequential Thinking | 1 | `snake_case` | Reasoning scratchpad | Structured trace | None | — |

The two outliers in tool count (Cloudflare 2, GitHub 56+) and naming (Atlassian `camelCase`, Notion `kebab-case`) are deliberate design statements, not accidents.

---

## Design disagreements

Where the exemplars contradict each other. When two production servers disagree, pick deliberately.

### Tool count — Cloudflare (2) vs GitHub (56) vs Atlassian Rovo (54)

Cloudflare bets that Codemode dominates for large APIs: 2 tools, 1,000 tokens, JS sandbox. GitHub and Atlassian bet on rich discrete surfaces with toolset filtering as the lever. Both philosophies have live production deployments. Vercel sits in the middle at 14 (cited in `transport-and-ops.md` § 18). Shopify Storefront lives at the other extreme (4 tools, workflow-consolidated). **Pick whichever matches your domain:** Codemode-friendly REST APIs → Cloudflare model; product platform with strong resource nouns → GitHub/Atlassian; narrow task surface → Shopify.

### Naming — `snake_case` (most) vs `camelCase` (Atlassian) vs `kebab-case` (Notion)

Atlassian Rovo is the major outlier and pushes further with dotted sub-actions (`bitbucketPullRequest.merge`). Notion uses `kebab-case`. Everyone else ships `snake_case`. The risk with non-`snake_case` is accidental collisions with client tooling that assumes `snake_case` identifiers. When breaking from `snake_case`, document loudly and avoid cross-tool name collisions.

### `structuredContent` adoption vs stringified JSON

The MCP spec added `structuredContent` precisely to stop vendors shipping JSON-in-text. Yet Supabase's README explicitly states "this server does not send `structuredContent`; Vercel AI SDK parses JSON from content text." Linear ships the same way. **Recommendation:** send `structuredContent` AND a human-readable text summary. Don't rely on JSON parsing from text — it breaks clients that respect the spec.

### Transport — Streamable HTTP only (HubSpot) vs + SSE retained (Intercom, Notion)

HubSpot rejects SSE outright: "Supporting SSE would have introduced load balancer and scaling complexity" ([product.hubspot.com, 2025-06-18](https://product.hubspot.com/blog/unlocking-deep-research-crm-connector-for-chatgpt)). Intercom and Notion keep a deprecated SSE endpoint alongside Streamable HTTP. **When operating behind an auto-scaling load balancer, HubSpot's reasoning applies.** When the workload needs to support legacy MCP clients, keep SSE and mark deprecated.

### Auth model — Stripe Restricted Keys vs HubSpot OAuth 2.1 + PKCE

Stripe delegates permissioning entirely to Restricted API Keys — no MCP-level scopes. HubSpot intersects OAuth app scopes with live user permissions on every call, adding a few dozen ms latency but enforcing current permissions. **Stripe's model is simpler for single-tenant; HubSpot's is correct for mutable-permission enterprises.**

### One-monolith MCP vs per-product mesh

Atlassian Rovo ships one server spanning Jira, Confluence, JSM, Bitbucket, and Compass — 54 tools, cross-product graph exposed via `getTeamworkGraphContext`. Cloudflare ships 16+ separate product servers, each at its own URL, each with its own auth scope. **Atlassian wins on cross-product correlation; Cloudflare wins on blast radius** (compromise of the DNS analytics server doesn't grant access to AI Gateway).

---

## Notable one-offs

Patterns no one else replicates. Useful for similar problems.

- **GitHub `github_support_docs_search`** — parameter description IS a behavioral policy: "Input from the user about the question they need answered. This is the latest raw unedited user message. You should ALWAYS leave the user message as it is, you should never modify it." Description-as-enforcement.
- **GitHub Insiders channel** — toggle via URL `/insiders` or header `X-MCP-Insiders: true`. Two activation vectors for the same flag.
- **Cloudflare product mesh** — 16+ separate product MCP servers (docs, bindings, builds, observability, radar, containers, browser rendering, logpush, AI Gateway, AI Search, audit logs, DNS analytics, DEX, CASB, GraphQL, Agents SDK), one URL each.
- **Notion-flavored Markdown** — introduced specifically for MCP because hierarchical JSON blocks were too token-heavy. The first vendor-specific Markdown variant for agent consumption.
- **Figma `generate_diagram`** — Mermaid → FigJam reverse bridge. No other vendor replicates the inverse direction (text → visual canvas).
- **Sentry `EMBEDDED_AGENT_PROVIDER`** — caller-supplied LLM key inside the MCP for NL search. Operationally fragile; cite as a pattern only when latency dominates.
- **Atlassian Rovo Teamwork Graph** (`getTeamworkGraphContext`, `getTeamworkGraphObject`) — beta cross-product entity walks. Returns Jira + Confluence + Bitbucket context for one object in a single call.
- **HubSpot `@ChirpTool` auto-discovery** — any internal RPC annotated `@ChirpTool` becomes an MCP tool. Service catalog drives the surface. Only safe because the gateway intersects scopes per call.

---

## What to copy (cross-cut patterns)

Five patterns to imitate, distilled from the 16 servers above.

1. **Intent-consolidated tools, never 1:1 OpenAPI.** Notion v1's post-mortem is the proof — 1:1 mapping fails. Linear, Stripe, HubSpot started intent-first; everyone else migrated to it. Always: ask "what does the user need to do?" not "what endpoints does the API expose?"
2. **Flat input schemas with inline-enum descriptions.** Linear's `priority: 0 = No priority, 1 = Urgent, 2 = High` pattern. Models read descriptions; surface the enum mapping there rather than in nested objects.
3. **Untrusted-data wrapping for any tool that returns user-supplied content.** Supabase's `<untrusted-data-${UUID}>...</untrusted-data-${UUID}>` with embedded ignore-instructions. Defends against prompt injection in returned data. Cross-link `security.md`.
4. **Tool-group selection at consent or via URL query params.** Sentry (OAuth consent), Supabase (URL params), GitHub (toolset deploy flag). Three layers, one purpose: shrink the post-connect catalog to the user's actual workflow.
5. **`whoami`-style identity tool.** Figma ships one. Operationally invaluable for debugging "why is this tool acting under the wrong account?" Always include in any auth-bearing MCP.

## What to avoid (cross-cut anti-patterns)

Five patterns to never repeat.

1. **1:1 OpenAPI → MCP auto-generation.** Notion v1, several others. Token cost dominates; agents fail.
2. **Manual `client_credentials` token paste in env.** PayPal — users curl for a Bearer token, paste into env, repeat when it expires. No refresh in the MCP. Always use OAuth 2.1 + PKCE with refresh-token rotation, or a first-party key-rotation UX (Stripe).
3. **Stringified JSON in `content[].text` with no `structuredContent`.** Linear ships this. Forces every consumer to JSON-parse text. Send `structuredContent` AND a human summary text block — give consumers both.
4. **Silent tool removal without `instructions` updates.** GitHub's `create_pull_request_with_copilot` (#1220). Users don't know what replaced it. Always announce in `instructions` and return structured errors pointing at replacements.
5. **Bloated tool catalogs with no consent-time filtering.** Linear's 17.3k-token catalog. Atlassian Rovo's 54-tool surface. Both work on frontier models; mid-tier models degrade. When catalog cost exceeds ~5% of context, ship a selector.

---

## Reading order — apply by archetype

| Your situation | Primary exemplar | Secondary | Why |
|---|---|---|---|
| Large REST API (50+ endpoints) with typed bindings | Cloudflare (Codemode) | Atlassian Rovo (toolset filtering) | Cloudflare's Codemode benchmark is the only published number at this scale (2,594 endpoints → ~1,000 tokens). |
| GraphQL backend | Linear | Notion v2 | Linear publicly documents the flattening strategy; Notion v2 shows the post-migration hybrid. |
| Enterprise multi-tenant with scoped permissions | HubSpot | Stripe | HubSpot's OAuth 2.1 + runtime permission intersection is the gold standard; Stripe's Restricted Keys are simpler when permissions are static. |
| Narrow task surface (cart, ticket, small workflow) | Shopify Storefront | Brave Search | Both prove small tool counts work when the state machine is small. |
| Productivity suite with cross-product entities | Atlassian Rovo | Notion v2 | Rovo's Teamwork Graph shows cross-product walks; Notion's `search` shows a single universal entry. |
| Developer tooling with CLI already present | Vercel | Figma | Vercel's `use_vercel_cli` meta-tool shows the "don't replace the CLI" pattern; Figma bridges IDE and design tool. |
| Database / data-plane | Postgres + Supabase patterns | Filesystem | Read-only default, untrusted-data wrapping, paginated streaming. |
| Long-lived agent memory | Memory MCP | Sequential Thinking | Externalized state via graph; reasoning scratchpad as separate primitive. |
| Code forge (git host) | GitHub | Atlassian Rovo Bitbucket | Enum-dispatcher + lockdown + insiders + description override are all copy-worthy. |

---

## Cross-cutting observations

### Which patterns converged across vendors

- **Remote / hosted over stdio.** Every major vendor except PayPal ships a hosted Streamable HTTP endpoint as the primary path. Stdio remains only for local-dev or CI.
- **OAuth over long-lived API keys.** Even Stripe — which still accepts API keys — defaults to OAuth for its hosted MCP.
- **Intent-consolidated tools over 1:1 OpenAPI wrappers.** Notion explicitly regretted v1's 1:1 generation; Linear never attempted it; HubSpot, Stripe, and Shopify Storefront started intent-first.
- **`snake_case` as the default identifier convention.** 14 of 16 use it; Atlassian Rovo (`camelCase`) and Notion (`kebab-case`) are the outliers.
- **Streamable HTTP `/mcp` endpoint, deprecating `/sse`.** HubSpot, Cloudflare, Intercom, Notion, Atlassian, Asana V2 all point at Streamable HTTP and mark SSE legacy or reject it outright.
- **Per-request ephemeral sessions.** HubSpot is explicit about it; most hosted servers implement it the same way to scale horizontally.

### Which patterns diverged

- **Tool count.** 1 (Sequential Thinking) → 2 (Cloudflare, Time) → 4 (Shopify) → 6 (Intercom) → 14 (Vercel / Zapier Agentic) → 15 (Figma) → 22 (Notion v2) → 23 (Linear) → 27 (Supabase) → 29 (PayPal) → 54 (Atlassian Rovo) → 56+ (GitHub).
- **Response shape.** JSON (Stripe, PayPal, Vercel, Intercom, Supabase); stringified JSON in text (Linear); Markdown (Atlassian, Notion); XML (Figma metadata); mixed XML + screenshots (Figma FigJam); untrusted-data-wrapped JSON (Supabase); JS result (Cloudflare Codemode).
- **`structuredContent` adoption.** Spec-recommended. Supabase explicitly opts out. Linear doesn't use it. Most others ambiguous.
- **Auth sophistication.** HubSpot (OAuth 2.1 + PKCE + runtime permission intersection) > Atlassian / Linear / Notion / Intercom (OAuth with DCR) > Stripe (OAuth + Restricted Keys) > Asana V2 (OAuth without DCR) > PayPal (manual `client_credentials` → Bearer paste).

### Open questions the exemplars haven't settled

- **`structuredContent` in practice.** No exemplar publishes a before/after cost comparison. Supabase's explicit opt-out suggests the ergonomics story isn't settled.
- **Tool-count ceilings.** Atlassian Rovo 54 and GitHub 56+ work with frontier models today. There is no published evidence on whether mid-tier models degrade gracefully at those counts.
- **Markdown body format standardization.** Notion ships "Notion-flavored Markdown," Atlassian ships Confluence-flavored Markdown, Figma ships React+Tailwind by default. No convergence on how to serialize rich content for agents.
- **Consent-time tool scoping.** Sentry does it via OAuth consent; Supabase via URL query params; GitHub via toolset flag at deploy. Three different layers for the same problem, no clear winner.
- **Embedded LLM inside the MCP.** Sentry does this for NL search. No other exemplar does. Unclear whether this is a broader pattern or a Sentry-specific workaround.

Re-cite, don't paraphrase. When pulling a claim from this file into a design doc or PR, keep the vendor attribution and the date — the MCP ecosystem moves fast enough that exemplars older than ~6 months may have shipped redesigns.

---

## Cross-references

- `tools.md` — design, descriptions, response shapes; the patterns these exemplars validate.
- `schema-design.md` — flat schemas and lowest-common-denominator JSON Schema, validated by Linear and HubSpot.
- `auth-identity.md` — OAuth 2.1, PKCE, DCR, per-call permission intersection (HubSpot reference).
- `security.md` — untrusted-data wrapping (Supabase reference), sanitization, audit.
- `transport-and-ops.md` — Streamable HTTP convergence (HubSpot rationale), per-platform constraints.
- `model-behavior.md` — when tool count, schema features, or response size collide with model limits.
- `client-compatibility.md` — which clients render which response shapes; per-client matrix.
- `registry-and-distribution.md` — where these servers publish and how their trust models compare.
- `../../common/exemplars.md` — cross-surface vendor comparison (production CLIs alongside MCP servers).
