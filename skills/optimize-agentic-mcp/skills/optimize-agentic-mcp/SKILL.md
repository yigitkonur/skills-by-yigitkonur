---
name: optimize-agentic-mcp
description: "Use skill if you are auditing, optimizing, or architecting MCP servers for agent-readiness: framework choice, security, context budget, verification, and companion skills."
---

# MCP Server Skill — Audit, Optimize, Architect

Use this skill as the agent-readiness front door for MCP servers. It decides what is wrong, what should change, which reference set applies, which companion skill should handle implementation mechanics, and how the result should be verified.

## Trigger Boundary

Use this skill for:

- auditing or optimizing an existing MCP server for agent-readiness
- assessing tool design, schemas, responses, error recovery, security, auth, context/cost, client compatibility, and production readiness
- architecting a new MCP server before implementation, including framework and companion-skill choice

Do not use this skill for:

- raw implementation mechanics in `@modelcontextprotocol/sdk` v1 or v2 — route to `build-mcp-server-sdk-v1` or `build-mcp-server-sdk-v2`
- `mcp-use/server` implementation mechanics — route to `build-mcp-use-server`
- live CLI-only verification — route to `test-by-mcpc-cli`
- TypeScript Clean Architecture enforcement for `mcp-use` servers — route to `apply-clean-mcp-architecture`
- CLI agent-readiness work — route to `optimize-agentic-cli`

## Output Contract

For existing-server audits, the output must include:

- target path and detected framework
- short scorecard across tool interface, schemas/responses, errors, security/auth, context/cost, client compatibility, ops/testing, and architecture
- prioritized findings with severity, evidence path/line, impact, recommended fix, and companion-skill route
- verification plan: usually `test-by-mcpc-cli`, MCP Inspector, unit/integration tests, or targeted manual checks
- assumptions and items not touched

For new-server architecture, produce the existing architecture sketch from `references/decision-trees/brainstorming-new-mcp.md` and explicitly include:

- chosen framework and companion skill
- why MCP is better than CLI, an agent skill, or a smaller primitive
- security posture, context-budget posture, and production-readiness risks
- validation plan before and after implementation

Named surfaces map to these references:

| Surface | Read set |
|---|---|
| Security posture | `references/decision-trees/security-posture.md`, `references/patterns/security.md`, `references/patterns/auth-identity.md`, `references/patterns/threat-catalog.md` |
| Context budget | `references/patterns/context-engineering.md`, `references/patterns/caching-economics.md`, `references/decision-trees/tool-count.md`, `references/patterns/progressive-discovery.md` |
| Companion toolchain | `references/decision-trees/companion-toolchain.md` |

## Execution Rhythm

- If the user asks for an audit or review, produce the complete audit report and stop without code edits.
- If the user asks to optimize or fix and scope is clear, apply the in-scope fixes after upfront assumptions and any meaningful tradeoff block.
- Keep interactive "finding-by-finding" review only when the user explicitly asks for review-only guidance.
- Ask only when the target server is ambiguous, multiple MCP servers are in scope and the user did not request a repo-wide audit, or the next action is destructive or externally visible.
- After every applied optimization, pick one live verification route: `test-by-mcpc-cli`, MCP Inspector, unit/integration test, or targeted manual endpoint check.

## Minimal Read Sets

Do not load the whole reference tree by default. Start with the smallest bundle that fits.

| Work | Read first |
|---|---|
| Existing server quick audit | `scripts/audit-mcp-server.sh`, `scripts/measure-context-budget.sh`, `references/patterns/tool-design.md`, `references/patterns/schema-design.md`, `references/patterns/tool-responses.md`, `references/patterns/error-handling.md`, `references/patterns/testing.md` |
| Security/auth audit | `references/decision-trees/security-posture.md`, `references/patterns/security.md`, `references/patterns/auth-identity.md`, `references/patterns/threat-catalog.md` |
| Context/cost audit | `scripts/measure-context-budget.sh`, `references/patterns/context-engineering.md`, `references/patterns/caching-economics.md`, `references/decision-trees/tool-count.md`, `references/patterns/progressive-discovery.md` |
| New server architecture | `references/decision-trees/brainstorming-new-mcp.md`, `references/decision-trees/companion-toolchain.md`, `references/decision-trees/design-phase.md`, `references/patterns/mcp-vs-cli.md` |

## Mode A — Audit or Optimize an Existing MCP Server

Pick Mode A when the user already has an MCP server and wants it improved, audited, hardened, or reviewed.

