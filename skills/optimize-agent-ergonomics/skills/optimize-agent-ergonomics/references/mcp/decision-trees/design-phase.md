# Decision tree — design-phase choices that lock in for the lifetime of the server

The decisions you make once and live with. SDK, schema dialect, statefulness, transport, auth model — once shipped, the cost of changing any of these is high and the blast radius is wide. Pick deliberately.

## Decision branches

```
START: Are you starting a new MCP server or porting/redesigning?
|
+-- New server
|   +-- Run the 8 design-thinking questions first --> ../../common/design-thinking.md
|   +-- Confirm the surface decision --> ../../common/decide-surface.md
|   +-- Then walk the 5 design-phase decisions below in order
|
+-- Porting / redesigning
    +-- Honor as many existing decisions as possible (callers depend on them)
    +-- Change one branch at a time; don't rewrite all five at once
    +-- Schedule schema/transport/auth changes for major-version bumps only
```

The five decisions below are walked in order. Each one constrains the next.

### Decision 1 — SDK choice (v1 / v2 / mcp-use)

Three production options as of 2026-05.

| SDK | When | Trade-off |
|---|---|---|
| `@modelcontextprotocol/sdk` v1.x | Production-ready, mainstream, most exemplars use it (Linear, Stripe, GitHub) | Stable; less feature-velocity |
| `@modelcontextprotocol/sdk` v2.x (split-package) | Need newest features (sampling, elicitation, roots); willing to ride beta | Newer; smaller install; cleaner abstractions |
| `mcp-use` (HTTP-first wrapper) | Modern DX; opinionated; HTTP from day one | Higher-level; less control over protocol details |

Picking factors:

- **Existing codebase invests heavily in v1 idioms** → keep v1; port later.
- **Need sampling, elicitation, or roots** → v2 (advanced protocol features land there first).
- **Building a hosted Streamable HTTP server with no stdio path** → mcp-use simplifies the wire layer.
- **Targeting multiple MCP clients (Claude, Cursor, ChatGPT) with varying spec conformance** → v1 covers the broadest compatibility today.

Route to the companion build skill once decided: `build-mcp-server-sdk-v1`, `build-mcp-server-sdk-v2`, or `build-mcp-use-server`.

The SDK choice is changeable but expensive — it affects every tool registration, every schema, every transport configuration. Pick once and stick.

### Decision 2 — Schema strategy (Zod / JSONSchema / typed)

Three schema dialects with different portability profiles.

| Dialect | Portability | Trade-off |
|---|---|---|
| Zod (TypeScript) | Best in the v1/v2 SDK ecosystem; widely adopted | TypeScript-only; runtime validation lives with type definition |
| Pydantic (Python) | Best in the Python SDK ecosystem | Python-only; same runtime+type benefit |
| JSONSchema (raw) | Most portable; works in any language | Verbose to write; no compile-time type checking |

Cross-model compatibility considerations:

- **Claude** parses Zod-derived JSONSchema cleanly; `outputSchema` honored.
- **ChatGPT** (OpenAI tool calling) accepts JSONSchema with some restrictions on advanced features (`oneOf`, `$ref`, recursive schemas).
- **Cursor / VS Code** vary; assume the lowest common denominator (flat JSONSchema) for cross-model deployment.

Picking factors:

- **TypeScript stack** → Zod is the path of least resistance.
- **Python stack** → Pydantic.
- **Multi-language stack** OR **need raw OpenAPI integration** → JSONSchema.
- **Tools that need both `parameters` AND `outputSchema`** → Zod or Pydantic — both support output schema generation cleanly.

Cross-link `../patterns/schema-design.md` for the schema-shape principles (flat, ≤6 params, no nesting >1 level) that apply regardless of dialect.

### Decision 3 — Cross-model schema portability

What works in Claude vs ChatGPT vs Cursor.

```
Claude (Anthropic API + Claude Desktop + Claude Code)
+-- Honors `outputSchema` and `structuredContent`
+-- Honors MCP annotations (readOnlyHint, destructiveHint, idempotentHint)
+-- Honors server `instructions` field
+-- Tool-count sweet spot: 20-30; degrades past 50

ChatGPT (OpenAI tool-calling via MCP connector)
+-- Honors `inputSchema` (JSONSchema); some advanced features (oneOf, $ref) restricted
+-- `structuredContent` support: partial; depends on connector version
+-- Tool-count cap: 128 hard limit; sweet spot 15-20
+-- `instructions` field: variable client honor

Cursor / VS Code
+-- Variable; treat as "lowest common denominator"
+-- JSONSchema with `type`, `properties`, `required` always works
+-- Avoid `oneOf`, `anyOf`, `$ref` in schemas if portable target
```

