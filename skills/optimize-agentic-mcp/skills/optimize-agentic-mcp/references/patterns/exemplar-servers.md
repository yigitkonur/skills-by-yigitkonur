# Exemplar MCP Server Analysis

Empirical survey of 16 production MCP servers shipped by major SaaS vendors in 2025–26. Sibling pattern files (`tool-design.md`, `schema-design.md`, `tool-responses.md`, `auth-identity.md`, `transport-and-ops.md`, `context-engineering.md`) describe *principles*; this file records *which vendors chose which tradeoff* so you can cite evidence when making design calls. Every claim below cites a repo, doc page, or engineering blog.

**Headline findings, 2026-04.** The ecosystem has converged on **remote/hosted transports over stdio**, **OAuth 2.1 + PKCE over long-lived API keys**, and **intent-consolidated tools over 1:1 OpenAPI wrappers**. It has diverged sharply on **tool count philosophy** (Cloudflare 2 → GitHub 56 → Atlassian Rovo 54) and **`structuredContent` adoption** (spec-recommended, but Supabase and Linear explicitly opt out in favor of JSON-in-text).

---

## 1. Per-server profiles

### GitHub — `github/github-mcp-server`

- **Source**: `github.com/github/github-mcp-server`, preview 2025-04-04.
- **Surface**: 56+ tools grouped by *toolsets* (`actions`, `issues`, `pull_requests`, `repos`, `code_security`, `dependabot`, `discussions`, `gists`, `notifications`, `orgs`, `projects`, `secret_protection`, `security_advisories`, `users`, `copilot`). Dynamic toolset discovery.
- **Naming**: `snake_case`, resource-prefixed.
- **Granularity**: Hybrid. Action-enum dispatchers for high-cardinality domains (`issue_read`, `issue_write`, `pull_request_read` taking a `method` arg), one-per-operation for the rest. This is a deliberate middle path between "verb per endpoint" (PayPal) and "2 tools total" (Cloudflare).
- **Unique**:
    - Description override at deploy time via `github-mcp-server-config.json`. Operators rewrite tool descriptions for their environment without forking the server.
    - Insiders channel via `/insiders` URL suffix *or* `X-MCP-Insiders: true` header — two activation vectors for the same flag.
    - Lockdown mode filters response content *per method* when the caller lacks push access — finer-grained than a binary read-only flag.
    - Dynamic tool discovery (beta, local only) gates heavy toolsets behind an initial discovery step.
    - Read-only mode as a first-class deploy flag.
