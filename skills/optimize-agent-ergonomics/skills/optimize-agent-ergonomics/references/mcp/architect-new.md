# Mode B-MCP — Architect a new MCP server

Design a new MCP server from scratch. Run the surface-agnostic 8-question pass first, confirm MCP is the right primitive, then walk the 12-question MCP brainstorm, produce an architecture sketch, get user approval, hand off to a companion build skill. No code is written here — this file ends with a one-page sketch and a named handoff.

## Before you open this file

Two preconditions. Skip either and the rest of the conversation is wasted:

1. The user said "I want to build an MCP server" or equivalent — not "should I build a CLI or an MCP?" If the surface is undecided, route to `../common/decide-surface.md` first and come back.
2. The 8 surface-agnostic questions in `../common/design-thinking.md` are already answered, and "MCP" was the surface that fell out. If they are not, run that file first.

Reaching the end of this file without an approved architecture sketch and a named companion skill means Mode B-MCP is not finished — keep going.

## Workflow

```
1. Run common/design-thinking.md (8 surface-agnostic questions)
   |
   +-- Surface lands on MCP --> continue
   +-- Surface lands on CLI --> route to cli/architect-new.md, stop
   +-- Surface unclear      --> route to common/decide-surface.md, stop
2. Walk the 12 MCP brainstorm questions below (Q1..Q12)
   |
   +-- An answer says "MCP is the wrong primitive"
   |   --> route to common/decide-surface.md, stop
   +-- All 12 answered --> continue
3. Produce the architecture sketch (template below)
4. Present sketch; ask the user to approve or adjust
   |
   +-- User adjusts --> revise sketch, re-present
   +-- User approves --> continue
5. Pick the companion build skill (handoff matrix below)
6. State the install command and the first follow-on action; stop
```

Do not skip step 1. The 8 surface-agnostic questions are the evidence that MCP is the right surface in the first place; jumping into the MCP-specific 12 without them produces a pretty sketch for the wrong product.

## The 12 MCP brainstorm questions

Ask each verbatim or with minimal sharpening. Order matters — later questions assume earlier answers. After every question, write the answer down; the architecture sketch will need it. Cite the source for each block when relaying to the user.

### Q1. End-user task in one sentence

> "Describe the outcome users want, not the endpoints. What is the end-user task this MCP enables in one sentence?"

**Why it matters.** If the answer reads like an API description ("expose `GET /users`"), the user is in the wrong frame. Tools map to user intents, not REST verbs. A vague answer here flows downstream into a 1:1 REST wrap and a 30-tool surface.

**Implication.** Sharp answer → continue. Vague answer → ask one follow-up; if still vague, route to `decision-trees/design-phase.md` and stop until the user can name the task.

**Next.** `decision-trees/design-phase.md` for the early architecture lock-ins.

### Q2. Existing CLI or SDK already

> "Does the system you're wrapping have an official CLI (`gh`, `kubectl`, `aws`, `az`, `stripe`) or a well-maintained SDK?"

**Why it matters.** If a battle-tested CLI already exists, an MCP wrapper is often duplicate surface area for the agent — read `../common/decide-surface.md` before committing.

**Implication.** Yes → route to `../common/decide-surface.md`. No → continue.

### Q3. Local or remote

> "Will this MCP run on the user's machine (stdio, one process) or hosted somewhere (HTTP)?"

**Why it matters.** Transport decides the auth, deployment, scaling, and threat model. Almost everything new in 2026 is remote Streamable HTTP; stdio is local dev tools.

**Implication.**
- Local stdio → official SDK v1, no network threat model.
- Remote HTTP, modern DX → `mcp-use` server.
- Remote HTTP, widest compat → official SDK v1.
- Remote HTTP, willing to accept beta → SDK v2.

**Next.** `patterns/transport-and-ops.md`.

### Q4. Tool count and granularity

> "How many tools do you expect at launch and one year out?"

**Why it matters.** Tool count drives the schema-design and progressive-discovery decisions. Past the per-model sweet spot, routing accuracy collapses.

**Implication.**
- < 10 tools → static list is fine.
- 10–20 → consolidate CRUD into action-enums; namespace clearly.
- 20–40 → progressive discovery (`patterns/progressive-discovery.md`).
- 40+ → meta-tools or semantic search.

**Next.** `decision-trees/tool-count.md`.

### Q5. Schema strategy

> "Will you author schemas in Zod, JSONSchema, or generate them from typed code?"

**Why it matters.** SDK choice partially decides this (v1 → Zod v3; v2 → Zod v4; mcp-use → Zod). LLMs reliably generate flat structures; nested objects past one level fail at parse time.