1. **Explore the codebase.** Read the repo before asking questions. Start with the helper scripts when available:

   ```bash
   bash skills/optimize-agentic-mcp/skills/optimize-agentic-mcp/scripts/audit-mcp-server.sh .
   bash skills/optimize-agentic-mcp/skills/optimize-agentic-mcp/scripts/measure-context-budget.sh .
   ```

   Then confirm with direct searches:

   ```bash
   tree . -I node_modules --dirsfirst -L 3
   rg -n -l "McpServer|FastMCP|server\\.tool|@tool|@mcp\\.tool|registerTool|Server\\(" . -g '!node_modules'
   rg -n "server\\.tool|@tool|registerTool|def .*tool|tool\\(" . -g '!node_modules'
   rg -n -l "z\\.|inputSchema|BaseModel|Field\\(|pydantic|jsonschema" . -g '!node_modules'
   rg -n "stdio|streamable|sse|transport" . -g '!node_modules'
   ```

   If `tree` is missing, use `find . -maxdepth 3 -type d`. If `rg` is missing, use `grep -R`. If no MCP-shaped code exists after checking root and likely server directories (`src/`, `server/`, `servers/`, `app/`, `apps/`, `packages/`, `services/`, `mcp/`), report the missing prerequisite and switch to Mode B only if the user actually wants a new server.

2. **Detect framework, then route mechanics.** Read manifest, entry point, tool registration, schemas, transport/auth config. Keep this skill on audit reasoning; route implementation mechanics to the companion table below.

3. **Score and prioritize.** Produce the Output Contract scorecard. Tie every finding to real code evidence, stated context, or a labeled assumption. Thresholds in the references are diagnostic cues, not verdicts.

4. **Apply only in implementation scope.** For optimize/fix requests, edit the in-scope findings and verify. For audit/review requests, stop at the report.

## Mode B — Architect a New MCP Server

Pick Mode B when the user says they want to build an MCP server and no server exists yet, or they want a fresh server alongside an existing one.

1. Open `references/decision-trees/brainstorming-new-mcp.md` and run the interview.
2. Open `references/decision-trees/companion-toolchain.md` to choose the companion skill and non-MCP alternatives.
3. Cross-check the sketch with `references/decision-trees/design-phase.md` for schema portability and early architecture gotchas.
4. If MCP is the wrong primitive for the job, route to `references/patterns/mcp-vs-cli.md` and recommend CLI, existing CLI, agent skill, or a smaller script instead.
5. Produce the architecture sketch with the chosen companion skill and validation plan. Hand off to the companion skill only after the architecture is clear.

## Delegation Policy

Use subagents only when the runtime supports them and local protocol allows it. Delegate independent current-research questions, broad codebase scans, or batch implementation after the user has authorized implementation scope. Pass outcome, constraints, and binary done criteria. Do not delegate work that is faster as a local read-plus-edit.

## Audit vs Build Skills

| Skill | Owns |
|---|---|
| `optimize-agentic-mcp` | Decide what is wrong and why: agent-readiness, security, context, compatibility, architecture choice |
| `build-mcp-server-sdk-v1` | Implement or maintain raw SDK v1 details |
| `build-mcp-server-sdk-v2` | Implement or maintain raw SDK v2 alpha details |
| `build-mcp-use-server` | Implement or maintain `mcp-use/server` details |

## Companion Skills

These skills build, enforce, or test what this skill recommends. Install format from the repo's root AGENTS.md or project instructions:

```bash
npx -y skills add -y -g yigitkonur/skills-by-yigitkonur/skills/<skill-name>
```

| Skill | When to pick | Tradeoff |
|---|---|---|
| [`build-mcp-use-server`](../../../build-mcp-use-server/) | New HTTP-first TypeScript server that wants `mcp-use/server` conventions, widgets/apps, OAuth helpers, and modern DX | Locks into `mcp-use/server` imports and conventions; less bare-metal control |
| [`build-mcp-server-sdk-v1`](../../../build-mcp-server-sdk-v1/) | Production-default raw SDK path with `@modelcontextprotocol/sdk` v1.x, widest client compatibility, stdio or HTTP | Manual transport/OAuth wiring; deprecated overloads still compile |
| [`build-mcp-server-sdk-v2`](../../../build-mcp-server-sdk-v2/) | New greenfield projects willing to accept the current `@modelcontextprotocol/server` v2 alpha risk after checking npm and docs | Alpha APIs can change; Node 20+/ESM/Zod v4 constraints; server-side OAuth removed |
| [`test-by-mcpc-cli`](../../../test-by-mcpc-cli/) | Repeatable stdio/Streamable HTTP smoke checks, JSON scripting, schema inspection, and post-optimization live verification | Requires `mcpc 0.2.x` locally |
| [`apply-clean-mcp-architecture`](../../../apply-clean-mcp-architecture/) | TypeScript `mcp-use/server` audit finds layer-boundary, folder-layout, dependency-direction, or TypeScript quality issues | Positive routing for layer discipline; not a replacement for this agent-readiness audit |
| `optimize-agentic-cli` | The interface should stay CLI-first or the task is CLI agent-readiness, not MCP server design | CLI contract work, not MCP protocol work |

## Freshness Checks

