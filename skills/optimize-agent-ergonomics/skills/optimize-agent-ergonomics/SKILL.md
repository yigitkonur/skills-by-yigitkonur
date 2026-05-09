---
name: optimize-agent-ergonomics
description: Use skill if you are deciding CLI vs MCP, harmonizing cross-surface agent contracts, or auditing surface choice before implementation.
---

# optimize-agent-ergonomics

Make agent-facing tool surfaces easier to choose, use, and repair. This skill owns the CLI-vs-MCP decision, shared contract design, cross-surface audits, and handoff to surface-specific MCP build and test skills.

## Trigger Boundary

Use this skill when the task is about:

- deciding whether an agent workflow belongs on a CLI, MCP server, hybrid surface, or skill-plus-CLI path
- harmonizing one workflow across CLI and MCP without duplicating incompatible contracts
- auditing why an agent fails on an existing tool when the root cause could be surface choice, descriptions, outputs, auth, state, or retries
- drafting the shared agent contract before implementation starts
- preparing a named handoff to a build or test skill after the surface is fixed

Do not use this skill when:

- the surface is already fixed and the task is implementation-only
- the work is ordinary CLI usage with no agent-readiness concern
- the work is ordinary MCP server coding with no ergonomics, surface, audit, or contract decision
- the user asks for one throwaway shell script with no agent loop
- the user asks to deprecate sibling skills; that is a separate maintainer-approved scope

## Relationship To Sibling Skills

Maintained position for this repo: `optimize-agent-ergonomics` is the canonical cross-surface successor for agent-ready CLI/MCP decisions and shared contracts.

If `optimize-agentic-cli` or `optimize-agentic-mcp` exists in an installed pack, treat them as legacy surface-specific workflows until a maintainer approves one of two separate follow-ups:

- deprecate both legacy skills into redirect stubs pointing here
- keep all three active with narrower legacy descriptions and explicit routing boundaries

Do not edit sibling skills during an ergonomics pass unless the maintainer explicitly authorizes that separate deprecation or narrowing scope.

## Non-Negotiable Rules

1. Decide workload before deciding surface.
2. Audit existing code before recommending patterns.
3. Keep stdout, MCP content, and `structuredContent` parseable.
4. Return retryable errors with next action and stable error codes.
5. Route MCP implementation to `build-mcp-server-sdk-v1`, `build-mcp-server-sdk-v2`, or `build-mcp-use-server` after architecture is fixed.
6. Route MCP end-to-end verification to `test-by-mcpc-cli`.
7. Cite exact reference files for every recommendation.
8. State the verification rung actually reached.

## Modes

Pick one mode and name it in the answer.

| Mode | Use when | Required first route |
|---|---|---|
| Mode A — audit existing surface | Existing CLI/MCP/hybrid tool needs an agent-readiness audit | `references/common/audit-rhythm.md` |
| Mode B — sketch new architecture | New tool needs surface, contract, and handoff before implementation | `references/common/design-thinking.md` |
| Mode C — decide surface | Surface is undecided or contested | `references/common/decide-surface.md` |
| Mode D — harmonize contracts | One workflow must expose CLI and MCP consistently | `references/common/agent-integration.md` |
| Mode E — route out | Surface and implementation path are already fixed | matching reference below, then named companion skill |

## Surface Decision Summary

Use `references/common/decide-surface.md` for the full decision tree. The short path:

1. CLI fits shell-composable, local, batch, CI, or human-and-agent workflows.
2. MCP fits session-aware, model-native, remote, multi-tool, or client-integrated workflows.
3. Hybrid fits a shared core with both a subprocess boundary and MCP transport.
4. Skill+CLI fits deterministic local commands where a skill supplies workflow judgment.
5. Revisit surface if auth, state, audience, or retry semantics contradict the first answer.

Every surface decision output must use this shape:

```markdown
Surface recommendation: CLI / MCP / hybrid / skill+CLI
Reason: workload, auth, state, audience
Tradeoff: what the losing option would cost
Next route: references/...
Confidence: high / medium / low
```

## Workflow

### 1. Explore

Read the target code, docs, or current tool surface first. For existing tools, collect:

- command/tool list and names
- input schemas or flags
- output shape
- error and retry behavior
- auth and headless behavior
- state/session behavior
- operational signals: logs, tests, transport, deployment, timeout behavior

### 2. Decide Or Confirm Surface

Use `references/common/decide-surface.md` before recommending CLI, MCP, hybrid, or skill+CLI. If the user already chose a surface, still verify that workload, auth, state, and audience do not contradict it.

### 3. Apply Shared Contracts

Use the common references before surface-specific detail:

- descriptions and names: `references/common/descriptions-as-prompts.md`
- output shape: `references/common/output-contracts.md`
- errors and retries: `references/common/error-strategy.md`
- idempotency: `references/common/idempotency-and-retries.md`
- iterative repair loops: `references/common/iterative-loops.md`
- cognitive load: `references/common/agent-cognitive-load.md`

### 4. Route Surface-Specific Work

- CLI audit or design: route to `references/cli/audit-checklist.md` or `references/cli/architect-new.md`.
- MCP audit or design: route to `references/mcp/audit-existing.md` or `references/mcp/architect-new.md`.
- MCP implementation:
  - `build-mcp-server-sdk-v1` for production-ready official SDK v1 work
  - `build-mcp-server-sdk-v2` for split-package v2 work
  - `build-mcp-use-server` for HTTP-first `mcp-use` server work
- MCP testing: route to `test-by-mcpc-cli`.

## Output Contracts

### Mode A Audit

Produce:

```markdown
Mode: Mode A — audit existing surface
Target path: path/to/tool

Scorecard:
| Dimension | Score | Evidence |
|---|---:|---|
| discovery | 0-5 | file:line |
| input/schema | 0-5 | file:line |
| output | 0-5 | file:line |
| error/retry | 0-5 | file:line |
| auth/headless | 0-5 | file:line |
| state/iteration | 0-5 | file:line |
| operations | 0-5 | file:line |

Top findings:
1. Severity: Critical / High / Medium / Low
   Evidence: file:line
   Issue:
   Reference route:
   Minimal fix:
   Comprehensive fix:

Recommended fix path: minimal / comprehensive
Verification rung reached: Rung 1-6, with commands or observation
```

### Mode B Architecture Sketch

Produce:

```markdown
Mode: Mode B — sketch new architecture
Workload:
Chosen surface: CLI / MCP / hybrid / skill+CLI
Command/tool set:
Output contract:
Error model:
Auth model:
State model:
Test plan:
Handoff skill:
Next route: references/...
Verification rung reached: Rung 1-6, with commands or observation
```

## Reference Routing

### Common

| File | Read when |
|---|---|
| `references/common/agent-cognitive-load.md` | Tool count, response size, token budget, progressive disclosure, or context pressure matters. |
| `references/common/agent-integration.md` | The design must survive real agent harnesses across subprocess and MCP clients. |
| `references/common/audit-rhythm.md` | Any existing tool is being audited or diagnosed. |
| `references/common/decide-surface.md` | CLI vs MCP vs hybrid vs skill+CLI is open, contested, or needs confirmation. |
| `references/common/descriptions-as-prompts.md` | Names, descriptions, help text, parameter text, or tool selection are in scope. |
| `references/common/design-thinking.md` | A new agent-facing workflow needs workload-first architecture. |
| `references/common/error-strategy.md` | Error envelopes, retry semantics, `next_action`, transient/permanent classification, or loop detection are in scope. |
| `references/common/exemplars.md` | Precedent from production CLIs or MCP servers would sharpen a decision. |
| `references/common/idempotency-and-retries.md` | Side effects, retries, idempotency keys, or verb semantics are in scope. |
| `references/common/iterative-loops.md` | Multi-turn submit, validate, repair, resume, or state-token workflows are in scope. |
| `references/common/output-contracts.md` | Structured outputs, schema versioning, pagination, projection, or response-size caps are in scope. |

### CLI

| File | Read when |
|---|---|
| `references/cli/architect-new.md` | Designing a new agent-ready CLI after the surface decision lands on CLI. |
| `references/cli/audit-checklist.md` | Auditing an existing CLI for stdout/stderr, exit codes, headless mode, structured errors, and parsing reliability. |
| `references/cli/auth-headless.md` | CLI auth must work in CI, containers, remote shells, or non-interactive agent runs. |
| `references/cli/code-templates.md` | A small scaffold or implementation template is needed after CLI contract design. |
| `references/cli/exit-codes.md` | Exit-code taxonomy or retry/escalation classification is in scope. |
| `references/cli/flags-and-discovery.md` | Help text, standard flags, TTY detection, or CLI discovery is in scope. |
| `references/cli/iterative-pattern.md` | CLI needs validate-repair-advance phases, state tokens, or NDJSON progress. |
| `references/cli/output-envelope.md` | CLI JSON envelope, error object, pagination, or streaming output shape is in scope. |
| `references/cli/subprocess-harness.md` | A CLI must be exercised from a realistic agent subprocess harness. |

### MCP