**Implication.**
- Zod (v3 or v4) → flat, ≤6 top-level params, no nesting >1 level.
- JSONSchema hand-written → same flatness rule; easy to drift from the SDK's expected shape.
- Generated from typed code → audit the emitted shape, not the source type.

**Next.** `patterns/schema-design.md`.

### Q6. Response format

> "What do tools return — text the agent reads, structured data the agent acts on, both, or large datasets?"

**Why it matters.** Wrong shape burns context budget. Raw API JSON is the most common mistake.

**Implication.**
- Prose for the user → text content.
- Data for the agent → `structuredContent` + `outputSchema`.
- Both → mixed (text for narrative, structured for data); annotate audience.
- Large dataset → paginate or expose as Resources.

**Next.** `decision-trees/response-format.md`.

### Q7. Error model

> "How will the server signal failure — protocol error, `isError: true` in the result, or a custom envelope?"

**Why it matters.** Protocol errors get swallowed by the client; the LLM never sees them. Business-logic failures must use `isError: true` plus content that names the recovery path.

**Implication.**
- Validation / business failure → `isError: true` + recovery guidance the agent can act on.
- Auth / permission → `isError: true` + scope or step-up consent guidance.
- Transient (rate limit) → `isError: true` + retry-after.
- Transport / framework failure → JSON-RPC error code (the only legitimate use).

**Next.** `decision-trees/error-strategy.md` (and `../common/error-strategy.md` for the universal taxonomy).

### Q8. Auth profile

> "How does the server know who the caller is — no auth, static API key, OAuth 2.1 + PKCE, OAuth + CIMD/DCR for marketplace?"

**Why it matters.** Auth shape is one of the hardest decisions to undo. Forwarding user tokens to upstream APIs is a guaranteed footgun (use OBO with audience checks).

**Implication.**
- None → single-user local stdio only.
- Static API key in env → solo developer / small team.
- OAuth 2.1 + PKCE → multi-user remote.
- OAuth + CIMD/DCR → public marketplace.

**Next.** `decision-trees/security-posture.md` and `patterns/auth-identity.md`.

### Q9. Sessions and state

> "Does any tool need to remember state across calls within a session? Across sessions?"

**Why it matters.** Statefulness drives session-management complexity, scaling design, and cleanup obligations. Default to stateless when possible.

**Implication.**
- Stateless → simplest. Horizontal scale by request.
- Per-session state → in-memory keyed by sessionId; cleanup on disconnect.
- Cross-session persistence → externalize to Redis or DB; multi-tenant isolation.

**Next.** `patterns/session-and-state.md`.

### Q10. Scaling expectations

> "What is the load profile — single-user local, internal team, B2B SaaS, public marketplace? What is the throughput expectation in 6 months?"

**Why it matters.** Scaling is the joint product of auth, sessions, and tool design. Get any one wrong and the others can't compensate.

**Implication.**
- Single-user local → no scaling concern.
- Per-user remote → session-scoped; horizontal scale by user.
- Multi-tenant → sharding by tenant; per-call audit; per-user tokens.
- High-frequency tools → caching is mandatory.
- Long-running tools → consider sampling / elicitation / async.

**Next.** `decision-trees/scaling.md` and `patterns/caching-economics.md`.

### Q11. Advanced protocol features

> "Do you need sampling (server asks the client's LLM for a completion), elicitation (server asks the client to ask the user), or roots (filesystem boundaries)?"

**Why it matters.** Client support is uneven. Silently dropping a sampling feature on a non-supporting client breaks the workflow.

**Implication.**
- Sampling needed → capability-gate; fall back gracefully.
- Elicitation needed → same.
- Roots needed → check VS Code / Claude Desktop support matrix.
- Resources / Prompts (beyond tools) → useful for large datasets and templated workflows.

**Next.** `patterns/advanced-protocol.md` and `patterns/resources-and-prompts.md`.

### Q12. Client compatibility and deployment

> "Which MCP clients must this support — Claude Desktop, Claude Code, Cursor, Windsurf, VS Code, Goose? And where will it be deployed — npx, Smithery, Cloudflare Workers, Vercel, Railway, Docker?"

**Why it matters.** Some features only work in specific clients. Some platforms have cold-start or session quirks that bend the architecture.

**Implication.** Cross-check against `patterns/client-compatibility.md`. Pick the deployment that matches the session-affinity / cold-start budget the workload can tolerate (`patterns/transport-and-ops.md`).

## Architecture-sketch template

Once Q1..Q12 are answered, produce this sketch verbatim and ask the user to approve before any code is written.