Pick the portability target deliberately:

- **Single-client deployment** (e.g., Claude Desktop only) → use the full feature set; honor annotations and `outputSchema`.
- **Multi-client public MCP** → flat JSONSchema, no advanced features, ship both `content[].text` AND `structuredContent` for parsing flexibility.
- **Internal enterprise deployment with controlled clients** → standardize on one client's behavior; document the contract.

Cross-link `../patterns/client-compatibility.md` for the per-client compatibility matrix.

### Decision 4 — Stateless vs stateful

What state lives on the server vs the client.

| Pattern | When | Trade-off |
|---|---|---|
| **Stateless per-request** (HubSpot exemplar) | Multi-tenant SaaS; horizontal scaling; OAuth refresh-token rotation | Every request re-auths; latency cost of permission intersection (~20-50ms per call) |
| **Session-scoped state** (typical MCP) | Multi-turn workflows where state is meaningful within one conversation | Session lifecycle complexity; must handle reconnect / disconnect |
| **Persistent server-side state** | State must survive client disconnect (long-running jobs, queued operations) | Storage layer (Redis / Postgres); cleanup policy; eventual consistency questions |
| **Token-encoded state** (signed blob) | Workflow state can travel with the client | Token size grows with state; agent must pass tokens around |

Picking factors:

- **Workflow is single-call** → stateless is correct; don't pay session cost.
- **Workflow has obvious turn-by-turn state** (cursor pagination, transaction in progress) → session-scoped.
- **Workflow spans hours or days** (job queue, async batch) → persistent.
- **Workflow needs to be portable across client connections** → token-encoded.