- **Auth / transport**: OAuth (GitHub App/OAuth App) or PAT Bearer locally; OAuth remote. GHES supports PAT + OAuth. Remote at `api.githubcopilot.com/mcp/`, local stdio, Docker, GHE Cloud with data residency via `ghe.com`. No remote endpoint for GHES.
- **Most interesting tool**: `github_support_docs_search` — the *parameter* description is itself a behavioral policy: "Input from the user about the question they need answered. This is the latest raw unedited user message. You should ALWAYS leave the user message as it is, you should never modify it." Description-as-enforcement.
- **Known issue**: `create_pull_request_with_copilot` silently removed from remote (issue #1220, 2025-10-15, closed) — see Avoid #3.

### Linear

- **Source**: `linear.app/docs/mcp`; reverse-engineered tool dump at `blog.fiberplane.com/blog/mcp-server-analysis-linear/` (2025).
- **Surface**: 23 tools, remote-only. `list_issues`, `list_projects`, `list_teams`, `list_users`, `list_documents`, `list_cycles`, `list_comments`, `list_issue_labels`, `list_issue_statuses`, `list_project_labels`; `get_issue`, `get_project`, `get_team`, `get_user`, `get_document`, `get_issue_status`; `create_issue`, `create_project`, `create_comment`, `create_issue_label`; `update_issue`, `update_project`; `search_documentation`.
- **Naming / granularity**: `snake_case`; intent-consolidated, explicitly *not* a 1:1 GraphQL wrapper. Nested GraphQL filters collapsed into flat `assigneeId`, `teamId`, `stateId`. Magic value `"me"` accepted for assignee.
- **Schema**: Strict validation (UUID cursors, hex colors). Enum values hard-coded in parameter descriptions (e.g. priority `0 = No priority, 1 = Urgent, 2 = High, 3 = Normal, 4 = Low`). See sibling `schema-design.md` Pattern 3 on flat parameter shapes.
- **Response**: Stringified JSON in `content[].text`; no `structuredContent`. Tool catalog measures **17.3k tokens** after connect; context jumps roughly 61k → 78k.
- **Unique**: `search_documentation` tool has no matching API endpoint — a deliberate knowledge-layer bolt-on. This is the clearest signal Linear's team considers MCP a separate product surface, not an API mirror.
- **Auth / transport**: OAuth, hosted Streamable HTTP.

### Stripe

- **Source**: `github.com/stripe/agent-toolkit`.
- **Surface**: ~25 tools across Payments, Customers, Products, Prices, Invoices, Subscriptions, Refunds, Disputes, Balance, Payment Links, Coupons. `snake_case`, `--tools=` flag selects subsets at launch time.
- **Auth**: Remote OAuth at `https://mcp.stripe.com`; local via `npx -y @stripe/mcp --api-key=...`. **Restricted API Keys (`rk_*`) are the permissions surface** — there is no MCP-level scope system; Stripe reuses its existing fine-grained API key permissions. For Connect platforms, `context.account = "acct_123"` switches tenant per call.
- **Ecosystem sibling packages**: `@stripe/agent-toolkit` (framework helpers), `@stripe/ai-sdk` (Vercel AI SDK bindings), `@stripe/token-meter` (usage metering for LLM-driven Stripe actions).
- **Implication**: If you already have a fine-grained permissions primitive, reuse it as the MCP permissions surface rather than inventing a parallel scope system.

### Notion — `makenotion/notion-mcp-server` + hosted

- **Source**: `notion.com/blog/notions-hosted-mcp-server-an-inside-look` (2026 post-mortem).
- **Surface**: v1 = 19 tools (1:1 from OpenAPI, auto-generated); v2 = 22 tools (hybrid, AI-first rewrites + wrappers for gap coverage).
- **Naming**: **`kebab-case`** — unusual: `query-data-source`, `retrieve-a-data-source`, `update-a-data-source`, `create-a-data-source`, `list-data-source-templates`, `move-page`, `retrieve-a-database`. Hosted v2 adds agentic tools: `create-pages`, `update-page`, `search`, `create-comment`.
- **Response**: **"Notion-flavored Markdown"** for page content — introduced specifically because raw JSON blocks were too token-heavy.
- **Pipeline**: OpenAPI → Zod for schema generation; hand-written tools layered on top.
- **Auth / transport**: OAuth "one-click" shared public integration. Streamable HTTP primary + SSE fallback.
- **Unique tool**: `search` surfaces Notion workspace plus 10+ connected apps through one entry point — a Deep-Research-style tool inside a productivity MCP.
- **Post-mortem claim (verbatim)**: "1:1 API-to-tool mapping produced poor agent experiences, including high token use from hierarchical JSON block data." See Avoid #1.

### Sentry — `getsentry/sentry-mcp`

- **Source**: `docs.sentry.io/ai/mcp/`.
- **Surface**: ~10–15 tools incl. `search_events`, `search_issues`, `use_sentry`. Tool groups (Issues/Errors/Projects/Seer/discovery) selectable at **OAuth consent time**.
- **Unique**: NL search tools require caller-supplied `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` via `EMBEDDED_AGENT_PROVIDER` — an embedded LLM inside the MCP. `MCP_DISABLE_SKILLS=seer` disables cloud-only features. Claude Code plugin registers a `sentry-mcp` subagent.
- **Auth / transport**: Cloud = OAuth Streamable HTTP at `mcp.sentry.dev/mcp`; device-code for stdio. Self-hosted = access token. Session cached at `~/.sentry/mcp.json`, scoped by org/project.
- **Response discipline**: Sister `build_sim` pattern returns only `warnings | errors | status | next-step hints` — median 2.1 KB vs raw xcodebuild logs. See sibling `tool-responses.md`.

### Figma Dev Mode MCP

- **Source**: `developers.figma.com/docs/figma-mcp-server/tools-and-prompts/`; announcements `figma.com/blog/introducing-figma-mcp-server/` (2025-06-04 beta) and `figma.com/blog/design-systems-ai-mcp/` (2025-08-06).
- **Surface**: 15 tools (launched with 3). `snake_case`. Includes `generate_figma_design`, `get_design_context`, `get_variable_defs`, `get_code_connect_map`, `add_code_connect_map`, `get_screenshot`, `create_design_system_rules`, `get_metadata`, `get_figjam`, `generate_diagram`, `whoami`, `get_code_connect_suggestions`, `send_code_connect_mappings`, `use_figma`, `search_design_system`, `create_new_file`.
- **Unique**:
    - `generate_diagram` converts Mermaid syntax → FigJam — a **reverse-bridge** no other vendor replicates.
    - `create_design_system_rules` scans the caller's codebase and emits a rules file for agent guidance.
    - `use_figma` is a general create/edit/inspect tool.
    - `whoami` returns auth identity.
    - Docs explicitly mark tools "remote only" when hosted-only.
- **Response**: Code tools configurable (React + Tailwind default); `get_metadata` returns sparse XML; `get_figjam` returns XML + screenshots.
- **Auth / transport**: Figma desktop app session; local stdio with remote tools mixed in.
- **Design thesis (verbatim from launch blog)**: "Context > pixels; goal is alignment to design intent, not pixel-matching."

### Atlassian Rovo MCP Server

- **Source**: `support.atlassian.com/atlassian-rovo-mcp-server/docs/supported-tools/`. GA 2026-02-04.
- **Surface**: 54 tools — Jira (13), Confluence (11), JSM (4), Bitbucket Cloud (23), Rovo code/shared (4), Teamwork Graph (2 beta), Compass (12).
- **Naming**: **`camelCase`** — the major ecosystem outlier. `getJiraIssue`, `createConfluencePage`, `searchJiraIssuesUsingJql`.
- **Granularity**: Hybrid. Per-operation for Jira/Confluence/JSM. Bitbucket uses **nested dotted sub-action names**: `bitbucketPullRequest.approve`, `bitbucketRepoContent.branch.get`, `bitbucketPipeline.step.log` — hierarchy inside a single tool name.
- **Response**: Confluence body delivered as Markdown.
- **Unique**: Beta `fetch` + `search` universal tools Rovo-powered across products; `getTeamworkGraphContext` / `getTeamworkGraphObject` expose the cross-product entity graph.
- **Auth**: OAuth; users consent per AI client; admins allowlist clients.

### Cloudflare — `mcp-server-cloudflare` + product servers

- **Source**: `github.com/cloudflare/mcp-server-cloudflare`; `developers.cloudflare.com/agents/model-context-protocol/mcp-servers-for-cloudflare/`; `blog.cloudflare.com/model-context-protocol/` (2024-12-20 — earliest public MCP implementation from a major vendor).
- **Surface**: **2 tools total** for the Cloudflare API MCP — `search()` and `execute()`. Plus 16+ product-specific servers (docs, bindings, builds, observability, radar, containers, browser rendering, logpush, AI Gateway, AI Search, audit logs, DNS analytics, DEX, CASB, GraphQL, Agents SDK), each at its own URL with its own tools.
- **Codemode pattern**: `execute()` accepts JavaScript written against the typed OpenAPI spec, runs it in an isolated Dynamic Worker sandbox. The agent composes, Cloudflare runs.
- **Published benchmark**: 2,594 endpoints × full schemas = ~**1,170,000 tokens** for native MCP exposure. Required-params-only = 244,000. **Codemode = ~1,000 tokens.** The most concrete large-surface cost number publicly available in the ecosystem as of 2026.
- **JSDoc-typed methods**: Cloudflare's API surface exposes `camelCase` JS methods with JSDoc types; agents write idiomatic JS against them.
- **Auth / transport**: OAuth or API token. Streamable HTTP `/mcp`; deprecated `/sse`.
- **Implication**: Cloudflare argues the right abstraction for large APIs is a sandboxed runtime, not a flat tool list. Only relevant if your API has typed bindings the agent can call — not applicable to event-driven or stateful APIs.

### PayPal — `paypal/paypal-mcp-server`

- **Source**: `github.com/paypal/paypal-mcp-server`; blog `developer.paypal.com/community/blog/paypal-model-context-protocol/` (2025-04-02).
- **Surface**: 29 tools across Invoices, Orders, Refunds, Disputes, Shipment Tracking, Products, Subscription Plans, Subscriptions, Transactions. `snake_case`, one-per-operation.
- **Auth footgun**: Bearer access token generated via OAuth 2.0 `client_credentials` — users must manually `curl` to exchange `client_id`/`secret` for a token, then paste `PAYPAL_ACCESS_TOKEN` into env. Tokens expire ~32,400 s. **No built-in refresh in the MCP.** See Avoid #2.
- **Deploy**: `npx -y @paypal/mcp --tools=all`; sandbox/prod selected via `PAYPAL_ENVIRONMENT`.

### Shopify Storefront MCP

- **Source**: `shopify.dev/docs/apps/build/storefront-mcp/servers/storefront`.
- **Surface**: **4 tools only** — `search_shop_catalog`, `search_shop_policies_and_faqs`, `get_cart`, `update_cart`.
- **Unique**:
    - Per-tenant URL: `{shop}.myshopify.com/api/mcp`. The tenant is in the URL, not in a header or param.
    - **Zero authentication** for storefront flavor — consistent with Shopify's existing storefront API model.
    - `update_cart` creates a new cart if no `cart_id` passed — upsert semantics collapse "create cart" and "update cart" into one tool.
    - Explicit docs guardrail: "Use only the provided answer for policy responses; don't include external information." Policy answers are the narrowest, most brand-risk-sensitive surface; Shopify gates them via prose convention.
- **Implication**: extreme narrow-surface design. Four tools are enough because the workflow is "browse → add to cart → check policies." Not a generalizable pattern; only works for e-commerce storefronts where the state machine is small.

### Asana V2 MCP

- **Source**: `developers.asana.com/docs/integrating-with-asanas-mcp-server`. V1 shutdown 2026-05-11.
- **Endpoint**: `https://mcp.asana.com/v2/mcp` (no more `/sse`). Tool count not published — docs tell clients to call `tools/list`.
- **Auth**: OAuth 2.0 with **pre-registered app (`client_id` + `client_secret`)**. **DCR NOT supported.** Optional RFC 8707 `resource=https://mcp.asana.com/v2` param; `scope=default`; refresh tokens supported; 1 h access tokens.
- **Isolation quirk**: Tokens issued for MCP apps only work with the MCP server, **not with the REST API** — deliberate surface isolation.
- **Common error**: "Invalid scope(s) requested" is caused by including `scope` param at all.
- **Downstream impact**: Docker MCP Gateway (issue #479) is blocked on the no-DCR decision pending the V1 sunset. See Avoid #5.

### Supabase — `supabase-community/supabase-mcp`

- **Source**: `github.com/supabase-community/supabase-mcp`.
- **Surface**: 27 tools (README lists 32, feature-filtered). `snake_case`. Feature groups: `account`, `docs`, `database`, `debugging`, `development`, `functions`, `storage`, `branching`. Default disables `storage` "to reduce tool count."
- **Schema**: **Zod v4 with both `parameters` AND `outputSchema` on every tool.** Heavy use of MCP annotations: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`. See Copy #1.
- **URL-query-param config**: hosted at `mcp.supabase.com/mcp` accepts `?project_ref=`, `?read_only=true`, `?features=database,docs` — no client restart needed to change scope. See Copy #4.
- **Prompt-injection defense**: `execute_sql` wraps results in `<untrusted-data-${UUID}>…</untrusted-data-${UUID}>` with a generated UUID per call and an embedded instruction to ignore commands inside. Source: `packages/mcp-server-supabase/src/tools/database-operation-tools.ts`. See Copy #2 and sibling `security.md`.
- **Deliberate `structuredContent` omission**: README notes "This server does not send `structuredContent`; Vercel AI SDK parses JSON from content text." See Disagreement #3.
- **Client helper**: `createToolSchemas()` exposes the same feature/scope filter client-side for TS type safety.

### HubSpot Remote MCP

- **Source**: `developers.hubspot.com/mcp`; deep engineering blog `product.hubspot.com/blog/unlocking-deep-research-crm-connector-for-chatgpt` (2025-06-18). GA 2026-04-13.
- **Auth**: **OAuth 2.1 + PKCE required** — one of very few vendors explicit about 2.1. Refresh token rotation mandatory. Server intersects OAuth app scopes with live user permissions on every call (adds a few dozen ms).
- **Transport**: **Streamable HTTP, explicitly rejects SSE.** Blog: "SSE requires long-lived connections, harder for load balancers in auto-scaling environments." Because the Java MCP SDK didn't yet support Streamable HTTP at build time, HubSpot wrote a custom transport inside the SDK and committed to contribute it back upstream.
- **Tool surface**: Internal MCP Gateway auto-discovers RPC methods annotated `@ChirpTool` across microservices and auto-registers them as MCP tools — service-catalog-driven tool surface. New tools appear as soon as a team ships an annotated RPC.
- **Session model**: Ephemeral session per HTTP request — no state retained server-side. Pairs naturally with permission intersection on every call.
- **Query DSL**: single-string token-based, e.g. `object_type:contacts associated_companies:12345 limit:100 sort:lastmodifieddate:desc`. **No boolean OR, no nested expressions, no relative dates** — dropped intentionally because LLMs get them wrong. See Copy #6.
- **Safety posture**: read-only scopes + no sensitive properties by default. The intersection layer means even if an OAuth app grants more than the user has, runtime narrows to the user.

### Vercel MCP

- **Source**: `vercel.com/docs/agent-resources/vercel-mcp/tools`.
- **Surface**: **Exactly 14 tools**. `snake_case`. Includes `search_documentation`, `list_teams`, `list_projects`, `get_project`, `list_deployments`, `get_deployment`, `get_deployment_build_logs`, `get_runtime_logs`, `check_domain_availability_and_price`, `buy_domain`, `get_access_to_vercel_url`, `web_fetch_vercel_url`, `use_vercel_cli`, `deploy_to_vercel`.
- **Unique**:
    - `use_vercel_cli — Instructs the LLM to use Vercel CLI commands with --help flag for information.` A **meta-tool that does not execute**; it just nudges the agent to run the CLI. Counter-example to the "everything must be a tool call" assumption. See sibling `mcp-vs-cli.md`.
    - `get_access_to_vercel_url` creates a temporary shareable link for protected deployments — the MCP acts as an auth bridge for previews.
    - `web_fetch_vercel_url` pairs with the access tool so agents can fetch behind-auth preview content without separate credential plumbing.

### Intercom — `mcp.intercom.com`

- **Source**: `developers.intercom.com/docs/guides/mcp`.
- **Surface**: **6 tools** — universal `search`, `fetch` + direct `search_conversations`, `get_conversation`, `search_contacts`, `get_contact`.
- **Pattern**: Explicit universal + direct pair. `search` takes a DSL (`object_type:conversations`); `fetch` retrieves a specific resource; direct tools offer richer filters. See Copy #7.
- **Response**: Pagination with `total_in_page`, `results`, `pages`, `_note`, cursor via `starting_after`. Up to 150 items/page.
- **Auth / transport**: OAuth (recommended, browser) or Bearer. Streamable HTTP `/mcp`; SSE `/sse` deprecated but retained.
- **Status**: US workspaces only, 2026-04.

### Zapier — `zapier/zapier-mcp`

- **Source**: `github.com/zapier/zapier-mcp`.
- **Two-mode surface** (unique across exemplars):
    - **Classic mode**: user enables specific actions; each enabled action becomes a dedicated tool with typed parameters (e.g. `gmail_send_email` with `to/subject/body`). Shaped like the user's workflow.
    - **Agentic mode (beta)**: 14 static meta-tools discover/enable/disable/execute actions dynamically. Shaped like a platform API.
- **Rationale**: users pick a "focused handful" (Classic) when the workflow is known, or "broad across the stack" (Agentic) when the agent must explore. Exposes 8,000+ apps and 40,000+ actions.
- **Auth**: API key (personal) or OAuth (multi-user).
- **Implication**: Zapier is the only exemplar to publicly concede one surface doesn't fit both modes of use; everyone else picks one and defends it.

---

## 2. Head-to-head comparison

| Server | Tools | Naming | Granularity | Schema | Response | Auth | Transport | `outputSchema` + `structuredContent` |
|---|---|---|---|---|---|---|---|---|
| GitHub | 56+ | `snake_case` + enum verbs | Hybrid: enum dispatchers for high-cardinality | Flat; override via config file | Text, some JSON | OAuth / PAT Bearer | Streamable HTTP | No |
| Linear | 23 | `snake_case` | Intent-consolidated | Flat | Stringified JSON in text | OAuth | Streamable HTTP | No |
| Stripe | ~25 | `snake_case` | Intent-consolidated | Flat | JSON | OAuth / Restricted API Key | Streamable HTTP | — |
| Notion | 22 (v2) | `kebab-case` | Hybrid: AI-first + API wrappers | Zod from OpenAPI | Notion-flavored Markdown | OAuth | Streamable HTTP + SSE | — |
| Sentry | ~10–15 | `snake_case` | Intent + embedded LLM | Flat | Text | OAuth / Token | Streamable HTTP + stdio | — |
| Figma | 15 | `snake_case` | Per-capability | Flat | Text / XML / React+TW / screenshots | Desktop app session | Local stdio → remote | — |
| Atlassian Rovo | 54 | **`camelCase`** + dotted sub-actions | Hybrid: flat + nested | Flat | Markdown for pages | OAuth | Streamable HTTP | — |
| Cloudflare API | 2 | `camelCase` in JS code | Codemode (JS sandbox) | JS runs against OpenAPI | JS result | OAuth / API token | Streamable HTTP | — |
| PayPal | 29 | `snake_case` | One-per-operation | Flat | JSON | OAuth `client_credentials` → Bearer | stdio / npx | — |
| Shopify Storefront | 4 | `snake_case` | Workflow-consolidated | JSON-RPC 2.0 | JSON | **None** | HTTP | — |
| Asana V2 | `tools/list` | — | — | — | — | OAuth (no DCR) | Streamable HTTP | — |
| Supabase | 27 | `snake_case` | Feature-grouped | **Zod v4 in + out** | JSON + `<untrusted-data-UUID>` wrapping | OAuth / PAT | Streamable HTTP | **`outputSchema` yes, `structuredContent` NO (explicit)** |
| HubSpot | auto-discovered | — | Per-RPC via `@ChirpTool` | Zod | JSON | **OAuth 2.1 + PKCE** | Streamable HTTP (custom impl) | — |
| Vercel | 14 | `snake_case` | Flat per-operation | Flat | JSON | OAuth | Streamable HTTP | — |
| Intercom | 6 | `snake_case` | Universal (`search`/`fetch`) + direct | Flat + DSL | JSON with pagination | OAuth / Bearer | Streamable HTTP | — |
| Zapier Agentic | 14 meta | `snake_case` | Dynamic action discovery | Flat | JSON | API key / OAuth | Streamable HTTP | — |

---

## 3. Copy-this patterns

### Copy 1: Supabase — tool annotations + input AND output Zod schemas on every tool

Supabase declares `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` on every tool, alongside Zod `parameters` and `outputSchema`. This lets clients precompute which tools need consent gating and which are safe for batch execution. Source: `packages/mcp-server-supabase/src/tools/database-operation-tools.ts` (GitHub, 2025). Pair with sibling `schema-design.md` and `prompt-gates.md`.

### Copy 2: Supabase — prompt-injection wrapping of untrusted tool output

`execute_sql` wraps returned rows in `<untrusted-data-${UUID}>…</untrusted-data-${UUID}>`, where the UUID is freshly generated per call, plus an embedded instruction telling the agent to ignore any commands inside. This defends against SQL result rows that contain injected prompts. Same source file. Cross-reference sibling `security.md` and `threat-catalog.md`.

### Copy 3: Cloudflare — Codemode for large API surfaces

For a 2,594-endpoint API, Cloudflare published **1,170,000 tokens native → ~1,000 tokens via Codemode** (`search()` + `execute()`), running typed JS against the OpenAPI spec in a Dynamic Worker sandbox. Source: `developers.cloudflare.com/agents/model-context-protocol/mcp-servers-for-cloudflare/`. Use this when the API has > ~50 endpoints. Cross-reference sibling `tool-design.md` and `progressive-discovery.md`.

### Copy 4: Supabase — URL-query-param server configuration

`mcp.supabase.com/mcp?project_ref=…&read_only=true&features=database,docs` reconfigures tool surface without restarting the MCP client. Adopt for any multi-tenant hosted MCP. See sibling `transport-and-ops.md`.

### Copy 5: Linear — flatten nested filters + inline-enum descriptions

Linear collapses GraphQL's nested filter objects into flat `assigneeId`, `teamId`, `stateId` and documents enum values inside the description string, e.g. `"Priority: 0 = No priority, 1 = Urgent, 2 = High, 3 = Normal, 4 = Low"`. Source: `blog.fiberplane.com/blog/mcp-server-analysis-linear/` (2025). Cross-reference sibling `schema-design.md` Pattern 3.

### Copy 6: HubSpot — restricted query DSL for LLM reliability

Single-string `key:value` tokens: `object_type:contacts associated_companies:12345 limit:100 sort:lastmodifieddate:desc`. **Explicitly bans boolean OR, nested expressions, and relative dates** because LLMs get them wrong. Source: `product.hubspot.com/blog/unlocking-deep-research-crm-connector-for-chatgpt` (2025-06-18). Cross-reference sibling `model-behavior.md`.

### Copy 7: Intercom — universal `search`/`fetch` + direct-tool pair

Pair a DSL-driven `search`/`fetch` pair for Deep-Research-style broad browsing with direct per-resource tools (`search_conversations`, `get_conversation`) for precise filters. Agents that know the domain pick the direct tool; agents exploring pick the universal pair. Source: `developers.intercom.com/docs/guides/mcp`. See sibling `tool-design.md` and `progressive-discovery.md`.

### Copy 8: GitHub — description override at deploy time

`github-mcp-server-config.json` lets operators rewrite tool descriptions without forking. Ship this any time enterprises will tune tool behavior per environment (e.g. "in this org, `issue_write` is read-only"). Source: `github.com/github/github-mcp-server`.

### Copy 9: GitHub — lockdown mode filters response content per method

When the author lacks push access, lockdown filters the response of specific methods (not just hides the whole tool). More granular than a binary read-only flag. Source: `github.com/github/github-mcp-server`.

### Copy 10: Figma — server-side repo introspection via `create_design_system_rules`

Scans the caller's codebase from the MCP server side and emits a rules file the agent can consume. Inverts the usual "agent reads repo" flow: the MCP knows its own domain better and packages that knowledge for the calling agent. Source: `developers.figma.com/docs/figma-mcp-server/tools-and-prompts/`. See sibling `context-engineering.md`.

### Copy 11: Sentry — tool-group selection at OAuth consent

The user picks which tool groups (Issues / Errors / Projects / Seer) are exposed during the OAuth consent flow, shrinking the post-connect tool catalog per user rather than per tenant. Source: `docs.sentry.io/ai/mcp/`. See sibling `auth-identity.md`.

### Copy 12: HubSpot — ephemeral per-request sessions

No server-side session state. Each HTTP request re-runs auth, permission intersection, and execution. Scales horizontally, fails safe (a crashed worker doesn't lose session state), pairs with OAuth 2.1 refresh-token rotation. Source: `product.hubspot.com/blog/unlocking-deep-research-crm-connector-for-chatgpt` (2025-06-18). See sibling `session-and-state.md`.

### Copy 13: Atlassian Rovo — cross-product Teamwork Graph tools

`getTeamworkGraphContext` and `getTeamworkGraphObject` (beta) return entity context that spans Jira + Confluence + Bitbucket for a single object. When your product has multiple surfaces referring to the same entity, expose the graph-walk instead of forcing the agent to join three tool calls. Source: `support.atlassian.com/atlassian-rovo-mcp-server/docs/supported-tools/`.

---

## 4. Avoid-this anti-patterns

### Avoid 1: Notion v1 — 1:1 OpenAPI → MCP generation

Notion's own post-mortem (`notion.com/blog/notions-hosted-mcp-server-an-inside-look`, 2026): "1:1 API-to-tool mapping produced poor agent experiences, including high token use from hierarchical JSON block data." v2 added hand-written AI-first tools *and* introduced Notion-flavored Markdown because JSON blocks burned tokens. If you're shipping v1, stop — every exemplar that started API-shaped migrated away from it.

### Avoid 2: PayPal — manual OAuth `client_credentials` flow in MCP config

PayPal ships an MCP that expects users to cURL for a Bearer token with ~32,400 s lifetime, paste it into `PAYPAL_ACCESS_TOKEN`, and re-run cURL when it expires. No built-in refresh. Source: `github.com/paypal/paypal-mcp-server/blob/main/README.md`. Prefer OAuth 2.1 + PKCE with refresh-token rotation (HubSpot) or first-party key rotation UX (Stripe Restricted Keys). See sibling `auth-identity.md`.

### Avoid 3: GitHub — silent tool removal without updating `instructions`

`create_pull_request_with_copilot` was removed from the remote surface with no deprecation note in the server `instructions` block; issue #1220 (2025-10-15, closed) shows the resulting user confusion. When removing or gating tools, announce it in the server `instructions` and return structured errors pointing at the replacement. See sibling `advanced-protocol.md`.

### Avoid 4: Linear — stringified JSON in `content[].text` + noise fields

Linear serializes tool responses as JSON stringified inside a text block (no `structuredContent`) *and* includes noise fields (`createdAt`, `updatedAt`, `avatarUrl`, `isAdmin`, `isGuest`) in `list_users` even though agents almost only want assignment data. Result: 17.3k-token tool catalog + bloated per-call responses. Source: `blog.fiberplane.com/blog/mcp-server-analysis-linear/`. Cross-reference sibling `tool-responses.md` and `context-engineering.md`.

### Avoid 5: Asana V2 — OAuth without DCR and workspace-scoping break

V2 requires pre-registered `client_id` + `client_secret` per integrator and does not support Dynamic Client Registration; tokens issued for MCP apps don't work with the REST API. Docker MCP Gateway is blocked on the product decision (`github.com/docker/mcp-gateway/issues/479`) pending the 2026-05-11 V1 sunset. Supporting DCR is table-stakes for gateway integrations in 2026. See sibling `auth-identity.md`.

### Avoid 6: PayPal / similar — token-only deploy with no sandbox/prod toggle in the tool surface

PayPal toggles sandbox/prod with `PAYPAL_ENVIRONMENT` env var alone. The LLM cannot see which environment it is acting against. Either expose a `whoami`-style tool (Figma does this) or include the environment in every response payload. See sibling `session-and-state.md`.

### Avoid 7: Shopify Storefront — zero-auth docs guardrail via prose alone

Shopify Storefront has no authentication and embeds the guardrail "Use only the provided answer for policy responses; don't include external information." in docs rather than in tool descriptions or response envelopes. A compliant agent may obey; a sloppy one will not. When the only enforcement is docs, be explicit about that risk to operators and consider moving the guardrail into the response payload (e.g. a `policy_enforcement: strict` field the agent is trained to respect).

### Avoid 8: Linear — no `structuredContent` *and* catalog eats 17.3k tokens

Not just the JSON-in-text problem (Avoid #4). The full Linear catalog on connect is 17.3k tokens, bumping a session from 61k → 78k before the agent runs its first tool. When catalog token cost exceeds ~5% of the agent's context window, the server should offer a tool-subset selector at connect time (Sentry does this, Supabase does this via URL query params). Linear currently does not.

---

## 5. Design disagreements

### Disagreement 1: Tool count — Cloudflare (2) vs GitHub (56) vs Atlassian Rovo (54)

Cloudflare bets that Codemode dominates for large APIs: 2 tools, 1,000 tokens, JS sandbox. GitHub and Atlassian bet on rich discrete surfaces with toolset filtering as the lever. Both philosophies have live production deployments as of 2026-04. Vercel sits in the middle at exactly 14. Shopify Storefront lives at the other extreme (4 tools, workflow-consolidated). Copy whichever matches your domain: Codemode-friendly REST APIs → Cloudflare; product-platform with strong resource nouns → GitHub/Atlassian; narrow task surface → Shopify. See sibling `tool-design.md`.

### Disagreement 2: Naming — `snake_case` (almost everyone) vs `camelCase` (Atlassian Rovo)

Atlassian Rovo is the major outlier and pushes further with dotted sub-actions (`bitbucketPullRequest.merge`, `bitbucketRepoContent.branch.get`). Notion uses `kebab-case`. Everyone else ships `snake_case`. The risk with non-`snake_case` is accidental collisions with client tooling that assumes `snake_case` identifiers. If you break from `snake_case`, document it and avoid cross-tool name collisions. See sibling `schema-design.md`.

### Disagreement 3: `structuredContent` adoption vs stringified JSON

The MCP spec added `structuredContent` precisely to stop vendors shipping JSON-in-text. Yet Supabase's README explicitly states "this server does not send `structuredContent`; Vercel AI SDK parses JSON from content text." Linear ships the same way. Recommendation: send `structuredContent` *and* a human-readable text summary. Do not rely on JSON parsing from text — it breaks clients that respect the spec. See sibling `tool-responses.md`.

### Disagreement 4: Transport — Streamable HTTP only (HubSpot) vs + SSE fallback retained (Intercom, Notion)

HubSpot rejects SSE outright: "Supporting SSE would have introduced load balancer and scaling complexity" (`product.hubspot.com/blog/...`, 2025-06-18). Intercom and Notion keep a deprecated SSE endpoint alongside Streamable HTTP for backward compatibility. If you operate behind an auto-scaling load balancer, HubSpot's reasoning applies — don't ship SSE. If you need to support legacy MCP clients, keep SSE and mark it deprecated in docs. See sibling `transport-and-ops.md`.

### Disagreement 5: Auth model — Stripe Restricted Keys vs HubSpot OAuth 2.1 + PKCE with per-call permission intersection

Stripe delegates permissioning entirely to Restricted API Keys — no MCP-level scopes. HubSpot intersects OAuth app scopes with live user permissions on every call, adding a few dozen ms latency but enforcing current permissions. Stripe's model is simpler for single-tenant; HubSpot's is correct for mutable-permission enterprises. See sibling `auth-identity.md`.

---

### Disagreement 6: One-monolith MCP vs per-product mesh

Atlassian Rovo ships one server spanning Jira, Confluence, JSM, Bitbucket, Rovo code/shared, Teamwork Graph, and Compass — 54 tools, cross-product graph exposed via `getTeamworkGraphContext`. Cloudflare ships 16+ separate product servers, each at its own URL, each with its own auth scope. Atlassian wins on cross-product correlation (one tool call returns linked Jira + Confluence content); Cloudflare wins on blast radius (compromise of the DNS analytics server doesn't grant access to AI Gateway). Pick based on whether your product surfaces share a graph or are genuinely independent.

### Disagreement 7: Static tool list vs auto-registered tool list

HubSpot auto-registers any microservice RPC marked `@ChirpTool`. GitHub, Linear, and Vercel maintain hand-curated tool lists. Auto-registration lets the MCP scale with the org without central coordination; hand-curation forces a deliberate API design review per tool. HubSpot's approach only works because the Gateway intersects scopes per call — otherwise auto-registered tools would sprawl permissions.

---

## 6. Notable one-offs

- **GitHub `github_support_docs_search`** — the parameter description is itself a behavioral policy: *"Input from the user about the question they need answered. This is the latest raw unedited user message. You should ALWAYS leave the user message as it is, you should never modify it."* Description-as-enforcement. See sibling `tool-descriptions.md`.
- **GitHub Insiders channel** — toggle via URL `/insiders` or header `X-MCP-Insiders: true`. Two activation vectors for the same flag.
- **Cloudflare product mesh** — 16+ separate product MCP servers (docs, bindings, builds, observability, radar, containers, browser rendering, logpush, AI Gateway, AI Search, audit logs, DNS analytics, DEX, CASB, GraphQL, Agents SDK), one URL each. Per-product server mesh rather than a monolith.
- **HubSpot `@ChirpTool` auto-discovery** — any internal RPC annotated `@ChirpTool` is auto-registered as an MCP tool. Service catalog drives the tool surface.
- **Supabase `createToolSchemas()`** — client-side helper mirrors the URL filter for TS type safety.
- **Notion-flavored Markdown** — introduced specifically for MCP, because hierarchical JSON blocks were too token-heavy.
- **Figma `generate_diagram`** — Mermaid → FigJam reverse bridge, no other vendor replicates.
- **Sentry `EMBEDDED_AGENT_PROVIDER`** — requires caller-supplied LLM key; embedded LLM inside the MCP for NL search.
- **Zapier dual-mode (Classic per-action + Agentic meta)** — no other vendor exposes both modes in one server.
- **Shopify Storefront auth** — zero authentication, per-tenant URL pattern; policy answers explicitly gated by docs ("use only the provided answer").
- **Asana V2 RFC 8707 `resource` param** — tokens work *only* with the MCP server, not with the REST API; deliberate surface isolation.
- **HubSpot custom Streamable HTTP transport** — Java MCP SDK lacked support at build time; HubSpot wrote custom transport and committed to contribute it back upstream.

---

## 7. Cross-cutting observations

### 7.1 Which patterns converged across 16 vendors

- **Remote / hosted over stdio.** Every major vendor except PayPal ships a hosted Streamable HTTP endpoint as the primary path. Stdio remains only for local-dev or CI.
- **OAuth over long-lived API keys.** Even Stripe — which still accepts API keys — defaults to OAuth for its hosted MCP.
- **Intent-consolidated tools over 1:1 OpenAPI wrappers.** Notion explicitly regretted v1's 1:1 generation; Linear never attempted it; HubSpot, Stripe, and Shopify Storefront started intent-first.
- **`snake_case` as the default identifier convention.** 14 of 16 use it; Atlassian Rovo (`camelCase`) and Notion (`kebab-case`) are the outliers.
- **Streamable HTTP `/mcp` endpoint, deprecating `/sse`.** HubSpot, Cloudflare, Intercom, Notion, Atlassian, Asana V2 all point at Streamable HTTP and mark SSE legacy or reject it outright.
- **Per-request ephemeral sessions.** HubSpot is explicit about it; most hosted servers implement it the same way to scale horizontally.

### 7.2 Which patterns diverged

- **Tool count.** 2 (Cloudflare) → 4 (Shopify) → 6 (Intercom) → 14 (Vercel / Zapier Agentic) → 15 (Figma) → 22 (Notion v2) → 23 (Linear) → 27 (Supabase) → 29 (PayPal) → 54 (Atlassian Rovo) → 56+ (GitHub).
- **Response shape.** JSON (Stripe, PayPal, Vercel, Intercom, Supabase); stringified JSON in text (Linear); Markdown (Atlassian, Notion); XML (Figma metadata); mixed XML + screenshots (Figma FigJam); untrusted-data-wrapped JSON (Supabase); JS result (Cloudflare Codemode).
- **`structuredContent` adoption.** Spec-recommended. Supabase explicitly opts out. Linear doesn't use it. Most others ambiguous because their README doesn't confirm either way.
- **Auth sophistication.** HubSpot (OAuth 2.1 + PKCE + runtime permission intersection) > Atlassian / Linear / Notion / Intercom (OAuth with DCR) > Stripe (OAuth + Restricted Keys) > Asana V2 (OAuth without DCR) > PayPal (manual `client_credentials` → Bearer paste).

### 7.3 Reading order for applying these findings

1. If you're starting a new MCP: read Copy #3 (Cloudflare Codemode) first if your API has > ~50 endpoints; otherwise read Copy #5 (Linear flattening) and Copy #7 (Intercom universal + direct pair).
2. If you're hardening an existing MCP: apply Copy #1–#2 (Supabase annotations + prompt-injection wrapping) and Copy #6 (HubSpot DSL constraints) before anything else.
3. If you're shipping remote/hosted: apply Disagreement #4 (Streamable HTTP only, per HubSpot) and Copy #4 (URL-query-param config).
4. If you're tempted to generate tools from OpenAPI: read Avoid #1 (Notion v1 post-mortem) first.
5. For auth: HubSpot > Stripe > PayPal in that order of sophistication. Don't ship PayPal-style manual `client_credentials` in 2026.
6. For enterprise deploy flexibility: combine GitHub's deploy-time description override (Copy #8) with Supabase's URL-query-param config (Copy #4) and GitHub's per-method lockdown (Copy #9).

### 7.4 Which exemplar to study for your domain

| Your situation | Primary exemplar to copy | Secondary | Why |
|---|---|---|---|
| Large REST API (50+ endpoints) with typed bindings | Cloudflare (Codemode) | Atlassian Rovo (toolset filtering) | Cloudflare's Codemode benchmark is the only published number at this scale. |
| GraphQL backend | Linear | Notion v2 | Linear publicly documents the flattening strategy; Notion v2 shows the post-migration hybrid. |
| Enterprise multi-tenant with scoped permissions | HubSpot | Stripe | HubSpot's OAuth 2.1 + runtime permission intersection is the gold standard; Stripe's Restricted Keys are simpler and work when permissions are static. |
| Narrow task surface (cart, ticket, small workflow) | Shopify Storefront | Intercom | Both prove small tool counts work when the state machine is small. |
| Productivity suite with cross-product entities | Atlassian Rovo | Notion v2 | Rovo's Teamwork Graph shows cross-product walks; Notion's `search` shows a single universal entry. |
| Developer tooling with CLI already present | Vercel | Figma | Vercel's `use_vercel_cli` meta-tool shows the "don't replace the CLI" pattern; Figma bridges IDE and design tool. |
| Platform with 10,000+ potential actions | Zapier | Cloudflare | Zapier's two-mode design is the only public acknowledgement that dynamic meta-tools vs static tools is a user-choice dimension. |
| Observability / incident tooling | Sentry | — | Sentry's tool-group selection at OAuth consent + embedded LLM for NL search are both rare. |
| Billing / financial API | Stripe | — | Stripe's Restricted Keys + Connect account context are the reference implementation. |
| Code forge (git host) | GitHub | Atlassian Rovo Bitbucket | GitHub's enum-dispatcher + lockdown + insiders + description override are all copy-worthy. |

### 7.5 Open questions the exemplars haven't settled

- **`structuredContent` in practice.** No exemplar publishes a before/after cost comparison for `structuredContent` vs stringified JSON. Supabase's explicit opt-out suggests the ergonomics story isn't settled.
- **DCR adoption.** Asana V2 rejects it; most others accept it. Gateways like Docker MCP Gateway are stuck waiting.
- **Meta-tools vs dedicated tools.** Zapier ships both modes and lets the user choose. No vendor publishes comparative telemetry on which mode wins for which task.
- **Embedded LLM inside the MCP.** Sentry does this (NL search). No other exemplar does. Unclear whether this is a broader pattern or a Sentry-specific workaround.
- **Tool-count ceilings.** Atlassian Rovo 54 and GitHub 56+ work with frontier models today. There is no published evidence on whether mid-tier models degrade gracefully at those counts.
- **Markdown body format standardization.** Notion ships "Notion-flavored Markdown", Atlassian ships Confluence-flavored Markdown, Figma ships React+Tailwind by default. No convergence on how to serialize rich content for agents.
- **Consent-time tool scoping.** Sentry does it via OAuth consent; Supabase via URL query params; GitHub via toolset flag at deploy. Three different layers for the same problem.

### 7.6 How this file relates to its siblings

- **Principles** → sibling files (`tool-design.md`, `schema-design.md`, `tool-responses.md`, `auth-identity.md`, `transport-and-ops.md`, `context-engineering.md`, `security.md`).
- **Evidence** → this file. When a sibling recommends a pattern, look here for which vendor validated it in production and how.
- **Counter-examples** → the Avoid section above. When a sibling principle has public failure data (e.g. Notion v1, PayPal auth), it's cited here.
- **Disagreements** → § 5. When siblings present a principle as settled, but exemplars disagree, this file records the disagreement so you can pick deliberately rather than by default.
- **Dates**: every claim citing a specific doc, blog, or repo includes the YYYY-MM-DD (or YYYY-MM) it was published or observed. Recompute staleness when reusing — the MCP ecosystem is moving fast enough that exemplars older than 6 months may have shipped redesigns.
- **Re-cite, don't paraphrase**. When you pull a claim from this file into a design doc or PR, keep the vendor attribution and the date. Unattributed exemplar claims age poorly.
