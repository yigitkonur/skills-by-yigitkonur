# exemplars — production CLIs and MCP servers, evidence-based

Real-world tools that get this right. Patterns alone are insufficient — the exemplars below show how production teams trade off the principles in this skill, with citation. When your design choice has precedent, name it. When two precedents disagree, name them both. Source: `optimize-agentic-cli/references/examples.md` (CLI audits) and `optimize-agentic-mcp/references/patterns/exemplar-servers.md` (16-server survey).

## CLI exemplars

### GitHub CLI (`gh`)

Production CLI from GitHub for repos, PRs, issues, runs, and the API. Universal `--json` flag across most commands; `--jq` for inline filtering.

What it does well:

- `--json <fields>` is universal: `gh repo view --json name,description` returns a clean JSON object the agent parses without thinking.
- `--jq <expr>` for in-line filtering reduces parser logic on the agent side: `gh pr list --json title,number --jq '.[] | select(.number > 100)'`.
- `--template` for custom output formatting; useful when agents want tabular slicing.
- `gh run watch` streams workflow status — though the output is human-readable text, not NDJSON.
- Stdout/stderr separation is clean: `gh repo view --json name 2> /dev/null` produces pure JSON.

What it does poorly:

- Exit codes are essentially binary: 0 for success, 1 for everything else. Not-found, auth-fail, rate-limit, conflict — all collapse to exit 1. Agent harnesses can't classify.
- API errors (`gh api`) return structured `{"message":"Not Found"}`, but plain CLI errors are stderr text only — no envelope.
- No `schema_version` on JSON outputs; field renames between versions break agents that learned the v1 shape.
- No NDJSON streaming for long-running operations (`gh run watch` ships text).

Score in the 5-check audit: stdout/stderr separation, non-interactive, JSON output — pass; exit codes, structured errors — partial. Net: ~86% (mostly ready). Source: `optimize-agentic-cli/references/examples.md` Section 11.

### `aws` CLI (v2)

Amazon's CLI for the AWS API. JSON is the default output; `--query` provides JMESPath filtering.

What it does well:

- JSON is the default; you have to pass `--output text` to get human-readable. Agents hit JSON without remembering a flag.
- `--query <jmespath>` for in-line filtering: `aws s3api list-buckets --query 'Buckets[].Name'`.
- Structured error responses on most commands: `aws s3 ls s3://nonexistent` returns a JSON error object, not freeform text.
- Pagination with `--max-items` and continuation tokens.
- `--dry-run` on EC2 mutations.

What it does poorly:

- Exit codes are not semantic — 1, 2, 252, 253, 254, 255 across different failure modes. The taxonomy is documented but agents have to learn the AWS-specific table.
- Long operations (waiters) emit human-readable progress, not NDJSON.
- Some commands print to stderr even with `--output json`; harnesses occasionally see noise.

Score: ~88% (agent-ready). The clean default-JSON behavior puts it above `gh` on output discipline; the exit-code muddle keeps it below a hypothetical perfect.

### `kubectl`

Kubernetes' CLI for cluster operations. Multiple output formats (`-o json`, `-o yaml`, `-o jsonpath`, `-o name`).

What it does well:

- `-o json` and `-o yaml` for any read; `-o jsonpath='{.items[*].metadata.name}'` for in-line projection.
- `--field-selector` and `--label-selector` reduce server-side filtering.
- `--dry-run=client` and `--dry-run=server` for previewing changes.
- Explicit non-interactive: most commands don't prompt; `--force` exists for safeguard overrides.

What it does poorly:

- Errors are unstructured text on stderr. `kubectl get pod nonexistent` prints `Error from server (NotFound): pods "nonexistent" not found` — no JSON envelope, no exit-code taxonomy beyond binary.
- No inline filter (`--jq` / `--query` equivalent for CLI-side reduction); agents pipe through `jq` themselves.
- Output across multiple resources can be ambiguous when one fails: silent partial success.

Score: ~71% (mostly ready). The format flexibility is a strength; the unstructured errors are the gap.

