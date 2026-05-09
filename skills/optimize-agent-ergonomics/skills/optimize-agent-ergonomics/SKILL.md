---
name: optimize-agent-ergonomics
description: Use skill if you are auditing a CLI or MCP server for agent-readiness, designing one from scratch, or deciding CLI vs MCP for an agent-callable tool.
---

# optimize-agent-ergonomics

Make tools that agents can actually use. Whether the tool ships as a CLI binary or an MCP server, the agent's experience is the same — read a description, pick a tool, send typed input, get a typed result, recover from errors. This skill owns the shared principles and routes to surface-specific deep dives.

## How to think about this

Three principles, applied without exception.

1. **Surface is a deployment choice, not an identity.** The same business logic can ship as a CLI, an MCP server, or both. Decide based on the workload — who calls it, how often, with what auth model, against what state — not based on which technology felt newer last week. The Mode-A audit and the Mode-B brainstorm both run through `references/common/decide-surface.md` before any surface-specific work begins.
2. **Descriptions are prompt engineering.** A `--help` page or a `tools/list` description is text the LLM reads at decision time. Write for the model, not for a human reading docs. Names, parameter labels, error messages — all of it is the prompt the agent uses to figure out whether to call your tool. See `references/common/descriptions-as-prompts.md`.
3. **Errors are the hard part.** Outputs an agent can parse and retry on are the difference between a tool the agent uses confidently and one it abandons after the first failure. Distinguish transient from permanent. Surface the next action. Make the envelope schema-versioned. See `references/common/error-strategy.md`.

## Use this skill when

- Auditing an existing CLI for agent-readiness ("why does Claude keep failing on my CLI?")
- Auditing an existing MCP server ("our MCP works in dev but the agent can't use it reliably")
- Designing a new CLI or MCP server from scratch
- Deciding whether a workflow should be a CLI, an MCP server, or both
- Diagnosing why an agent keeps failing on a tool that "looks right"
- Refactoring tool descriptions, schemas, error envelopes, retry semantics

## Do not use this skill when

- *Implementing* an MCP server in a specific SDK after the architecture is decided — defer to `build-mcp-server-sdk-v1`, `build-mcp-server-sdk-v2`, or `build-mcp-use-server`
- *Testing* an MCP server end-to-end — defer to `test-by-mcpc-cli`
- *Porting* a v1 MCP server to v2 — defer to `convert-mcp-server-sdk-v1-to-v2`
- The user wants a one-off shell script with no agent in the loop

## Workflow

### 1. Classify intent

Pick exactly one entry point. Ambiguous → ask one targeted question, never guess.

| Intent | Mode | Route |
|---|---|---|
| "Audit my existing CLI" | A-CLI | `references/cli/audit-checklist.md` → `references/common/audit-rhythm.md` → present findings |
| "Audit my existing MCP server" | A-MCP | `references/mcp/audit-existing.md` → `references/common/audit-rhythm.md` → present findings |
| "Design a new CLI" | B-CLI | `references/common/design-thinking.md` → `references/cli/architect-new.md` → handoff |
| "Design a new MCP server" | B-MCP | `references/common/design-thinking.md` → `references/mcp/architect-new.md` → handoff to companion build skill |
| "Should this be a CLI or an MCP?" | Decide | `references/common/decide-surface.md` → loop into A or B once the surface is fixed |
| "I have a problem and don't know which mode" | Diagnose | Ask one targeted question, then pick mode |

### 2. Apply the universal principles (`references/common/`)

Every audit and every architecture pass routes through the shared principle set first:

- `references/common/design-thinking.md` — 8 questions to answer for any new agent tool: workload, audience, statefulness, auth, scale, error semantics, observability, lifecycle.
- `references/common/descriptions-as-prompts.md` — names + descriptions ARE the prompt; how to write them so the model picks the right tool.
- `references/common/output-contracts.md` — structured outputs, schema versioning, what an agent can parse vs what dumps raw API noise into context.
- `references/common/error-strategy.md` — retry-friendly error envelopes; transient vs permanent; what the agent needs to recover.
- `references/common/idempotency-and-retries.md` — verb semantics (create / apply / ensure / delete), idempotency keys, side-effect safety.
- `references/common/iterative-loops.md` — multi-turn workflows: agent submits → validates → repairs → resubmits → advances.
- `references/common/agent-cognitive-load.md` — token budgets, progressive disclosure, why fewer well-designed tools beat thirty narrow ones.
- `references/common/agent-integration.md` — how agents actually call tools (subprocess for CLI, MCP client for MCP); failure modes the tool author should anticipate.
- `references/common/audit-rhythm.md` — the Explore → Diagnose → Present → Optimize ritual; do not pattern-match before reading the user's code.
- `references/common/exemplars.md` — production CLIs and MCP servers that get this right, evidence-based.
- `references/common/decide-surface.md` — the canonical CLI-vs-MCP decision tree; the only file that owns this question.