Before making version-sensitive claims, verify current MCP SDK, `mcp-use`, client compatibility, pricing, CVEs, and registry status from primary sources. Start with npm package metadata and the official TypeScript SDK repository/release notes when framework guidance depends on SDK state.

Time-sensitive references to re-check before citing:

- `references/patterns/auth-identity.md`
- `references/patterns/client-compatibility.md`
- `references/patterns/caching-economics.md`
- `references/patterns/deployment-platforms.md`
- `references/patterns/model-behavior.md`
- `references/patterns/registry-and-distribution.md`
- `references/patterns/threat-catalog.md`

## Decision Tree — What Aspect Needs Attention?

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
│   └── Weak next action guidance ────── references/patterns/tool-responses.md
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

## Quick Reference Card

| You want to... | Start here |
|---|---|
| Architect a brand-new MCP | `references/decision-trees/brainstorming-new-mcp.md` → `references/decision-trees/companion-toolchain.md` |
| Decide MCP vs CLI vs agent skill | `references/patterns/mcp-vs-cli.md` |
| Evaluate tool interface quality | `references/patterns/tool-design.md` → `references/patterns/tool-descriptions.md` |
| Fix schema parse failures | `references/patterns/schema-design.md` → `references/decision-trees/design-phase.md` |
| Improve error recovery | `references/decision-trees/error-strategy.md` → `references/patterns/error-handling.md` |
| Harden security posture | `references/decision-trees/security-posture.md` → `references/patterns/security.md` → `references/patterns/auth-identity.md` |
| Reduce context / token usage | `scripts/measure-context-budget.sh` → `references/patterns/context-engineering.md` |
| Manage 20+ tools | `references/decision-trees/tool-count.md` → `references/patterns/progressive-discovery.md` |
| Add sampling, elicitation, or roots | `references/patterns/advanced-protocol.md` |
| Pick deployment platform | `references/patterns/deployment-platforms.md` |
| Design for a specific client | `references/patterns/client-compatibility.md` |
| Publish to a registry | `references/patterns/registry-and-distribution.md` |
| Validate with live tests | `references/patterns/testing.md` → `test-by-mcpc-cli` |

## Common Pitfalls

| # | Pitfall | Fix |
|---|---|---|
| 1 | Wrapping every REST endpoint as a tool | Design around user intent — `references/patterns/tool-design.md` |
| 2 | Deeply nested JSON schemas | Flatten to one level, 3-6 params — `references/patterns/schema-design.md` |
| 3 | Returning raw API JSON | Curate and summarize — `references/patterns/tool-responses.md` |
| 4 | Throwing protocol errors for tool failures | Use `isError` in result content — `references/patterns/error-handling.md` |
| 5 | No input validation | Validate server-side — `references/patterns/security.md` |
| 6 | Registering 20+ tools eagerly | Progressive discovery — `references/patterns/progressive-discovery.md` |
| 7 | Vague tool descriptions | Treat descriptions as prompt engineering — `references/patterns/tool-descriptions.md` |
| 8 | No live verification after edits | Use `test-by-mcpc-cli`, Inspector, unit tests, or endpoint checks |
| 9 | Using SSE for new remote deployments | Streamable HTTP only — `references/patterns/transport-and-ops.md` |
| 10 | Ignoring session cleanup | Lifecycle management — `references/patterns/session-and-state.md` |

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

## Guardrails

- Explore before asking. Run the searches, read the files, then ask only questions that cite specific paths and lines.
- Scope one server at a time. Inventory multiple servers first; ask which is in scope unless the user asked for a repo-wide audit.
- Report audits; edit only when the user requested optimization/fixes or implementation scope is otherwise clear.
- Show real code evidence. Every finding cites actual file paths and line numbers.
- Thresholds are heuristics, not verdicts. Tool count, parameter count, latency, and token budgets are ground-truthable.
- Verify after applying. Use `test-by-mcpc-cli`, MCP Inspector, tests, or endpoint checks.
- Do not duplicate build-skill mechanics. Route SDK v1/v2 and `mcp-use/server` implementation details to companion skills.
- Do not wrap REST endpoints one-to-one. Map tools to user intent.
- Do not deeply nest schemas. Flatten past one level.
- Do not return raw upstream JSON. Curate, summarize, and format for LLM consumption.
- Do not use protocol errors for business failures. Reserve protocol errors for transport and framework issues.
- Do not eagerly register 20+ tools. Use progressive discovery.
- Do not skip input validation. Never trust LLM-generated input.
- Do not use SSE for new remote deployments. Use Streamable HTTP.
- Do not undervalue descriptions. They are the model's primary tool-selection signal.
- Do not return sensitive data in tool responses. Anything returned enters model context.
- Do not forward user tokens to upstream APIs. Use OBO with audience checks; see `references/patterns/auth-identity.md`.
- Do not silently drop advanced-protocol features. Capability-gate sampling, elicitation, and roots; see `references/patterns/advanced-protocol.md`.
