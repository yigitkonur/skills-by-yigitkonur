---
name: optimize-agent-ergonomics
description: Use skill if you are deciding CLI vs MCP or harmonizing shared agent-ergonomics contracts across both surfaces before routing to surface-specific skills.
---

# optimize-agent-ergonomics

Make cross-surface tool decisions that agents can actually use. Whether the tool ships as a CLI binary, an MCP server, or both, the agent's experience is the same — read a description, pick a tool, send typed input, get a typed result, recover from errors. This skill owns the shared principles and CLI-vs-MCP routing decision; surface-specific audit and build work belongs to the dedicated companion skills.

## How to think about this

Three principles, applied without exception.

1. **Surface is a deployment choice, not an identity.** The same business logic can ship as a CLI, an MCP server, or both. Decide based on the workload — who calls it, how often, with what auth model, against what state — not based on which technology felt newer last week. Every cross-surface pass runs through `references/common/decide-surface.md` before surface-specific work begins.
2. **Descriptions are prompt engineering.** A `--help` page or a `tools/list` description is text the LLM reads at decision time. Write for the model, not for a human reading docs. Names, parameter labels, error messages — all of it is the prompt the agent uses to figure out whether to call your tool. See `references/common/descriptions-as-prompts.md`.
3. **Errors are the hard part.** Outputs an agent can parse and retry on are the difference between a tool the agent uses confidently and one it abandons after the first failure. Distinguish transient from permanent. Surface the next action. Make the envelope schema-versioned. See `references/common/error-strategy.md`.

## Use this skill when

- Deciding whether a workflow should be a CLI, an MCP server, or both
- Harmonizing a workflow that ships as both CLI and MCP
- Designing the shared agent-facing contract before the surface is fixed
- Diagnosing why an agent keeps failing on a tool when the root cause could be surface choice, description, output, or retry semantics
- Preparing a handoff to `references/cli/audit-checklist.md` (CLI audit) or `references/cli/architect-new.md` (CLI design), `references/mcp/audit-existing.md` (MCP audit) or `references/mcp/architect-new.md` (MCP design), or an MCP build skill

## Do not use this skill when

- The work is a CLI-only audit, CLI-only redesign, or CLI implementation after the surface is fixed — defer to `references/cli/audit-checklist.md` (CLI audit) or `references/cli/architect-new.md` (CLI design)
- The work is an MCP-only audit, MCP architecture pass, or MCP optimization after the surface is fixed — defer to `references/mcp/audit-existing.md` (MCP audit) or `references/mcp/architect-new.md` (MCP design)
- *Implementing* an MCP server in a specific SDK after the architecture is decided — defer to `build-mcp-server-sdk-v1`, `build-mcp-server-sdk-v2`, or `build-mcp-use-server`
- *Testing* an MCP server end-to-end — defer to `test-by-mcpc-cli`
- *Porting* a v1 MCP server to v2 — defer to `convert-mcp-server-sdk-v1-to-v2`
- The user wants a one-off shell script with no agent in the loop

## Workflow

### 1. Classify intent

Pick exactly one entry point. Ambiguous → ask one targeted question, never guess.

| Intent | Mode | Route |
|---|---|---|
| "Should this be a CLI or an MCP?" | Decide | `references/common/decide-surface.md` → route to the companion skill once the surface is fixed |
| "Design the agent contract before picking a surface" | Cross-surface design | `references/common/design-thinking.md` → `references/common/output-contracts.md` → `references/common/error-strategy.md` → handoff |
| "This workflow needs both CLI and MCP" | Harmonize | `references/common/agent-integration.md` → `references/common/descriptions-as-prompts.md` → surface-specific handoff |
| "The agent fails, but I don't know whether it is a CLI or MCP problem" | Diagnose | `references/common/audit-rhythm.md` → `references/common/decide-surface.md` → route to companion skill |
| "Audit my existing CLI" | Route out | `references/cli/audit-checklist.md` (CLI audit) or `references/cli/architect-new.md` (CLI design) |
| "Audit my existing MCP server" | Route out | `references/mcp/audit-existing.md` (MCP audit) or `references/mcp/architect-new.md` (MCP design) |

### 2. Apply the universal principles

Every cross-surface decision and shared-contract pass routes through the shared principle set first:

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

For CLI-specific handoffs, cite the relevant `references/cli/` file in this skill only to explain the shared contract, then route detailed CLI audit/design work to `references/cli/audit-checklist.md` (CLI audit) or `references/cli/architect-new.md` (CLI design).