### `op` (1Password CLI) and `bw` (Bitwarden CLI)

Both pass-style CLIs share a clean pattern: `--format=json` is the default for the `--session` mode; auth via env var or session token; deterministic exit codes.

What `op` does well:

- `op item get <id> --format=json` returns a stable envelope; field names are `snake_case` and stable across versions.
- Session token via `OP_SESSION_<account>` env var; no interactive prompts under headless auth.
- `op signin --raw` returns just the token; agent harnesses pipe it directly.

What `bw` does well:

- `BW_SESSION` env var carries the unlocked session; no daemon, no prompts.
- `bw list items --search "github" --format=json` returns a JSON array; agents parse without ceremony.

What both do poorly:

- Exit codes are 0/1 only; no taxonomy distinguishing "vault locked" (auth) from "item not found" (not_found).
- Error envelopes on stdout exist but are inconsistent across subcommands.

These are good baselines for vault-style CLIs. The headless auth model (env-var session token) is worth copying.

### `linear-cli` and `stripe` CLI

Both ship `--json` flags and OAuth-based device-code login flows. `stripe` in particular leans into structured output: `stripe customers list --limit=10 -o json` returns an envelope with pagination metadata. `stripe events tail` ships NDJSON for real-time event watching.

What `stripe` does well:

- NDJSON streaming for long-running tools (`stripe events tail` flushes one event per line).
- Test-mode and live-mode separation is explicit (`--test-mode` flag); the agent always knows the environment.
- OAuth device-code login via `stripe login` — works headless after a single browser dance.

The pattern to copy from these CLIs: ship `--json` AND a streaming variant for long-lived workflows; honor headless auth via env vars; keep test-vs-prod mode visible in the envelope.

### Cross-CLI comparison

| CLI | --json universal | NDJSON stream | Semantic exit codes | Structured errors | Headless auth |
|---|---|---|---|---|---|
| `gh` | yes | no | binary (0/1) | partial (`gh api` only) | env var (PAT) |
| `aws` | default | partial | non-semantic taxonomy | yes | env vars (AWS_*) |
| `kubectl` | `-o json` | no | binary (0/1) | no | kubeconfig |
| `op` / `bw` | yes | no | binary (0/1) | partial | env var session |
| `stripe` | yes | yes (events) | binary (0/1) | yes | OAuth device code |

No CLI in this list ships the full canonical agent-ready surface (envelope + semantic exit codes + structured errors + NDJSON + headless auth). The closest is `aws`. Build for the gap they leave.

## MCP exemplars

Six production MCP servers from major SaaS vendors, with evidence drawn from the 16-server survey in `optimize-agentic-mcp/references/patterns/exemplar-servers.md`.

### GitHub — `github/github-mcp-server`

- **Surface**: 56+ tools grouped by toolsets (`actions`, `issues`, `pull_requests`, `repos`, `code_security`, ...). Hybrid: enum-dispatcher tools (`issue_read(method=enum)`) for high-cardinality domains, one-per-operation for the rest.
- **Auth**: OAuth (GitHub App / OAuth App) or PAT Bearer locally; OAuth remote.
- **Transport**: Remote at `api.githubcopilot.com/mcp/`; local stdio; Docker.
- **Notable**: deploy-time description override via `github-mcp-server-config.json` — operators rewrite tool descriptions without forking. Lockdown mode filters response content per method when the caller lacks push access.
- **Citation**: `github.com/github/github-mcp-server`, preview 2025-04-04.

### Linear

- **Surface**: 23 tools, remote-only. `list_issues`, `get_issue`, `create_issue`, `update_issue`, etc. Intent-consolidated; explicitly NOT a 1:1 GraphQL wrapper.
- **Schema**: Flat — collapsed nested GraphQL filters into `assigneeId`, `teamId`, `stateId`. Magic value `"me"` accepted for assignee.
- **Response**: Stringified JSON in `content[].text`; no `structuredContent`. Catalog measures **17.3k tokens** after connect — the agent's context jumps 61k → 78k before any work.
- **Notable**: ships a `search_documentation` tool with no matching API endpoint — a deliberate knowledge-layer bolt-on. Linear treats MCP as a separate product surface.
- **Citation**: `linear.app/docs/mcp`; reverse-engineered tool dump at `blog.fiberplane.com/blog/mcp-server-analysis-linear/` (2025).

