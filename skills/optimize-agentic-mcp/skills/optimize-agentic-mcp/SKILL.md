---
name: optimize-agentic-mcp
description: Use skill if you are optimizing an existing MCP server or architecting a new one — framework pick, security posture, context budget, and companion toolchain.
---

# MCP Server Skill — Optimize Existing or Architect New

This skill is the entry point for any MCP-server work that is bigger than one line of code. It helps you either tune up a server that already exists or shape a brand-new one before a single file is scaffolded. Both paths share the same reference library — one folder of decision trees, one folder of pattern files — so you only learn the routing once.

Two things to remember before anything else:

1. Do not apply patterns mechanically. Explore the repo (or the user's intent) first, present findings with options, let the user choose.
2. You are not expected to do it all alone. If a question needs fresh research or a big chunk of file work, dispatch a subagent — see "Dispatching Subagents" below.

## Two Modes — Pick One Before You Do Anything

### Mode A — Optimize an existing MCP server

Pick Mode A when the user already has an MCP server (their repo, a fixture, a package) and wants it improved, audited, hardened, or reviewed. The rhythm is **Explore → Diagnose → Present → Optimize**, and it never skips straight to code.

1. **Explore the codebase.** Before you ask a single question, read the repo. Look for an MCP entry point, tool registrations, schemas, error handling, and transport config. Useful starting searches:

   ```bash
   tree . -I node_modules --dirsfirst -L 3
   rg -n -l "McpServer|FastMCP|server\\.tool|@tool|@mcp\\.tool|registerTool|Server\\(" . -g '!node_modules'
   rg -n "server\\.tool|@tool|registerTool|def .*tool|tool\\(" . -g '!node_modules'
   rg -n -l "z\\.|inputSchema|BaseModel|Field\\(|pydantic|jsonschema" . -g '!node_modules'
   rg -n "stdio|streamable|sse|transport" . -g '!node_modules'
   ```

   If `tree` is missing, fall back to `find . -maxdepth 3 -type d`. If `rg` is missing, fall back to `grep -R`. If the repo contains multiple MCP servers, stop and ask which one is in scope — never blend findings across servers.

   Read the files in this order: manifest (`package.json`, `pyproject.toml`), entry point, tool registration, schemas, transport/auth config.

   **Prerequisite check.** If nothing MCP-shaped exists after searching repo root and the usual server directories (`src/`, `server/`, `servers/`, `app/`, `apps/`, `packages/`, `services/`, `mcp/`), stop and report the missing prerequisite. Do not invent a server just to keep going. If the user actually wants a new server, switch to Mode B.

2. **Diagnose with targeted questions.** Ask 2–3 questions that reference specific files and line numbers you found. Generic questions waste the user's time. Example: *"In `packages/customer-mcp/tools/search.ts:42`, `search_users` takes 14 parameters including `filters.dateRange.start` — are all 14 used, or are most optional?"*

   If the user is unavailable for follow-up, switch to **draft mode**: surface the full prioritized finding set with explicit assumptions, but do not apply anything.

3. **Present findings one at a time.** Tie every finding to real code evidence, stated context, or a clearly labeled assumption. Thresholds in the reference docs (tool count, parameter count, latency) are diagnostic cues, not verdicts. Format:

   ```
   ### Finding [N]: [Title]
   Dimension: [category]   Severity: Critical / High / Medium / Low
   File(s): path/to/file.ts:line

   Current state: [their actual code snippet]
   Issue: [why it's suboptimal — reference the pattern]
   Options:
     - A (recommended): [description + tradeoff]
     - B: [description + tradeoff]
     - C (minimal change): [description + tradeoff]
   Should I apply this? (yes / no / show me option X first)
   ```

   Work by severity. Wait for the user's decision before moving to the next finding.

4. **Apply only after explicit approval.** Show the diff, explain the change, make the edit, and suggest a verification step — usually MCP Inspector or a `test-by-mcpc-cli` command against the modified tool.

### Mode B — Architect a new MCP from scratch

Pick Mode B when the user says "I want to build an MCP server" and no server exists yet (or the repo has one but the user wants a fresh one alongside). Do not start writing code. Instead:

1. **Run the brainstorm interview.** Open [`references/decision-trees/brainstorming-new-mcp.md`](references/decision-trees/brainstorming-new-mcp.md) and walk the user through its 12 questions: end-user task, local-vs-remote, auth, statefulness, target clients, expected tool count, destructive operations, distribution plan, advanced protocol needs (sampling, elicitation, roots), and a success metric. The file contains the full Q&A flow and a companion-skill picker.
2. **Produce an architecture sketch.** The brainstorming file gives you a template — surface, transport, auth shape, storage, advanced features used, testing plan, chosen companion skill. Keep it short.
3. **Get approval before handoff.** Present the sketch, ask the user to approve or adjust, then hand off to the right companion skill (see "Companion Skills" below).
4. **Smell-test with the design-phase tree.** Cross-check the sketch against [`references/decision-trees/design-phase.md`](references/decision-trees/design-phase.md) for cross-model schema portability and early architecture gotchas before handoff.

If the brainstorm exposes that MCP is the wrong primitive for the user's job (a CLI, a Claude skill, or a bash script would do), route to [`references/patterns/mcp-vs-cli.md`](references/patterns/mcp-vs-cli.md) and stop.

## Dispatching Subagents

You are the orchestrator. Fire subagents when a task needs more capacity than a single turn, but give them self-contained briefs with outcome, constraints, and a binary DoD.

- **`internet-researcher`** — any question about current spec (`auth-identity.md` references the 2025-11-25 profile), vendor pricing, platform quirks, or CVEs. Launch one per independent sub-question; run them in parallel when the questions don't depend on each other.
- **`general-purpose` (Opus 4+)** — multi-file edits, scaffolding a new MCP server per the architecture sketch, or applying a batch of approved optimizations after the user signs off.
- **`Plan`** — when a finding has 3+ competing architectural options (e.g. gateway vs split servers vs progressive discovery) and you want a structured tradeoff comparison before presenting.

Rules for the brief: observable end-state, hard constraints only, no step-by-step procedure. Grant ownership ("You own this — explore freely"). Keep DoD items binary and verifiable. Do not dispatch for work you can do in a single read-plus-edit round.

## Companion Skills

These skills actually build or test the server. This skill decides *what* to build and *why*; they decide *how*. Install command format (from the repo's root CLAUDE.md):

```
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>
```

| Skill | When to pick | Tradeoff |
|---|---|---|
| [`build-mcp-use-server`](../../../build-mcp-use-server/) | New HTTP-first TypeScript server, modern DX, want the `mcp-use` wrapper to handle transport, CORS, OAuth, sessions | Locks you into `mcp-use/server` imports and conventions; less bare-metal control |
| [`build-mcp-server-sdk-v1`](../../../build-mcp-server-sdk-v1/) | Canonical path: `@modelcontextprotocol/sdk` v1.x, single package, Zod v3, widest client compatibility, stdio or HTTP | Manual transport/OAuth wiring; deprecated overloads still compile so easy to pick wrong API |
| [`build-mcp-server-sdk-v2`](../../../build-mcp-server-sdk-v2/) | Only for new greenfield projects willing to accept beta. v2 split packages (`@modelcontextprotocol/server`), Zod v4, ESM-only, Node 20+ | Community adoption still early (Q1 2026 release); server-side OAuth removed; no CJS |
| [`test-by-mcpc-cli`](../../../test-by-mcpc-cli/) | Always useful once a server is running. Live CLI-based testing over stdio or Streamable HTTP, scripts, grep, task verification | Requires `mcpc 0.2.x` locally |

If the user's environment does not have the companion skill installed yet, tell them to run:

```
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>
```

substituting the skill name from the table above.

## Decision Tree — What Aspect Needs Attention?

Use this tree to jump into the right reference file. It covers both modes.

```
What aspect of the MCP server is in scope?
│
├── Brand new server, no code yet
│   └── references/decision-trees/brainstorming-new-mcp.md       (interview + framework picker)
│
├── Architecture decision — should this even be an MCP server?
│   └── references/patterns/mcp-vs-cli.md                        (MCP vs CLI / skills / bash)
│
├── Tool interface quality
│   ├── Tools feel like REST wrappers ───────── references/patterns/tool-design.md
│   ├── Model picks wrong tool ─────────────── references/patterns/tool-descriptions.md
│   └── Response doesn't guide next action ─── references/patterns/tool-responses.md
│
├── Input / output reliability
│   ├── Schema parse failures ──────────────── references/patterns/schema-design.md
│   ├── Errors don't help model recover ────── references/patterns/error-handling.md
│   ├── Choosing response format ───────────── references/decision-trees/response-format.md
│   └── Choosing error strategy ────────────── references/decision-trees/error-strategy.md
│
├── Security and identity
│   ├── Generic prompt-injection / sandbox ─── references/patterns/security.md
│   ├── Named attacks, CVEs, defense tooling ─ references/patterns/threat-catalog.md
│   ├── 2025-11-25 OAuth 2.1 / CIMD / OBO ──── references/patterns/auth-identity.md
│   └── Full security audit flow ───────────── references/decision-trees/security-posture.md
│
├── Context, tokens, and cost
│   ├── Context window exhaustion ──────────── references/patterns/context-engineering.md
│   ├── Provider prompt-caching + cost math ── references/patterns/caching-economics.md
│   ├── 20+ tools, eager registration ──────── references/decision-trees/tool-count.md
│   └── Progressive / dynamic tool loading ─── references/patterns/progressive-discovery.md
│
├── Protocol depth
│   ├── Sampling, elicitation, roots,
│   │   progress, cancellation, _meta ──────── references/patterns/advanced-protocol.md
│   ├── Resources + prompts usage ──────────── references/patterns/resources-and-prompts.md
│   └── Tool response authority / gates ────── references/patterns/prompt-gates.md
│
├── Client + model compatibility
│   ├── Per-client quirks & silent drops ───── references/patterns/client-compatibility.md
│   └── Per-model tool-use benchmarks ──────── references/patterns/model-behavior.md
│
├── Architecture & scaling
│   ├── Workflow / agent ordering ──────────── references/patterns/agentic-patterns.md
│   ├── Multi-server / gateway composition ─── references/patterns/composition.md
│   ├── Growth and load distribution ───────── references/decision-trees/scaling.md
│   └── Early design-time decisions ────────── references/decision-trees/design-phase.md
│
├── Operations, testing, deployment
│   ├── Transport choice + ops ─────────────── references/patterns/transport-and-ops.md
│   ├── Platform-specific hosting patterns ─── references/patterns/deployment-platforms.md
│   ├── Session / state lifecycle ──────────── references/patterns/session-and-state.md
│   ├── Test coverage and eval-driven dev ──── references/patterns/testing.md
│   └── Pre-deploy operational readiness ───── references/decision-trees/production-readiness.md
│
└── Distribution and trust
    ├── Vendor MCP servers to learn from ───── references/patterns/exemplar-servers.md
    └── Registries, gateways, trust signals ── references/patterns/registry-and-distribution.md
```

## Quick Reference Card

Common entry points across both modes.

| You want to... | Start here |
|---|---|
| Architect a brand-new MCP | `references/decision-trees/brainstorming-new-mcp.md` |
| Decide MCP vs CLI vs skill | `references/patterns/mcp-vs-cli.md` |
| Evaluate tool interface quality | `references/patterns/tool-design.md` → `references/patterns/tool-descriptions.md` |
| Fix schema parse failures | `references/patterns/schema-design.md` → `references/decision-trees/design-phase.md` |
| Improve error recovery | `references/decision-trees/error-strategy.md` → `references/patterns/error-handling.md` |
| Harden security posture | `references/decision-trees/security-posture.md` → `references/patterns/security.md` |
| Apply 2025-11-25 OAuth profile | `references/patterns/auth-identity.md` |
| Look up a named MCP attack or CVE | `references/patterns/threat-catalog.md` |
| Reduce context / token usage | `references/patterns/context-engineering.md` |
| Cut per-turn cost with prompt caching | `references/patterns/caching-economics.md` |
| Manage 20+ tools | `references/decision-trees/tool-count.md` → `references/patterns/progressive-discovery.md` |
| Add sampling, elicitation, or roots | `references/patterns/advanced-protocol.md` |
| Pick deployment platform | `references/patterns/deployment-platforms.md` |
| Design for a specific client's quirks | `references/patterns/client-compatibility.md` |
| Pick a default target model | `references/patterns/model-behavior.md` |
| Compare against vendor MCPs | `references/patterns/exemplar-servers.md` |
| Publish to the registry | `references/patterns/registry-and-distribution.md` |
| Validate with live tests | `references/patterns/testing.md` → companion skill `test-by-mcpc-cli` |
| Check production readiness | `references/decision-trees/production-readiness.md` → `references/patterns/transport-and-ops.md` |

## Common Pitfalls

| # | Pitfall | Fix |
|---|---|---|
| 1 | Wrapping every REST endpoint as a tool | Design around user intent — `references/patterns/tool-design.md` |
| 2 | Deeply nested JSON schemas | Flatten to ≤1 level, ≤6 params — `references/patterns/schema-design.md` |
| 3 | Returning raw API JSON | Curate and summarize — `references/patterns/tool-responses.md` |
| 4 | Throwing protocol errors for tool failures | Use `isError` in result content — `references/patterns/error-handling.md` |
| 5 | No input validation | Validate server-side — `references/patterns/security.md` |
| 6 | Registering 30+ tools at once | Progressive discovery — `references/patterns/progressive-discovery.md` |
| 7 | Vague tool descriptions | Treat descriptions as prompt engineering — `references/patterns/tool-descriptions.md` |
| 8 | No tests before production | Add tool + integration tests — `references/patterns/testing.md` |
| 9 | Using SSE for new remote deployments | Streamable HTTP only — `references/patterns/transport-and-ops.md` |
| 10 | Ignoring session cleanup | Lifecycle management — `references/patterns/session-and-state.md` |
| 11 | Invalidating prompt cache on every turn | Keep the prefix byte-identical — `references/patterns/caching-economics.md` |
| 12 | Assuming every client supports sampling/elicitation | Capability-gate first, fall back in tool response — `references/patterns/advanced-protocol.md` |
| 13 | Forwarding user tokens to upstream APIs | OBO with audience check — `references/patterns/auth-identity.md` |
| 14 | Publishing to v0 of the official registry | v0 is unstable; check trust tier — `references/patterns/registry-and-distribution.md` |
| 15 | Picking a platform before counting cold starts or session needs | Match shape to constraints — `references/patterns/deployment-platforms.md` |

## Reference Routing Table

### Pattern files (`references/patterns/`)

| File | Read when... |
|---|---|
| `tool-design.md` | Evaluating tool granularity, intent-based design, naming |
| `tool-descriptions.md` | Diagnosing tool selection, improving description quality |
| `tool-responses.md` | Optimizing return shape, picking output format, reducing tokens |
| `schema-design.md` | Fixing parse failures, flattening schemas, trimming required params |
| `error-handling.md` | Improving recovery, retry loops, circuit breakers |
| `security.md` | Generic defenses: injection vectors, sandboxing, auth basics |
| `threat-catalog.md` | Named MCP attacks (TPA, line jumping, FSP, ATPA, shadowing), dated CVEs, defense tooling, audit checklist |
| `auth-identity.md` | 2025-11-25 OAuth 2.1 profile, RFC 9728 PRM, CIMD, OBO, step-up consent |
| `context-engineering.md` | Token-budget diagnosis, context window optimization, tiered verbosity |
| `caching-economics.md` | Provider-side prompt caching (Anthropic, OpenAI, Gemini, Vertex, Bedrock), write premiums, TTL, cost math |
| `progressive-discovery.md` | Managing 20+ tools, dynamic tool loading |
| `agentic-patterns.md` | Agent loops, multi-step workflows, ordering constraints |
| `composition.md` | Multi-server setups, gateway federation, meta-server patterns |
| `prompt-gates.md` | Tool response authority, approval workflows, guardrails |
| `resources-and-prompts.md` | Resource and prompt primitive usage, data-exposure strategy |
| `session-and-state.md` | Session lifecycle, state leaks, cleanup, application-level caching |
| `testing.md` | Eval-driven development, regression testing, CI integration |
| `transport-and-ops.md` | Transport choice, deployment config, monitoring, connection management |
| `deployment-platforms.md` | Cloudflare Workers, Vercel, Lambda, Cloud Run, ACA, Modal, Fly, Smithery specifics |
| `mcp-vs-cli.md` | Deciding whether MCP is the right primitive vs CLI, bash, skills, or hybrid |
| `client-compatibility.md` | Per-client truth table — silent drops, partial support, workarounds |
| `model-behavior.md` | Per-model tool-use benchmarks (BFCL, MCP-Atlas, MCPMark), idioms, pricing |
| `advanced-protocol.md` | Sampling, elicitation, roots, completions, progress, cancellation, `_meta` |
| `exemplar-servers.md` | Comparing design against 16 production vendors (GitHub, Linear, Stripe, Notion, Sentry, Figma, Atlassian Rovo, Cloudflare, PayPal, Shopify, Asana V2, Supabase, HubSpot, Vercel, Intercom, Zapier) |
| `registry-and-distribution.md` | Official Registry, Smithery, Docker MCP Catalog, gateways, trust signals, namespaces |

### Decision-tree files (`references/decision-trees/`)

| File | Read when... |
|---|---|
| `brainstorming-new-mcp.md` | Mode B — user wants to architect a new MCP; interview + companion-skill picker + sketch template |
| `design-phase.md` | Early architecture decisions, cross-model schema portability |
| `tool-count.md` | How many tools to expose; organizing a large surface |
| `response-format.md` | Text vs structured content vs mixed |
| `error-strategy.md` | Fail-fast vs retry vs fallback |
| `security-posture.md` | Threat model selection, full security audit flow |
| `scaling.md` | Growth, multi-server setups, load distribution |
| `production-readiness.md` | Pre-deploy checklist, operational readiness |

## Guardrails

Non-negotiables that apply to both modes.

- **Explore before asking.** Run the searches, read the files, and only then ask questions that cite specific paths and lines.
- **Ask before optimizing.** Never apply a pattern without presenting it as a finding with options and getting explicit approval.
- **One finding at a time in interactive mode.** Work by severity. Wait for the user's decision before moving on.
- **Draft mode is for follow-up gaps only.** Label every assumption; do not apply code changes in draft mode.
- **Show real code.** Every finding quotes the user's actual code with file paths and line numbers. No hypothetical examples.
- **Scope one server at a time.** Inventory multiple servers first; ask which is in scope unless the user asked for a repo-wide audit.
- **Thresholds are heuristics, not verdicts.** Tool count, parameter count, latency, and token budgets are ground truth-able; don't weaponize them as rules.
- **Verify after applying.** Every optimization gets a verification step — MCP Inspector, `test-by-mcpc-cli` command, or a targeted manual check.
- **Do not wrap REST endpoints one-to-one.** Map tools to user intent.
- **Do not deeply nest schemas.** Flatten past one level. LLMs reliably generate flat structures.
- **Do not return raw upstream JSON.** Always curate, summarize, and format for LLM consumption.
- **Do not use protocol errors for business failures.** Reserve protocol errors for transport and framework issues.
- **Do not eagerly register 20+ tools.** Use progressive discovery.
- **Do not skip input validation.** Never trust LLM-generated input.
- **Do not use SSE for new remote deployments.** Streamable HTTP only.
- **Do not undervalue descriptions.** They are the model's primary tool-selection signal — treat them as prompt engineering.
- **Do not return sensitive data in tool responses.** Anything returned enters the LLM context.
- **Do not deploy without tests.** At minimum: valid input, invalid input, upstream failure.
- **Do not forward user tokens to upstream APIs.** Use OBO (on-behalf-of) with audience checks — see `references/patterns/auth-identity.md`.
- **Do not silently drop advanced-protocol features.** Capability-gate sampling, elicitation, and roots; fall back gracefully — see `references/patterns/advanced-protocol.md`.
- **Do not publish to v0 of the official registry.** Wait for a stable API revision — see `references/patterns/registry-and-distribution.md`.
