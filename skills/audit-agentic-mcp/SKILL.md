---
name: audit-agentic-mcp
description: "Use skill if you are auditing an existing MCP server for agent-readiness, designing a new MCP server before any code, or deciding framework, security, and context posture."
---

# audit-agentic-mcp — Audit, Optimize, Architect MCP Servers

The agent-readiness front door for MCP servers. Decides what is wrong, what should change, which reference applies, which companion skill implements the fix, and how to verify the result.

This skill **does not write SDK code**. It diagnoses, prescribes, and routes.

## When to use

*Trigger when the user asks any of:*

- *"audit my MCP server"* / *"review this MCP server"* / *"is my MCP server agent-ready?"*
- *"optimize my MCP server"* / *"my agent keeps misusing this tool — what's wrong?"*
- *"design a new MCP server"* / *"should this be an MCP or a CLI?"*
- *"score this MCP server's tool design / schemas / auth / context budget"*
- *"my MCP server returns too much context"* / *"my agent picks the wrong tool"*
- *"harden my MCP server"* / *"production-readiness check for MCP"*
- *"which MCP framework should I pick — SDK v1, SDK v2, or `mcp-use`?"*

**Do NOT use this skill for:**

- Writing or fixing raw `@modelcontextprotocol/sdk` v1 code → route to `build-mcp-server-sdk-v1`
- Writing or fixing raw `@modelcontextprotocol/server` v2 alpha code → route to `build-mcp-server-sdk-v2`
- Writing or fixing `mcp-use/server` code → route to `build-mcp-use-server`
- Live CLI smoke-testing of an MCP server → route to `test-by-mcpc-cli`
- Enforcing TypeScript Clean Architecture layering on `mcp-use/server` → route to `build-clean-mcp-architecture`
- CLI agent-readiness (not MCP) → route to `audit-agentic-cli`
- Migrating SDK v1 code to v2 → route to `convert-mcp-sdk-v1-to-v2`

## Hard rules (load-bearing)

| # | Rule | Reference |
|---|---|---|
| 1 | Explore the codebase before asking. Run helper scripts and `rg` first. | `scripts/audit-mcp-server.sh.md` |
| 2 | Audit requests stop at the report. Optimize/fix requests apply edits and verify. | — |
| 3 | Every finding cites file path and line, real code or labeled assumption. | — |
| 4 | One server at a time. If multiple servers exist, inventory and ask which is in scope. | — |
| 5 | Map tools to user intent — never wrap REST endpoints one-to-one. | `references/patterns/tool-design.md` |
| 6 | Flatten schemas past one nesting level; keep 3–6 required params. | `references/patterns/schema-design.md` |
| 7 | Curate tool responses for LLM consumption — never return raw upstream JSON. | `references/patterns/tool-responses.md` |
| 8 | Use `isError` in result content for tool failures. Reserve protocol errors for transport. | `references/patterns/error-handling.md` |
| 9 | Validate all LLM input server-side; never trust generated input. | `references/patterns/security.md` |
| 10 | Use Streamable HTTP for new remote deployments — not SSE. | `references/patterns/transport-and-ops.md` |
| 11 | Use progressive discovery past ~20 tools, not eager registration. | `references/patterns/progressive-discovery.md` |
| 12 | Tool descriptions are prompt engineering — treat them with care. | `references/patterns/tool-descriptions.md` |
| 13 | Capability-gate sampling, elicitation, and roots — never silently drop. | `references/patterns/advanced-protocol.md` |
| 14 | Use OBO with audience checks; never forward user tokens to upstream APIs. | `references/patterns/auth-identity.md` |
| 15 | Verify after every applied edit. Pick one live route. | `references/patterns/testing.md` + `test-by-mcpc-cli` |

## Two modes

### Mode A — Audit / optimize an existing MCP server

Pick this when MCP-shaped code already exists.