### Stripe

- **Surface**: ~25 tools across Payments, Customers, Products, Prices, Invoices, Subscriptions, Refunds, Disputes, Balance, Payment Links, Coupons.
- **Auth**: Remote OAuth at `mcp.stripe.com`; local via `npx -y @stripe/mcp --api-key=...`. **Restricted API Keys (`rk_*`) are the permissions surface** — there is no MCP-level scope system; Stripe reuses its existing fine-grained API key permissions.
- **Notable**: For Connect platforms, `context.account = "acct_123"` switches tenant per call. Sibling `@stripe/agent-toolkit` provides framework helpers; `@stripe/token-meter` measures usage.
- **Citation**: `github.com/stripe/agent-toolkit`.

### Notion — `makenotion/notion-mcp-server` + hosted

- **Surface**: v1 = 19 tools (1:1 from OpenAPI); v2 = 22 tools (hybrid, AI-first rewrites + wrappers). Hosted v2 adds agentic tools: `create-pages`, `update-page`, `search`, `create-comment`.
- **Naming**: **`kebab-case`** — unusual.
- **Response**: Notion-flavored Markdown for page content — introduced specifically because raw JSON blocks were too token-heavy.
- **Notable**: post-mortem (`notion.com/blog/notions-hosted-mcp-server-an-inside-look`, 2026): "1:1 API-to-tool mapping produced poor agent experiences, including high token use from hierarchical JSON block data." Definitive citation when arguing against 1:1 wrappers.

### Sentry — `getsentry/sentry-mcp`

- **Surface**: ~10–15 tools incl. `search_events`, `search_issues`, `use_sentry`. Tool groups (Issues / Errors / Projects / Seer / discovery) selectable at **OAuth consent time**.
- **Auth**: Cloud = OAuth Streamable HTTP at `mcp.sentry.dev/mcp`; device-code for stdio. Self-hosted = access token.
- **Notable**: NL search tools require caller-supplied `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` — an embedded LLM inside the MCP. Tool-group selection at OAuth consent is the rare pattern: shrink the catalog per user, not per tenant.
- **Citation**: `docs.sentry.io/ai/mcp/`.

### Supabase — `supabase-community/supabase-mcp`