### 3. Apply the surface-specific patterns

For CLI work, route through `references/cli/audit-checklist.md` (the 5-check entry — stdout/stderr separation, exit codes, non-interactive flags, structured errors, parsing reliability) and the rest of `references/cli/`.

For MCP work, route through `references/mcp/audit-existing.md` and the relevant `references/mcp/decision-trees/` based on the diagnosis (tool count? response format? security posture? scaling? production readiness?), then to `references/mcp/patterns/` for the deep dives.

### 4. Hand off (Mode B only)

After the architecture sketch is approved by the user:

- **CLI:** hand off with the templates from `references/cli/code-templates.md`. There is no `build-cli` companion skill in this repo — the merged skill produces a working scaffold and stops.
- **MCP:** route to the right companion build skill based on the architecture decision:
  - `build-mcp-server-sdk-v1` — production-ready, mainstream SDK
  - `build-mcp-server-sdk-v2` — beta SDK, newest features
  - `build-mcp-use-server` — HTTP-first, modern DX, opinionated wrapper
  - `convert-mcp-server-sdk-v1-to-v2` — when the user has a v1 server and wants to port

## Decision rules

- **Surface decision is conditional, not assumed.** Don't open with "is this a CLI or MCP?" — first ask what the workload is. The surface falls out.
- **Audit before optimize.** Read the existing code before suggesting patterns. Mechanical pattern-matching is worse than no help at all — that's why `references/common/audit-rhythm.md` is non-negotiable.
- **Descriptions are prompts.** Treat every tool description and `--help` page as text the LLM reads at tool-selection time, not as documentation a human will read once.
- **Errors must be retryable.** If the agent can't tell whether to retry, the tool will be abandoned after one failure. Schema-versioned envelopes, error codes, and `next_action` guidance are the difference.
- **Surface-specific work routes to surface-specific references.** Don't try to apply CLI patterns to MCP and vice versa — the contracts are different even when the principles match.
- **Companion skills own implementation.** This skill stops at architecture + audit findings; build skills implement.

## Recovery paths

| Symptom | Cause | Fix |
|---|---|---|
| Agent fails to call a tool that "looks right" | Description is human-readable, not LLM-readable | Read `references/common/descriptions-as-prompts.md`; rewrite description with intent + parameter shape + side-effect note |
| Agent succeeds once, then gives up on retry | Error envelope doesn't distinguish transient from permanent | Read `references/common/error-strategy.md`; add error code + retry guidance to envelope |
| Agent submits malformed input repeatedly | Schema is too deep or too permissive | Read `references/mcp/patterns/schema-design.md` (MCP) or `references/cli/flags-and-discovery.md` (CLI); flatten + tighten |
| 30 tools, agent picks the wrong one | Too many tools in flat namespace | Read `references/mcp/decision-trees/tool-count.md`; consolidate or progressive-discover |
| Agent times out on a long-running tool | No iterative pattern | Read `references/common/iterative-loops.md` + `references/cli/iterative-pattern.md` (CLI) or `references/mcp/patterns/agentic-patterns.md` (MCP); add `phase` + `progress` + `next_action` |
| Tool exposes raw API JSON | Agent loses context budget on noise | Read `references/mcp/patterns/tools.md` (response-shape) or `references/cli/output-envelope.md`; project to agent-relevant fields only |
| MCP server passes audit but fails in production | Skipped `references/mcp/decision-trees/production-readiness.md` | Run that tree before declaring done |
| User asks "should I use MCP or just stick with the CLI?" | Surface decision question | Read `references/common/decide-surface.md` — the decision tree is in there |
| Agent loses context across turns on a multi-step workflow | No session state | Read `references/mcp/patterns/session-and-state.md` (MCP) or `references/cli/iterative-pattern.md` (CLI) |
| Agent keeps re-fetching the same large data | No caching strategy | Read `references/mcp/patterns/caching-economics.md` |

## Reference routing