1. **Explore.** Start with the helper scripts:
   ```bash
   bash skills/audit-agentic-mcp/skills/audit-agentic-mcp/scripts/audit-mcp-server.sh .
   bash skills/audit-agentic-mcp/skills/audit-agentic-mcp/scripts/measure-context-budget.sh .
   ```
   Then confirm with direct searches:
   ```bash
   tree . -I node_modules --dirsfirst -L 3
   rg -n -l "McpServer|FastMCP|server\.tool|@tool|@mcp\.tool|registerTool|Server\(" . -g '!node_modules'
   rg -n "server\.tool|@tool|registerTool|def .*tool|tool\(" . -g '!node_modules'
   rg -n -l "z\.|inputSchema|BaseModel|Field\(|pydantic|jsonschema" . -g '!node_modules'
   rg -n "stdio|streamable|sse|transport" . -g '!node_modules'
   ```
   See `scripts/audit-mcp-server.sh.md` and `scripts/measure-context-budget.sh.md` for what the helpers cover and what to read next.

   If `tree` is missing, `find . -maxdepth 3 -type d`. If `rg` is missing, `grep -R`. If no MCP-shaped code exists after checking root and likely server dirs (`src/`, `server/`, `servers/`, `app/`, `apps/`, `packages/`, `services/`, `mcp/`), report the missing prerequisite and switch to Mode B only if the user actually wants a new server.

2. **Detect framework, then route mechanics.** Read manifest, entry point, tool registration, schemas, transport/auth config. Keep this skill on audit reasoning; route implementation mechanics to the companion table below.

3. **Score and prioritize.** Produce the audit Output Contract below. Tie every finding to real evidence or a labeled assumption. Thresholds in references are diagnostic cues, not verdicts.

4. **Apply only in implementation scope.** For optimize/fix, edit the in-scope findings and verify with one live route. For audit/review, stop at the report.

#### Audit Output Contract

- target path and detected framework
- short scorecard across: tool interface, schemas/responses, errors, security/auth, context/cost, client compatibility, ops/testing, and architecture
- prioritized findings — each with severity, evidence path/line, impact, recommended fix, companion-skill route
- verification plan: `test-by-mcpc-cli`, MCP Inspector, unit/integration, or targeted manual check
- assumptions and items not touched

### Mode B — Architect a new MCP server

Pick this when no MCP-shaped code exists yet, or the user wants a fresh server alongside an existing one.

1. Run the interview in `references/decision-trees/brainstorming-new-mcp.md`.
2. Choose framework and companion via `references/decision-trees/companion-toolchain.md`.
3. Cross-check the sketch with `references/decision-trees/design-phase.md` for schema portability and architecture gotchas.
4. If MCP is the wrong primitive, route to `references/patterns/mcp-vs-cli.md` and recommend CLI, agent skill, or a smaller script instead.
5. Hand off to the chosen companion only after the architecture sketch is signed off.

#### Architect Output Contract

- chosen framework and companion skill
- why MCP is better than CLI, agent skill, or a smaller primitive — sourced from `references/patterns/mcp-vs-cli.md`
- security posture, context-budget posture, and production-readiness risks
- validation plan before and after implementation

## Minimal read sets

Do not load the whole reference tree by default. Start with the smallest bundle.

| Work | Read first |
|---|---|
| Existing-server quick audit | `scripts/audit-mcp-server.sh.md`, `scripts/measure-context-budget.sh.md`, `references/patterns/tool-design.md`, `references/patterns/schema-design.md`, `references/patterns/tool-responses.md`, `references/patterns/error-handling.md`, `references/patterns/testing.md` |
| Security / auth audit | `references/decision-trees/security-posture.md`, `references/patterns/security.md`, `references/patterns/auth-identity.md`, `references/patterns/threat-catalog.md` |
| Context / cost audit | `scripts/measure-context-budget.sh.md`, `references/patterns/context-engineering.md`, `references/patterns/caching-economics.md`, `references/decision-trees/tool-count.md`, `references/patterns/progressive-discovery.md` |
| New-server architecture | `references/decision-trees/brainstorming-new-mcp.md`, `references/decision-trees/companion-toolchain.md`, `references/decision-trees/design-phase.md`, `references/patterns/mcp-vs-cli.md` |