For MCP-specific handoffs, cite `references/mcp/audit-existing.md`, the relevant `references/mcp/decision-trees/*.md`, or `references/mcp/patterns/*.md` only to explain the shared contract, then route detailed MCP audit/architecture work to `references/mcp/audit-existing.md` (MCP audit) or `references/mcp/architect-new.md` (MCP design).

### 4. Hand off once the surface is fixed

After the surface decision or cross-surface contract is approved by the user:

- **CLI:** hand off to `references/cli/audit-checklist.md` (CLI audit) or `references/cli/architect-new.md` (CLI design) with the chosen contract and any relevant CLI reference route.
- **MCP architecture / optimization:** hand off to `references/mcp/audit-existing.md` (MCP audit) or `references/mcp/architect-new.md` (MCP design).
- **MCP implementation:** route to the right companion build skill based on the architecture decision:
  - `build-mcp-server-sdk-v1` — production-ready, mainstream SDK
  - `build-mcp-server-sdk-v2` — beta SDK, newest features
  - `build-mcp-use-server` — HTTP-first, modern DX, opinionated wrapper
  - `convert-mcp-server-sdk-v1-to-v2` — when the user has a v1 server and wants to port

## Decision rules

- **Surface decision is conditional, not assumed.** Don't open with "is this a CLI or MCP?" — first ask what the workload is. The surface falls out.
- **Audit before optimize.** Read the existing surface and failure evidence before suggesting patterns. Mechanical pattern-matching is worse than no help at all — that's why `references/common/audit-rhythm.md` is non-negotiable.
- **Descriptions are prompts.** Treat every tool description and `--help` page as text the LLM reads at tool-selection time, not as documentation a human will read once.
- **Errors must be retryable.** If the agent can't tell whether to retry, the tool will be abandoned after one failure. Schema-versioned envelopes, error codes, and `next_action` guidance are the difference.
- **Surface-specific work routes to surface-specific references.** Don't try to apply CLI patterns to MCP and vice versa — the contracts are different even when the principles match.
- **Companion skills own surface-specific depth.** This skill stops at surface decision + shared contract; CLI/MCP-specific skills audit, optimize, architect, and implement.

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
| `references/common/agent-cognitive-load.md` | Tool count, token budgets, context-engineering across surfaces |
| `references/common/agent-integration.md` | Understanding how agents actually call tools |
| `references/common/audit-rhythm.md` | Diagnosing ambiguous tool failures before routing to a surface skill |
| `references/common/decide-surface.md` | The user is unsure whether the workflow should be a CLI or MCP, or you need to confirm the surface choice before optimizing |
| `references/common/descriptions-as-prompts.md` | Whenever tool naming or description is in scope |
| `references/common/design-thinking.md` | Designing a shared agent contract before the surface is fixed |
| `references/common/error-strategy.md` | Designing error envelopes; cross-surface principles |
| `references/common/exemplars.md` | Need a worked example or vendor reference |
| `references/common/idempotency-and-retries.md` | Designing operations with side effects; verb semantics |
| `references/common/iterative-loops.md` | Multi-turn agent workflows; submit → validate → repair |
| `references/common/output-contracts.md` | Designing structured output; cross-surface principles |
| `references/cli/architect-new.md` | CLI-specific handoff context for a new agent-ready CLI |
| `references/cli/audit-checklist.md` | CLI-specific handoff context for the 5-check audit |
| `references/cli/auth-headless.md` | Headless auth, env vars, sandbox boundaries |
| `references/cli/code-templates.md` | Production code samples in Go / Python / Node / Rust / Bash |
| `references/cli/exit-codes.md` | Semantic exit code taxonomy |
| `references/cli/flags-and-discovery.md` | Standard flag registry, TTY/CI detection, help-text-as-API |
| `references/cli/iterative-pattern.md` | CLI-specific iterative pattern fields |
| `references/cli/output-envelope.md` | CLI-specific JSON envelope (`ok` / `result` / `error` / `schema_version`) |
| `references/cli/subprocess-harness.md` | Calling an agent-ready CLI from a Python / Node agent harness |
| `references/mcp/architect-new.md` | MCP-specific handoff context for a new MCP server |
| `references/mcp/audit-existing.md` | MCP-specific handoff context for auditing an existing MCP server |
| `references/mcp/decision-trees/design-phase.md` | Deciding whether MCP architecture work is ready to hand off |
| `references/mcp/decision-trees/error-strategy.md` | Choosing MCP error signaling and recovery shape |
| `references/mcp/decision-trees/production-readiness.md` | Auditing production deployment, ops, and reliability readiness |
| `references/mcp/decision-trees/response-format.md` | Choosing response shape and content structure |
| `references/mcp/decision-trees/scaling.md` | Deciding scaling, transport, and operational shape |
| `references/mcp/decision-trees/security-posture.md` | Auditing auth, secrets, permissions, and threat posture |
| `references/mcp/decision-trees/tool-count.md` | Deciding whether to split, merge, or progressively disclose tools |
| `references/mcp/patterns/advanced-protocol.md` | Advanced protocol capabilities and when to expose them |
| `references/mcp/patterns/agentic-patterns.md` | MCP patterns that help agents recover, iterate, and continue work |
| `references/mcp/patterns/auth-identity.md` | Auth, identity, and user-context design |
| `references/mcp/patterns/caching-economics.md` | Caching strategy and token/cost tradeoffs |
| `references/mcp/patterns/client-compatibility.md` | Client-specific compatibility and capability expectations |
| `references/mcp/patterns/error-handling.md` | MCP error envelopes, `isError`, and recoverability |
| `references/mcp/patterns/exemplar-servers.md` | Worked server examples and patterns worth copying |
| `references/mcp/patterns/model-behavior.md` | Model behavior considerations that affect MCP design |
| `references/mcp/patterns/progressive-discovery.md` | Progressive disclosure for large tool surfaces |
| `references/mcp/patterns/prompt-gates.md` | Prompt and confirmation gates before risky actions |
| `references/mcp/patterns/registry-and-distribution.md` | Registry, packaging, and distribution considerations |
| `references/mcp/patterns/resources-and-prompts.md` | MCP resources and prompts as discovery surfaces |
| `references/mcp/patterns/schema-design.md` | Schema depth, argument shape, and validation design |
| `references/mcp/patterns/security.md` | Security principles for MCP servers |
| `references/mcp/patterns/session-and-state.md` | Session state, continuity, and multi-step tool flows |
| `references/mcp/patterns/testing.md` | MCP testing strategy and verification expectations |
| `references/mcp/patterns/threat-catalog.md` | Threat catalog for review and design work |
| `references/mcp/patterns/tools.md` | Tool granularity, naming, and response-shape patterns |
| `references/mcp/patterns/transport-and-ops.md` | Transport, deployment, observability, and operations |

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
- **Never claim a CLI is agent-ready without routing to the CLI 5-check audit.** Stdout/stderr, exit codes, non-interactive, structured errors, parsing reliability — all five belong to `references/cli/audit-checklist.md` (CLI audit) or `references/cli/architect-new.md` (CLI design) once the surface is fixed.
- **Never skip `references/common/decide-surface.md` when the user is unsure of the surface.** Guessing the surface pollutes the rest of the conversation.
- **Never wrap a REST API 1:1** as either CLI commands or MCP tools. That's a guaranteed agent footgun — the agent loses context on response noise and the tool surface is too granular for intent-based dispatch (`references/mcp/patterns/tools.md`).
- **Never create deeply nested input schemas.** Flatten to ≤6 top-level params. LLMs fail at deep-nested structure (`references/mcp/patterns/schema-design.md`).
- **Never expose protocol errors for business logic.** Use `isError` + structured content (MCP) or exit codes + envelope (CLI). Protocol errors are reserved for transport/framework failures.
- **Never blanket-recommend MCP over CLI or vice versa.** The decision is workload-dependent (`references/common/decide-surface.md`).
- **Never skip the companion-skill handoff once the surface is fixed.** This skill ends at surface decision + shared contract; surface-specific work belongs to the companion skill.

## Final checks

Before declaring done:

- [ ] Mode is explicit (Decide / Cross-surface design / Harmonize / Diagnose / Route out)
- [ ] At least one exact common reference file was read for principles
- [ ] At least one exact CLI or MCP reference file was read for surface specifics
- [ ] Findings are presented one at a time with options, not as a wall of recommendations
- [ ] Handoff to companion CLI/MCP/build/test skill is named once the surface is fixed
- [ ] Surface decision was made consciously, not assumed
- [ ] Every recommendation cites the reference file that backs it