The HubSpot exemplar is worth studying: ephemeral per-request sessions plus permission intersection on every call. Scales horizontally; fails safe (a crashed worker doesn't lose session state); pairs naturally with OAuth 2.1 refresh-token rotation.

Cross-link `../patterns/session-and-state.md` for the deep dive.

### Decision 5 — Transport (stdio / HTTP / SSE)

The wire layer decision constrains everything downstream.

| Transport | When | Trade-off |
|---|---|---|
| **stdio** | Local-dev, CI, single-user desktop apps | Process lifecycle = client lifecycle; no auth layer; no horizontal scaling |
| **Streamable HTTP** (recommended) | Hosted MCP servers; multi-tenant; SaaS connectors | Standard load-balancer pattern; OAuth 2.1; sessions either stateless or external |
| **SSE** (deprecated) | Legacy client compatibility only | Long-lived connections; harder to scale; HubSpot rejects outright |
| **WebSocket** | Custom transports; rare | Not standard MCP; client compatibility variable |

Picking factors:

- **Local-only, developer-driven, single-tenant** → stdio.
- **Hosted, multi-tenant, OAuth-required** → Streamable HTTP.
- **Need to support legacy clients that don't speak Streamable HTTP** → SSE alongside Streamable HTTP, marked deprecated.
- **Anything else** → Streamable HTTP. It's the production answer in 2026.

HubSpot's published reasoning (`product.hubspot.com/blog/...`, 2025-06-18): "Supporting SSE would have introduced load balancer and scaling complexity in auto-scaling environments." If you operate behind an auto-scaling LB, follow HubSpot — Streamable HTTP only.

Cross-link `../patterns/transport-and-ops.md` for the deployment patterns and operational concerns.

## Decisions that are expensive to undo

| Decision | Why expensive |
|---|---|
| Schema dialect | Every tool definition is written against the dialect; rewriting is per-tool |
| Transport | Hosted endpoint URL, OAuth callback URL, client config — all change |
| Auth model | OAuth flows, scopes, token TTLs, refresh logic — touch every code path |
| Statefulness | Server architecture, database schema, scaling profile — all derived |
| Tool naming convention (snake_case / camelCase) | Every client config and every agent prompt that references tools by name |

The cheaper decisions to revisit later: tool count (consolidate), description quality (rewrite), error envelope shape (additive changes to the schema), individual tool input schema (minor-version bump). The expensive ones above: ship deliberately and lock in.

## Re-evaluation triggers

These are the conditions that force you back to the design-phase decisions even after launch.

- **Adding a second target client** (e.g., Claude Desktop ships, then ChatGPT support requested) → revisit Decision 3 (cross-model portability).
- **Tool count crosses a per-model cliff** (50+ on Claude, 20+ on GPT-4, 10+ on Gemini) → revisit Decision 1 (does the SDK choice still fit?).
- **Operator wants to deploy on multi-region auto-scaling infrastructure** → revisit Decision 5 (transport must be Streamable HTTP) and Decision 4 (statefulness must be ephemeral or external).
- **Auth requirement upgrades to per-user OAuth + audit + revocation** → revisit Decision 4 (likely needs server-side session for token rotation tracking) and `../patterns/auth-identity.md` for OAuth 2.1 + PKCE patterns.
- **A tool needs to span multiple sessions** (long-running async job) → revisit Decision 4; persistent state required.

Each of these is a major-version event. Plan for migration: keep the old contract working through one full version while the new one rolls out.

## Anti-patterns at the design phase

- **Picking the SDK based on team familiarity, not on workload fit.** v1 is the default for most workloads, but if you need sampling/elicitation, v2 is the right answer regardless of how comfortable the team is with v1.
- **Skipping cross-model portability decisions until launch.** "We'll worry about ChatGPT support later" leads to schemas that work in Claude and break elsewhere.
- **Defaulting to stateful when stateless would work.** Stateful adds complexity; only pay for it when the workflow demands it.
- **Adopting SSE in 2026.** It's deprecated. Streamable HTTP only.
- **Picking auth model before deciding statefulness.** Auth and statefulness are coupled; OAuth 2.1 + PKCE pairs naturally with stateless per-request, while shared-secret keys can work either way.
- **Mixing schema dialects within one server.** Some tools defined in Zod, others in raw JSONSchema, others in Pydantic — the maintenance cost compounds. Pick one.
- **Designing the schema before deciding statefulness.** A stateless API and a stateful one have different schemas (idempotency keys, state tokens). Settle Decision 4 first.
- **Locking transport before knowing the deployment target.** stdio is fine for local-only; Streamable HTTP for hosted. Picking the wrong one means rewriting the server lifecycle.

## Worked example — picking decisions for a hypothetical "issue tracker MCP"

Walk the five decisions for an MCP that fronts an issue-tracker SaaS:

1. **SDK choice.** Production-ready, multi-tenant SaaS connector. Pick v1 — broad client compatibility wins over advanced features.
2. **Schema strategy.** TypeScript stack. Pick Zod with `parameters` AND `outputSchema` per tool (Supabase pattern).
3. **Cross-model portability.** Multi-client (Claude Desktop, Cursor, ChatGPT). Use flat JSONSchema (no `oneOf` / `$ref`); ship both `content[].text` summary AND `structuredContent`.
4. **Statefulness.** Multi-tenant; OAuth refresh required. Pick stateless per-request (HubSpot pattern) with permission intersection on every call.
5. **Transport.** Hosted, multi-region, behind an auto-scaling load balancer. Streamable HTTP only; reject SSE.

Five decisions made; the rest of the design (tool granularity, error envelope, audit logging) is downstream from these.

## Cross-references

- For the 8 surface-agnostic questions that precede this tree, read `../../common/design-thinking.md`.
- For the surface decision (CLI vs MCP) that gates whether this tree applies, read `../../common/decide-surface.md`.
- For schema-shape principles independent of dialect, read `../patterns/schema-design.md`.
- For client-compatibility matrices, read `../patterns/client-compatibility.md`.
- For session-vs-stateless trade-offs, read `../patterns/session-and-state.md`.
- For transport selection and deployment patterns, read `../patterns/transport-and-ops.md`.
- For auth-model patterns (OAuth 2.1 + PKCE, RFC 9728 PRM, CIMD, OBO), read `../patterns/auth-identity.md`.
- For exemplars that ship each combination of decisions, read `../patterns/exemplar-servers.md`.
- For the next tree once design-phase choices are locked, read `tool-count.md`.