## Companion skills (route fixes here)

| Skill | When to pick | Tradeoff |
|---|---|---|
| [`build-mcp-server-sdk-v1`](../../../build-mcp-server-sdk-v1/) | Production-default raw SDK with widest client compatibility, stdio or HTTP | Manual transport/OAuth wiring; deprecated overloads still compile |
| [`build-mcp-server-sdk-v2`](../../../build-mcp-server-sdk-v2/) | New greenfield projects accepting v2 alpha risk after checking npm and docs | Alpha APIs can change; Node 20+/ESM/Zod v4; no server-side OAuth |
| [`build-mcp-use-server`](../../../build-mcp-use-server/) | New HTTP-first TypeScript server wanting `mcp-use/server` conventions, widgets/apps, OAuth helpers | Locks into `mcp-use/server` imports; less bare-metal control |
| [`convert-mcp-sdk-v1-to-v2`](../../../convert-mcp-sdk-v1-to-v2/) | Migrating existing SDK v1 code to v2 alpha | Targets the migration only |
| [`test-by-mcpc-cli`](../../../test-by-mcpc-cli/) | Repeatable stdio/Streamable HTTP smoke checks, JSON scripting, post-edit verification | Requires `mcpc 0.2.x` locally |
| [`build-clean-mcp-architecture`](../../../build-clean-mcp-architecture/) | TypeScript `mcp-use/server` audit hits layer-boundary, folder-layout, or dependency-direction issues | Layer discipline; not a replacement for this agent-readiness audit |
| [`audit-agentic-cli`](../../../audit-agentic-cli/) | The interface should stay CLI-first or the task is CLI agent-readiness, not MCP | CLI contract work, not MCP protocol work |

## Execution rhythm

- Audit/review request → produce the full audit report and stop. No code edits.
- Optimize/fix request with clear scope → state assumptions and tradeoffs upfront, apply in-scope edits, verify.
- Ask only when the target server is ambiguous, multiple servers are in scope and the user did not request a repo-wide audit, or the next action is destructive or externally visible.
- After every applied optimization, pick one live verification route: `test-by-mcpc-cli`, MCP Inspector, unit/integration test, or targeted manual endpoint check.

## Decision tree — what aspect needs attention?

```
What aspect of the MCP server is in scope?
│
├── Brand new server, no code yet
│   ├── references/decision-trees/brainstorming-new-mcp.md
│   └── references/decision-trees/companion-toolchain.md
│
├── Architecture decision — should this even be an MCP server?
│   └── references/patterns/mcp-vs-cli.md
│
├── Tool interface quality
│   ├── REST-wrapper tools ───────────── references/patterns/tool-design.md
│   ├── Wrong tool selected ──────────── references/patterns/tool-descriptions.md
│   └── Weak next-action guidance ────── references/patterns/tool-responses.md
│
├── Input / output reliability
│   ├── Schema parse failures ────────── references/patterns/schema-design.md
│   ├── Poor recovery errors ─────────── references/patterns/error-handling.md
│   ├── Response format choice ───────── references/decision-trees/response-format.md
│   └── Error strategy choice ────────── references/decision-trees/error-strategy.md
│
├── Security and identity
│   ├── Security posture flow ────────── references/decision-trees/security-posture.md
│   ├── Generic defenses ─────────────── references/patterns/security.md
│   ├── OAuth / CIMD / OBO ───────────── references/patterns/auth-identity.md
│   └── Named attacks / CVEs ─────────── references/patterns/threat-catalog.md
│
├── Context, tokens, and cost
│   ├── Context budget ───────────────── references/patterns/context-engineering.md
│   ├── Prompt-caching economics ─────── references/patterns/caching-economics.md
│   ├── Tool count cliffs ────────────── references/decision-trees/tool-count.md
│   └── Progressive loading ──────────── references/patterns/progressive-discovery.md
│
├── Protocol depth
│   ├── Sampling / elicitation / roots ─ references/patterns/advanced-protocol.md
│   ├── Resources + prompts ──────────── references/patterns/resources-and-prompts.md
│   └── Tool response authority ──────── references/patterns/prompt-gates.md
│
├── Client + model compatibility
│   ├── Per-client quirks ────────────── references/patterns/client-compatibility.md
│   └── Per-model behavior ───────────── references/patterns/model-behavior.md
│
├── Architecture & scaling
│   ├── Agentic workflows ────────────── references/patterns/agentic-patterns.md
│   ├── Multi-server composition ─────── references/patterns/composition.md
│   ├── Growth / load distribution ───── references/decision-trees/scaling.md
│   └── Early design decisions ───────── references/decision-trees/design-phase.md
│
├── Operations, testing, deployment
│   ├── Transport + ops ──────────────── references/patterns/transport-and-ops.md
│   ├── Hosting platforms ────────────── references/patterns/deployment-platforms.md
│   ├── Session lifecycle ────────────── references/patterns/session-and-state.md
│   ├── Testing strategy ─────────────── references/patterns/testing.md
│   └── Production readiness ─────────── references/decision-trees/production-readiness.md
│
└── Distribution and trust
    ├── Vendor exemplars ─────────────── references/patterns/exemplar-servers.md
    └── Registries / gateways ───────── references/patterns/registry-and-distribution.md
```