```
# MCP Architecture Sketch — <project-name>

## Problem statement
<End-user outcome in 1-2 sentences. Not API endpoints.>

## User intents (1-3)
1. <intent 1>
2. <intent 2>
3. <intent 3>

## Tools (target count: <N>)
- <tool_name_1> — <one-line purpose; verb + resource>
- <tool_name_2> — <one-line purpose>

## Schema strategy
<Zod v3 / Zod v4 / JSONSchema; flat ≤6 top-level params, ≤1 nesting>

## Response format
<text / structured (with outputSchema) / mixed / paginated>

## Error model
<isError taxonomy; protocol errors only for transport>

## Auth
<none / API key / OAuth 2.1 + PKCE / OAuth + CIMD>

## Session model
<stateless / per-session in-memory / externalized>

## Transport
<stdio / Streamable HTTP>

## Advanced protocol
<sampling y/n; elicitation y/n; roots y/n; resources y/n; prompts y/n>

## Target clients
<Claude Desktop / Claude Code / Cursor / VS Code / Goose / ...>

## Deployment
<npx / Smithery / Cloudflare Workers / Vercel / Railway / Docker / ...>

## Framework choice
<mcp-use server / official SDK v1 / SDK v2 beta> — rationale:

## Success metric (3 months out)
<measurable outcome the user can later verify>

## Next steps
1. User approves this sketch.
2. Install <companion skill name> with the install command below.
3. After the first tool lands, return here for an audit pass against the prototype.
```

## Companion-skill handoff matrix

After the sketch is approved, route to exactly one of the following.

| Skill | Pick when | Tradeoff |
|---|---|---|
| `build-mcp-server-sdk-v1` | Production with mainstream SDK; widest client compatibility; stdio or HTTP; Zod v3 | Manual transport / OAuth wiring; deprecated overloads still compile |
| `build-mcp-server-sdk-v2` | Greenfield project willing to accept beta; Zod v4; ESM-only; Node 20+ | Adoption still early; server-side OAuth removed; no CJS |
| `build-mcp-use-server` | New HTTP-first TS server; want the wrapper to handle transport, CORS, OAuth, sessions | Locks you into `mcp-use/server` imports; less bare-metal control |

Adjacent skills that may apply:

- `convert-mcp-server-sdk-v1-to-v2` — when porting an existing v1 server.
- `test-by-mcpc-cli` — once the server is running, validate end-to-end with `mcpc 0.2.x`.
- `use-railway` — for ongoing Railway-hosted operations (logs, scale, restart).

Install command format:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>
```

## Anti-patterns

- **Skipping the brainstorm.** Jumping into code before Q1..Q12 are answered guarantees rework — the schema, transport, and auth decisions you make on instinct will not survive the first real user.
- **Wrapping a REST API 1:1.** Q1 is the canary; if the answer reads like API endpoints, the brainstorm has not actually started.
- **Picking SDK v2 because it is newer.** v2 is beta; pick it only when API churn is acceptable. v1 is the production default.
- **Choosing transport before auth.** Transport and auth are coupled (stdio implies "no network auth"; HTTP implies a full threat model). Decide together at Q3 + Q8.
- **Eagerly registering 30+ tools.** Past the model's sweet spot, routing collapses. Q4 forces the count out into the open early.
- **Ignoring client compatibility.** Sampling and elicitation work in some clients and silently no-op in others. Q11 + Q12 catch this before the architecture is locked.
- **Forwarding user tokens upstream.** Use OBO with audience checks — see `patterns/auth-identity.md`.
- **Skipping the architecture-sketch approval.** The sketch is the contract; without it, the companion build skill has no fixed target.

## Routing after this file

- The architecture sketch is approved → companion build skill (matrix above).
- The brainstorm exposed that MCP is the wrong primitive → `../common/decide-surface.md`.
- A specific question dominates the design (auth, scaling, tool count) → the matching decision-tree:
  - Tool count or progressive discovery → `decision-trees/tool-count.md`.
  - Response format → `decision-trees/response-format.md`.
  - Error semantics → `decision-trees/error-strategy.md`.
  - Threat model → `decision-trees/security-posture.md`.
  - Scaling → `decision-trees/scaling.md`.
  - Pre-deploy → `decision-trees/production-readiness.md`.
  - Early architecture lock-ins → `decision-trees/design-phase.md`.

## When to re-enter this file

- Tool count crosses the next cliff (10 / 20 / 40 / 100) — re-run Q4 and revisit `decision-trees/tool-count.md`.
- Target-client mix changes (Cursor or Windsurf added) — re-run Q11 + Q12.
- Sampling or elicitation discovered mid-build — `patterns/advanced-protocol.md`.
- Single-user scope grows to multi-tenant — re-run Q8 + Q10.
- v2 beta API changes land — re-read the `build-mcp-server-sdk-v2` SKILL.md before starting again.