- **Surface**: 27 tools. `snake_case`. Feature groups (`account`, `docs`, `database`, `debugging`, `development`, `functions`, `storage`, `branching`); default disables `storage` to reduce tool count.
- **Schema**: **Zod v4 with both `parameters` AND `outputSchema` on every tool.** Heavy use of MCP annotations: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`.
- **Notable**: URL-query-param config — `mcp.supabase.com/mcp?project_ref=…&read_only=true&features=database,docs` reconfigures the surface without restarting the client. `execute_sql` wraps results in `<untrusted-data-${UUID}>…</untrusted-data-${UUID}>` with embedded ignore-instruction — prompt-injection defense.
- **Disagreement**: README explicitly states "this server does not send `structuredContent`; Vercel AI SDK parses JSON from content text." Opt-out from the spec direction.
- **Citation**: `github.com/supabase-community/supabase-mcp`.

### Figma Dev Mode MCP

- **Surface**: 15 tools (launched with 3). `snake_case`. `generate_figma_design`, `get_design_context`, `get_variable_defs`, `get_code_connect_map`, etc.
- **Auth**: Figma desktop app session; local stdio with remote tools mixed in.
- **Notable**: `generate_diagram` converts Mermaid → FigJam — a reverse-bridge no other vendor replicates. `create_design_system_rules` scans the caller's codebase from the server side and emits a rules file for agent guidance — inverts the usual "agent reads repo" flow.
- **Design thesis**: "Context > pixels; goal is alignment to design intent, not pixel-matching" (`figma.com/blog/introducing-figma-mcp-server/`, 2025-06-04).

## Cross-surface comparison: same vendor, both surfaces

When the same vendor ships both a CLI and an MCP, the design choices diverge.

### GitHub: CLI vs MCP

| Aspect | `gh` CLI | GitHub MCP |
|---|---|---|
| Surface count | ~30 commands | 56+ tools |
| Granularity | Nouns (`gh pr`, `gh issue`, `gh repo`) with flat verbs | Hybrid: enum-dispatcher tools for high-cardinality domains |
| Output | JSON via `--json <fields>`; `--jq` for filtering | Tool responses; some structured, some text |
| Auth | PAT via env or `gh auth login` | OAuth (GitHub App/OAuth App) or PAT Bearer |
| Discovery | `--help` per command; no machine-readable spec | `tools/list` with full schemas; toolset filtering |

The CLI is shaped for shell composition: nouns + flat verbs, `jq`-friendly output, single-tenant auth. The MCP is shaped for cross-client governance: OAuth, toolset filtering, deploy-time description override, lockdown mode for permission-aware filtering. Same vendor, same backend API, two different surface designs because the workloads differ.

### Stripe: CLI vs MCP

| Aspect | `stripe` CLI | Stripe MCP |
|---|---|---|
| Surface count | ~30 commands | ~25 tools |
| Auth | OAuth device-code via `stripe login`; live/test mode flag | OAuth remote OR API key (`rk_*`); per-Connect-account context |
| Streaming | NDJSON via `stripe events tail` | None for events; structured tool calls only |
| Permissions | Restricted API Keys are the surface | Same — Restricted API Keys carry through |
| Test/prod separation | Explicit `--test-mode` flag | `mcp.stripe.com` for live; sandbox via key prefix |

Stripe's pattern: keep the permissions primitive (Restricted API Keys) constant across both surfaces. The CLI gets streaming and shell composition; the MCP gets per-account context and OAuth. The agent picks the surface based on whether the workload is composable (CLI) or governed (MCP).

The lesson: when shipping both surfaces, share the auth primitive. Don't reinvent permissions on the second surface.

## Cross-vendor convergences and divergences

The 16-server MCP survey (cross-link `../mcp/patterns/exemplar-servers.md`) plus the CLI exemplars above reveal the patterns that converged across vendors and the patterns that didn't.

### Where vendors converged

- **Remote / hosted transports over stdio** for MCP. Every major vendor except PayPal ships a hosted Streamable HTTP endpoint. Stdio remains for local-dev and CI.
- **OAuth over long-lived API keys.** Even Stripe — which still accepts API keys — defaults to OAuth for its hosted MCP. The CLI exemplars are split: `gh` and `aws` accept env-var tokens; `op`, `bw`, `stripe` ship OAuth-style flows.
- **`snake_case` as the default identifier convention.** 14 of 16 MCPs use it. Atlassian Rovo (`camelCase`) and Notion (`kebab-case`) are outliers. Same convention dominates production CLIs.
- **Streamable HTTP `/mcp` endpoint, deprecating `/sse`.** HubSpot, Cloudflare, Intercom, Notion, Atlassian, Asana V2 all point at Streamable HTTP and mark SSE legacy or reject it outright.
- **Per-request ephemeral sessions.** HubSpot is explicit; most hosted servers implement the same way to scale horizontally.
- **Intent-consolidated tools over 1:1 OpenAPI wrappers.** Notion explicitly regretted v1's auto-generated mapping; Linear never attempted it.

### Where vendors diverged

- **Tool count.** 2 (Cloudflare) → 4 (Shopify) → 6 (Intercom) → 14 (Vercel / Zapier Agentic) → 15 (Figma) → 22 (Notion v2) → 23 (Linear) → 27 (Supabase) → 29 (PayPal) → 54 (Atlassian Rovo) → 56+ (GitHub). Spread spans 28× — the design philosophies are genuinely different.
- **Response shape.** JSON (Stripe, PayPal, Vercel, Intercom, Supabase); stringified JSON in text (Linear); Markdown (Atlassian, Notion); XML (Figma metadata); untrusted-data-wrapped JSON (Supabase); JS result (Cloudflare Codemode).
- **`structuredContent` adoption.** Spec-recommended. Supabase explicitly opts out; Linear doesn't use it; most others ambiguous.
- **Auth sophistication.** HubSpot (OAuth 2.1 + PKCE + runtime permission intersection) > Atlassian / Linear / Notion / Intercom (OAuth with DCR) > Stripe (OAuth + Restricted Keys) > Asana V2 (OAuth without DCR) > PayPal (manual `client_credentials` → Bearer paste).
- **Statelessness vs sessions.** HubSpot pioneered ephemeral per-request; most hosted MCPs followed; some (Linear-style multi-turn workflows) keep session state.

The convergences are signal — they're now table-stakes. The divergences are choice points — pick deliberately, name your reason.

## What to copy — 5 patterns to imitate

1. **Universal `--json` flag (CLI) / `structuredContent` AND text summary (MCP).** GH's `--json`, AWS's default JSON, Supabase's dual-shape responses. Ship both: structured for the parser, summary for the human-readable surface.
2. **Headless auth via env var session token.** `OP_SESSION_*`, `BW_SESSION`, `STRIPE_API_KEY`. The agent doesn't dance through OAuth on every call.
3. **Toolset filtering at connect time.** Sentry at OAuth consent, Supabase via URL query params, GitHub via deploy-time toolset flags. Shrink the catalog before the agent sees it.
4. **Intent-consolidated tools instead of 1:1 API wrappers.** Linear, Notion v2, Stripe — all explicit about NOT mirroring endpoints. Notion's post-mortem is the citation when someone proposes auto-generating tools from OpenAPI.
5. **Deploy-time / config-time description override.** GitHub's `github-mcp-server-config.json`. Lets enterprises tune tool descriptions per environment without forking. Worth copying for any MCP shipping into varied deployments.

## What to avoid — 5 anti-patterns to refuse

1. **1:1 OpenAPI → MCP generation.** Notion's v1 post-mortem: poor agent experience, high token use from hierarchical JSON. Every exemplar that started API-shaped migrated away.
2. **Manual OAuth `client_credentials` flow with no refresh.** PayPal ships this — users must `curl` for a Bearer token, paste into env, re-run when it expires (~32,400s). Prefer OAuth 2.1 + PKCE with refresh-token rotation.
3. **Stringified JSON in `content[].text` with no `structuredContent`.** Linear ships this; the catalog still works, but the spec exists for a reason. Spec-respecting clients re-parse text and break on edge cases.
4. **Catalog token cost > 5% of context window with no toolset filter.** Linear's 17.3k-token connect cost without a tool-subset selector. The catalog eats the agent's budget before any work happens.
5. **OAuth without DCR for gateway integrations.** Asana V2 rejects DCR; Docker MCP Gateway is blocked on this decision. Supporting DCR is table-stakes for gateway integrations in 2026.

## Picking an exemplar to study

The right exemplar depends on the workload shape. Use this matrix to pick.

| Your situation | Primary exemplar | Why |
|---|---|---|
| Large REST API (50+ endpoints) with typed bindings | Cloudflare (Codemode) | Only published 1.17M → 1k token benchmark at this scale |
| GraphQL backend | Linear | Public flattening strategy; concrete examples |
| Enterprise multi-tenant with scoped permissions | HubSpot | OAuth 2.1 + PKCE + runtime permission intersection — gold standard |
| Narrow task surface (cart, ticket) | Shopify Storefront | 4-tool design proves small surface works for small workflows |
| Productivity suite with cross-product entities | Atlassian Rovo | Teamwork Graph — cross-product walks |
| Developer tooling with CLI already present | Vercel | `use_vercel_cli` meta-tool — "don't replace the CLI" |
| Platform with thousands of potential actions | Zapier | Two-mode design: Classic (curated) + Agentic (meta-tools) |
| Billing / financial API | Stripe | Restricted Keys + Connect account context |
| Code forge | GitHub | Enum-dispatcher + lockdown + insiders + description override |
| Vault / credential manager | `op` / `bw` | Headless auth via env-var session token |

When two exemplars apply, prefer the one with public engineering blog posts (HubSpot, Notion, Cloudflare) — they document the trade-offs you're about to face.

## Open questions the exemplars haven't settled

The 16-server survey leaves several questions unresolved as of 2026-04. Carry them as design decisions you'll have to make on your own evidence.

- **`structuredContent` in practice.** No exemplar publishes a before/after cost comparison for `structuredContent` vs stringified JSON. Supabase's explicit opt-out suggests the ergonomics story isn't settled. Ship both and measure your own.
- **DCR adoption.** Asana V2 rejects it; most others accept it. Gateways like Docker MCP Gateway are stuck waiting. If you're shipping for a gateway, support DCR.
- **Meta-tools vs dedicated tools.** Zapier ships both modes (Classic + Agentic) and lets the user choose. No vendor publishes comparative telemetry on which mode wins for which task.
- **Embedded LLM inside the MCP.** Sentry does this for NL search. No other exemplar does. Unclear whether this is a broader pattern or a Sentry-specific workaround.
- **Tool-count ceilings on mid-tier models.** Atlassian Rovo 54 and GitHub 56+ work with frontier models today. There is no published evidence on whether mid-tier models degrade gracefully at those counts.
- **Markdown body format standardization.** Notion ships "Notion-flavored Markdown", Atlassian ships Confluence-flavored Markdown, Figma ships React+Tailwind by default. No convergence.

When you make a call on any of these, document the reasoning and the date — the answers will move.

## How exemplars age

The MCP ecosystem moves fast enough that exemplars older than 6 months may have shipped redesigns.

Concrete examples of redesigns since launch:

- **Notion v1 → v2** (2025 → 2026): abandoned 1:1 OpenAPI mapping; added `create-pages`, `update-page`, `search`, `create-comment` agentic tools; introduced Notion-flavored Markdown to replace JSON blocks.
- **Asana V1 → V2** (sunset 2026-05-11): switched OAuth model; tokens for MCP no longer work with REST API.
- **Linear catalog growth** (2025 → 2026): tool count rose from ~12 to 23 with no toolset filter; catalog token cost is now 17.3k.
- **Sentry tool-group selection** (2026): added OAuth-consent-time grouping to shrink per-user catalogs.

When citing an exemplar, include the YYYY-MM-DD of the source page. When applying its pattern, recompute staleness — half the patterns above didn't exist 12 months ago.

## Citing exemplars in design discussions

Exemplars are evidence, not authority. Use them to back design decisions, not to win arguments.

Good citations:

- "Notion's post-mortem (notion.com/blog, 2026) recommends against 1:1 OpenAPI mapping; we should consolidate to intent-based tools instead."
- "HubSpot's published reasoning (product.hubspot.com/blog, 2025-06-18): SSE complicates auto-scaling. We're behind an LB; pick Streamable HTTP only."
- "Cloudflare's Codemode benchmark (developers.cloudflare.com, 2026): 1.17M tokens → 1k via JS sandbox. Our API has 80 endpoints; this is the path."

Bad citations:

- "Linear ships 23 tools, so we can ship 23." — Linear's catalog cost is 17.3k tokens; that's evidence against, not for, the count.
- "Stripe uses OAuth, so we should too." — Stripe's auth choice depends on Restricted API Keys as the permission surface; if you don't have that primitive, the model doesn't apply.

The exemplar is signal; the reasoning is yours.

## Cross-references

- For the full 16-server survey with disagreements and copy-this patterns, read `../mcp/patterns/exemplar-servers.md`.
- For the detailed CLI audits with scores, read the historical examples in the merged `cli/code-templates.md`.
- For the design choices these exemplars made, route through `descriptions-as-prompts.md`, `output-contracts.md`, `error-strategy.md`.
- For when the workload determines which exemplar to copy, read `decide-surface.md`.
- For exemplar-derived design phases, read `../mcp/decision-trees/design-phase.md`.