## Quick reference card

| You want to... | Start here |
|---|---|
| Architect a brand-new MCP | `references/decision-trees/brainstorming-new-mcp.md` → `references/decision-trees/companion-toolchain.md` |
| Decide MCP vs CLI vs agent skill | `references/patterns/mcp-vs-cli.md` |
| Evaluate tool interface quality | `references/patterns/tool-design.md` → `references/patterns/tool-descriptions.md` |
| Fix schema parse failures | `references/patterns/schema-design.md` → `references/decision-trees/design-phase.md` |
| Improve error recovery | `references/decision-trees/error-strategy.md` → `references/patterns/error-handling.md` |
| Harden security posture | `references/decision-trees/security-posture.md` → `references/patterns/security.md` → `references/patterns/auth-identity.md` |
| Reduce context / token usage | `scripts/measure-context-budget.sh.md` → `references/patterns/context-engineering.md` |
| Manage 20+ tools | `references/decision-trees/tool-count.md` → `references/patterns/progressive-discovery.md` |
| Add sampling, elicitation, or roots | `references/patterns/advanced-protocol.md` |
| Pick deployment platform | `references/patterns/deployment-platforms.md` |
| Design for a specific client | `references/patterns/client-compatibility.md` |
| Publish to a registry | `references/patterns/registry-and-distribution.md` |
| Validate with live tests | `references/patterns/testing.md` → `test-by-mcpc-cli` |

## Common pitfalls

| # | Pitfall | Fix |
|---|---|---|
| 1 | Wrapping every REST endpoint as a tool | Design around user intent — `references/patterns/tool-design.md` |
| 2 | Deeply nested JSON schemas | Flatten to one level, 3–6 params — `references/patterns/schema-design.md` |
| 3 | Returning raw API JSON | Curate and summarize — `references/patterns/tool-responses.md` |
| 4 | Throwing protocol errors for tool failures | Use `isError` in result content — `references/patterns/error-handling.md` |
| 5 | No input validation | Validate server-side — `references/patterns/security.md` |
| 6 | Registering 20+ tools eagerly | Progressive discovery — `references/patterns/progressive-discovery.md` |
| 7 | Vague tool descriptions | Treat descriptions as prompt engineering — `references/patterns/tool-descriptions.md` |
| 8 | No live verification after edits | Use `test-by-mcpc-cli`, Inspector, unit tests, or endpoint checks |
| 9 | Using SSE for new remote deployments | Streamable HTTP only — `references/patterns/transport-and-ops.md` |
| 10 | Ignoring session cleanup | Lifecycle management — `references/patterns/session-and-state.md` |