| File | Read when |
|---|---|
| `references/common/decide-surface.md` | The user is unsure whether the workflow should be a CLI or MCP, or you need to confirm the surface choice before optimizing |
| `references/common/design-thinking.md` | Mode B — designing any new agent tool, surface-agnostic; 8 questions to answer up front |
| `references/common/audit-rhythm.md` | Mode A — auditing any existing tool; the Explore → Diagnose → Present → Optimize ritual |
| `references/common/descriptions-as-prompts.md` | Whenever tool naming or description is in scope (always for new tools, often for audits) |
| `references/common/output-contracts.md` | Designing structured output; cross-surface principles |
| `references/common/error-strategy.md` | Designing error envelopes; cross-surface principles |
| `references/common/idempotency-and-retries.md` | Designing operations with side effects; verb semantics |
| `references/common/iterative-loops.md` | Multi-turn agent workflows; submit → validate → repair |
| `references/common/agent-cognitive-load.md` | Tool count, token budgets, context-engineering across surfaces |
| `references/common/agent-integration.md` | Understanding how agents actually call tools |
| `references/common/exemplars.md` | Need a worked example or vendor reference |
| `references/cli/architect-new.md` | Mode B-CLI — designing a new agent-ready CLI |
| `references/cli/audit-checklist.md` | Mode A-CLI — auditing existing CLI; 5-check entry |
| `references/cli/output-envelope.md` | CLI-specific JSON envelope (`ok` / `result` / `error` / `schema_version`) |
| `references/cli/exit-codes.md` | Semantic exit code taxonomy |
| `references/cli/flags-and-discovery.md` | Standard flag registry, TTY/CI detection, help-text-as-API |
| `references/cli/auth-headless.md` | Headless auth, env vars, sandbox boundaries |
| `references/cli/iterative-pattern.md` | CLI-specific iterative pattern fields |
| `references/cli/code-templates.md` | Production code samples in Go / Python / Node / Rust / Bash |
| `references/cli/subprocess-harness.md` | Calling an agent-ready CLI from a Python / Node agent harness |
| `references/mcp/architect-new.md` | Mode B-MCP — designing a new MCP server (12-question brainstorm) |
| `references/mcp/audit-existing.md` | Mode A-MCP — auditing existing MCP server |
| `references/mcp/decision-trees/*.md` | Routing within MCP audits and architecture passes |
| `references/mcp/patterns/*.md` | Deep dives the trees route into |

## Cross-skill handoffs

- **`build-mcp-server-sdk-v1`** — implements the MCP server using `@modelcontextprotocol/sdk` v1.x; the canonical production path
- **`build-mcp-server-sdk-v2`** — implements with the v2 split-package SDK (beta as of May 2026)
- **`build-mcp-use-server`** — implements with the `mcp-use` HTTP-first wrapper
- **`convert-mcp-server-sdk-v1-to-v2`** — ports a v1 server to v2
- **`test-by-mcpc-cli`** — tests an MCP server end-to-end with `mcpc 0.2.x`
- **`use-railway`** — operates Railway-hosted MCP servers (logs, scale, restart) post-deploy
- **`init-makefiles`** — scaffolds `make` targets around the resulting tool (CLI or MCP server)

## Guardrails

- **Never apply patterns mechanically.** Read the user's code first. The audit rhythm is non-negotiable for a reason — pattern-fitting before exploration generates worse advice than no advice.
- **Never claim a CLI is agent-ready without running the 5-check audit.** Stdout/stderr, exit codes, non-interactive, structured errors, parsing reliability — all five.
- **Never skip `references/common/decide-surface.md` when the user is unsure of the surface.** Guessing the surface pollutes the rest of the conversation.
- **Never wrap a REST API 1:1** as either CLI commands or MCP tools. That's a guaranteed agent footgun — the agent loses context on response noise and the tool surface is too granular for intent-based dispatch (`references/mcp/patterns/tools.md`).
- **Never create deeply nested input schemas.** Flatten to ≤6 top-level params. LLMs fail at deep-nested structure (`references/mcp/patterns/schema-design.md`).
- **Never expose protocol errors for business logic.** Use `isError` + structured content (MCP) or exit codes + envelope (CLI). Protocol errors are reserved for transport/framework failures.
- **Never blanket-recommend MCP over CLI or vice versa.** The decision is workload-dependent (`references/common/decide-surface.md`).
- **Never skip the companion-skill handoff in Mode B-MCP.** This skill ends at architecture; building belongs to a build skill.

## Final checks

Before declaring done:

- [ ] Mode is explicit (A-CLI / A-MCP / B-CLI / B-MCP / Decide)
- [ ] At least one `references/common/` reference was read for principles
- [ ] At least one surface-folder reference (`references/cli/` or `references/mcp/`) was read for surface specifics
- [ ] Findings are presented one at a time with options (Mode A) or as an architecture sketch (Mode B), not as a wall of recommendations
- [ ] Handoff to companion build/test skill is named (Mode B-MCP)
- [ ] Surface decision was made consciously, not assumed
- [ ] Every recommendation cites the reference file that backs it