| File | Read when |
|---|---|
| `references/mcp/architect-new.md` | Designing a new MCP server before routing to a build skill. |
| `references/mcp/audit-existing.md` | Auditing an existing MCP server for agent-readiness and production ergonomics. |
| `references/mcp/decision-trees/design-phase.md` | SDK, schema dialect, statefulness, transport, or auth choices are still open. |
| `references/mcp/decision-trees/error-strategy.md` | MCP-specific protocol error vs `isError` vs structured recovery shape is in scope. |
| `references/mcp/decision-trees/production-readiness.md` | Deployment, health, telemetry, tests, or production reliability is in scope. |
| `references/mcp/decision-trees/response-format.md` | Text content, `structuredContent`, mixed responses, resources, or pagination must be chosen. |
| `references/mcp/decision-trees/scaling.md` | Load profile, session pooling, async tasks, gateway, or multi-server scale is in scope. |
| `references/mcp/decision-trees/security-posture.md` | Deployment threat model, auth, secrets, permissions, or SSRF defenses are in scope. |
| `references/mcp/decision-trees/tool-count.md` | Tool count, granularity, consolidation, or progressive discovery is in scope. |
| `references/mcp/patterns/advanced-protocol.md` | Sampling, elicitation, roots, cancellation, or capability fallback is in scope. |
| `references/mcp/patterns/agentic-patterns.md` | MCP workflow gating, HATEOAS next actions, prompt gates, or server-enforced stages are in scope. |
| `references/mcp/patterns/auth-identity.md` | OAuth 2.1, PRM, CIMD, OBO, audience validation, or step-up consent is in scope. |
| `references/mcp/patterns/caching-economics.md` | Prompt caching, result caching, invalidation, or token-cost economics is in scope. |
| `references/mcp/patterns/client-compatibility.md` | Client support differences across Claude, ChatGPT, Cursor, Goose, or other MCP clients matter. |
| `references/mcp/patterns/error-handling.md` | MCP result errors, `isError`, recovery hints, validation errors, or retry fields are in scope. |
| `references/mcp/patterns/exemplar-servers.md` | Vendor server precedent or production pattern comparison is needed. |
| `references/mcp/patterns/model-behavior.md` | Model-specific tool selection, schema filling, or long-context behavior affects the design. |
| `references/mcp/patterns/progressive-discovery.md` | Large tool catalogs need meta-tools, staged disclosure, semantic search, or hidden-tool fallback. |
| `references/mcp/patterns/prompt-gates.md` | Destructive or high-stakes actions need confirmation, approval, or consent gates. |
| `references/mcp/patterns/registry-and-distribution.md` | Publishing, namespacing, marketplace install, registry metadata, or trust signals are in scope. |
| `references/mcp/patterns/resources-and-prompts.md` | MCP resources or prompts are part of discovery, context, or reusable workflow design. |
| `references/mcp/patterns/schema-design.md` | Input schemas, nesting, enums, optionality, validation, or generated schemas are in scope. |
| `references/mcp/patterns/security.md` | Prompt injection, data exfiltration, privilege escalation, or hardening strategy is in scope. |
| `references/mcp/patterns/session-and-state.md` | Session state, stateless tokens, resumability, or cross-turn continuity is in scope. |
| `references/mcp/patterns/testing.md` | Unit, protocol, Inspector, `mcpc`, regression, or production verification strategy is in scope. |
| `references/mcp/patterns/threat-catalog.md` | Findings need named MCP attack vocabulary, CVEs, or dated practitioner evidence. |
| `references/mcp/patterns/tools.md` | Tool granularity, descriptions, response shape, or tool composition is in scope. |
| `references/mcp/patterns/transport-and-ops.md` | Transport, stdio/HTTP/SSE, stdout purity, deployment, observability, or ops is in scope. |

## Script Routing

Use deterministic helpers only as preflight evidence; never treat them as complete audits.

| Script | Read first | Use when |
|---|---|---|
| `scripts/audit-cli.sh` | `scripts/audit-cli.md` | Running a quick static/behavioral CLI preflight on a safe local probe command. |
| `scripts/audit-mcp.sh` | `scripts/audit-mcp.md` | Running a conservative MCP source scan for registrations, schemas, transports, and error patterns. |

## Final Checks

Before declaring done:

- [ ] Mode is explicit.
- [ ] Surface recommendation uses the required five-line shape when surface choice was in scope.
- [ ] Mode A audit output includes scorecard, findings, fix options, evidence, and verification rung.
- [ ] Mode B sketch names workload, surface, command/tool set, output, error, auth, state, test plan, and handoff skill.
- [ ] Every recommendation cites a `references/...` file or companion skill.
- [ ] MCP implementation handoff names `build-mcp-server-sdk-v1`, `build-mcp-server-sdk-v2`, or `build-mcp-use-server`.
- [ ] MCP test handoff names `test-by-mcpc-cli` when end-to-end MCP verification is required.
- [ ] Verification claims match the rung actually reached.