## Reference routing table

### Pattern files (`references/patterns/`)

| File | Read when... |
|---|---|
| `tool-design.md` | Evaluating tool granularity, intent-based design, naming |
| `tool-descriptions.md` | Diagnosing tool selection, improving description quality |
| `tool-responses.md` | Optimizing return shape, picking output format, reducing tokens |
| `schema-design.md` | Fixing parse failures, flattening schemas, trimming required params |
| `error-handling.md` | Improving recovery, retry loops, circuit breakers |
| `security.md` | Generic defenses: injection vectors, sandboxing, auth basics |
| `threat-catalog.md` | Named MCP attacks, dated CVEs, defense tooling, audit checklist |
| `auth-identity.md` | OAuth profile, RFC 9728 PRM, CIMD, OBO, step-up consent |
| `context-engineering.md` | Token-budget diagnosis, context window optimization, tiered verbosity |
| `caching-economics.md` | Provider-side prompt caching, write premiums, TTL, cost math |
| `progressive-discovery.md` | Managing 20+ tools, dynamic tool loading |
| `agentic-patterns.md` | Agent loops, multi-step workflows, ordering constraints |
| `composition.md` | Multi-server setups, gateway federation, meta-server patterns |
| `prompt-gates.md` | Tool response authority, approval workflows, guardrails |
| `resources-and-prompts.md` | Resource and prompt primitive usage, data-exposure strategy |
| `session-and-state.md` | Session lifecycle, state leaks, cleanup, application-level caching |
| `testing.md` | Eval-driven development, regression testing, CI integration |
| `transport-and-ops.md` | Transport choice, deployment config, monitoring, connection management |
| `deployment-platforms.md` | Hosting platforms and deployment constraints |
| `mcp-vs-cli.md` | Deciding whether MCP is the right primitive vs CLI, bash, skills, or hybrid |
| `client-compatibility.md` | Per-client truth table, silent drops, partial support, workarounds |
| `model-behavior.md` | Per-model tool-use benchmarks, idioms, pricing |
| `advanced-protocol.md` | Sampling, elicitation, roots, completions, progress, cancellation, `_meta` |
| `exemplar-servers.md` | Comparing design against production vendor servers |
| `registry-and-distribution.md` | Official Registry, Smithery, Docker MCP Catalog, gateways, trust signals |

### Decision-tree files (`references/decision-trees/`)

| File | Read when... |
|---|---|
| `brainstorming-new-mcp.md` | Mode B interview, framework picker, architecture sketch |
| `companion-toolchain.md` | Choosing build, test, architecture, CLI, or no-MCP companion route |
| `design-phase.md` | Early architecture decisions, cross-model schema portability |
| `tool-count.md` | How many tools to expose; organizing a large surface |
| `response-format.md` | Text vs structured content vs mixed |
| `error-strategy.md` | Fail-fast vs retry vs fallback |
| `security-posture.md` | Threat model selection, full security audit flow |
| `scaling.md` | Growth, multi-server setups, load distribution |
| `production-readiness.md` | Pre-deploy checklist, operational readiness |

## Freshness checks

Before making version-sensitive claims, verify current MCP SDK, `mcp-use`, client compatibility, pricing, CVEs, and registry status from primary sources. Start with npm package metadata and the official TypeScript SDK repository/release notes when framework guidance depends on SDK state.

Time-sensitive references — re-check before citing:

- `references/patterns/auth-identity.md`
- `references/patterns/client-compatibility.md`
- `references/patterns/caching-economics.md`
- `references/patterns/deployment-platforms.md`
- `references/patterns/model-behavior.md`
- `references/patterns/registry-and-distribution.md`
- `references/patterns/threat-catalog.md`

## Delegation policy

Use subagents only when the runtime supports them and project policy allows it. Delegate independent current-research questions, broad codebase scans, or batch implementation after the user has authorized implementation scope. Pass outcome, constraints, and binary done criteria. Do not delegate work that is faster as a local read-plus-edit.
