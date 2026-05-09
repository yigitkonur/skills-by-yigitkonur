---
name: optimize-agent-ergonomics
description: Use skill if you are deciding CLI vs MCP, harmonizing one workflow across both surfaces, or auditing why an agent fails on a tool before any implementation.
---

# optimize-agent-ergonomics

Make agent-facing tool surfaces easier to choose, use, and repair. This skill owns the **surface decision** (CLI vs MCP vs hybrid vs skill+CLI), the **shared cross-surface contracts** (descriptions, outputs, errors, retries, idempotency), and the **named handoff** to surface-specific build and test skills once the architecture is fixed.

## When to use

Trigger on tasks that fit any of these:

- *deciding whether an agent workflow belongs on a CLI, MCP server, hybrid surface, or skill+CLI path*
- *harmonizing one workflow across CLI and MCP without diverging schemas, names, or error envelopes*
- *auditing why an agent fails on an existing tool when the root cause could be surface choice, descriptions, output shape, auth, state, or retries*
- *drafting the shared agent contract — names, descriptions, output schema, error model, retry semantics — before any code lands*
- *preparing a named handoff to `build-mcp-server-sdk-v1`, `build-mcp-server-sdk-v2`, `build-mcp-use-server`, or `test-by-mcpc-cli` after surface and contract are decided*
- *picking between a stateless one-shot CLI and a session-aware MCP tool when auth, state, or audience is contested*

Do NOT use when:

- The surface is already fixed and the work is **CLI-only implementation** — route to `optimize-agentic-cli`.
- The surface is already fixed and the work is **MCP-only implementation** — route to `optimize-agentic-mcp`.
- The user wants a one-off shell script with no agent harness in the loop — write the script directly.
- The task is to deprecate or rewrite sibling skills — that is a separate maintainer-approved scope; do not edit `optimize-agentic-cli` or `optimize-agentic-mcp` here.

## Sibling boundary

| Skill | Owns |
|---|---|
| `optimize-agent-ergonomics` (this skill) | Surface choice, cross-surface harmonization, ergonomics audits where surface itself is suspect, named handoff. |
| `optimize-agentic-cli` | CLI-only audit and command-contract design once the surface is CLI. |
| `optimize-agentic-mcp` | MCP-only audit and architecture once the surface is MCP. |
| `build-mcp-server-sdk-v1` / `-sdk-v2` / `build-mcp-use-server` | MCP implementation after architecture is fixed. |
| `test-by-mcpc-cli` | End-to-end MCP verification. |

If `optimize-agentic-cli` or `optimize-agentic-mcp` is also installed, treat them as the **post-decision** specialists. This skill stops at the handoff line.

## Non-negotiable rules

1. Decide the **workload** (what the agent is actually doing) before the surface.
2. Read the target code/docs **before** recommending any pattern — never blind-prescribe.
3. Keep CLI stdout, MCP `content`, and MCP `structuredContent` parseable; never mix prose into a JSON envelope.
4. Errors must be retryable: include `next_action` and a stable error code so an agent can decide retry vs escalate vs abort.
5. After the surface decision lands, hand off by **name** to the matching build/test skill — do not implement here.
6. Cite the exact `references/...` file or companion skill behind every recommendation.
7. State the actual verification rung reached (Rung 1 read → Rung 6 user-confirmed) — never inflate.

## Pick a mode (and name it in the answer)

| Mode | Use when | First reference to read |
|---|---|---|
| **A — audit existing surface** | An existing CLI/MCP/hybrid tool is failing agents and needs an ergonomics scorecard. | `references/common/audit-rhythm.md` |
| **B — sketch new architecture** | A new tool needs surface, contracts, and handoff before code. | `references/common/design-thinking.md` |
| **C — decide surface** | CLI vs MCP vs hybrid vs skill+CLI is contested or undecided. | `references/common/decide-surface.md` |
| **D — harmonize contracts** | One workflow must expose CLI **and** MCP consistently. | `references/common/agent-integration.md` |
| **E — route out** | Surface and implementation path are already fixed; only need the right next-skill name. | matching reference below, then named companion skill |

## Surface decision output (mandatory shape)

Whenever surface choice is in scope, end the answer with this exact block:

```
Surface recommendation: CLI / MCP / hybrid / skill+CLI
Reason: workload, auth, state, audience
Tradeoff: what the losing option would cost
Next route: references/...
Confidence: high / medium / low
```

Short decision path (full tree in `references/common/decide-surface.md`):

1. **CLI** — shell-composable, local, batch, CI, or human-and-agent workflows.
2. **MCP** — session-aware, model-native, remote, multi-tool, or client-integrated workflows.
3. **Hybrid** — shared core with both subprocess boundary and MCP transport.
4. **Skill+CLI** — deterministic local commands plus skill-supplied workflow judgment.
5. Revisit if **auth, state, audience, or retry semantics** contradict the first answer.

## Workflow

### 1. Explore (always first)

For an existing tool, collect:

- command/tool list and names
- input schemas / flags
- output shape (stdout, JSON, MCP `content` vs `structuredContent`)
- error and retry behavior
- auth and headless/CI behavior
- state/session model
- ops signals: logs, tests, transport, deployment, timeout behavior

For a greenfield tool, collect the **workload statement**: what the agent does, how often, with what side effects, against which audience.

### 2. Decide or confirm surface

Read `references/common/decide-surface.md`. If the user pre-chose a surface, still verify workload + auth + state + audience do not contradict it. Cross-check precedent in `references/common/exemplars.md` when conviction is shaky.

### 3. Apply shared contracts (before surface-specific detail)

| Topic | Reference |
|---|---|
| Names, descriptions, help text, tool selection | `references/common/descriptions-as-prompts.md` |
| Output shape, schema versioning, pagination | `references/common/output-contracts.md` |
| Error envelope, retry classes, `next_action` | `references/common/error-strategy.md` |
| Idempotency keys, verb semantics, side effects | `references/common/idempotency-and-retries.md` |
| Multi-turn submit/validate/repair/resume | `references/common/iterative-loops.md` |
| Tool count, response size, token budget | `references/common/agent-cognitive-load.md` |
| Survival across real subprocess + MCP harnesses | `references/common/agent-integration.md` |
| Existing-tool audit rhythm | `references/common/audit-rhythm.md` |
| Workload-first new-tool design | `references/common/design-thinking.md` |
| Production CLI/MCP precedent | `references/common/exemplars.md` |

### 4. Route surface-specific work

After the surface decision lands, route by direction:

- **CLI design** → `references/cli/architect-new.md`
- **CLI audit** → `references/cli/audit-checklist.md`
- **MCP design** → `references/mcp/architect-new.md`
- **MCP audit** → `references/mcp/audit-existing.md`
- **MCP build** → `build-mcp-server-sdk-v1` / `build-mcp-server-sdk-v2` / `build-mcp-use-server`
- **MCP test** → `test-by-mcpc-cli`

## Output contracts

### Mode A audit

```markdown
Mode: Mode A — audit existing surface
Target path: path/to/tool

Scorecard:
| Dimension | Score | Evidence |
|---|---:|---|
| discovery        | 0-5 | file:line |
| input/schema     | 0-5 | file:line |
| output           | 0-5 | file:line |
| error/retry      | 0-5 | file:line |
| auth/headless    | 0-5 | file:line |
| state/iteration  | 0-5 | file:line |
| operations       | 0-5 | file:line |

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

### Mode B architecture sketch

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

## Reference routing

### Common (`references/common/`)

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

### CLI (`references/cli/`)

| File | Read when |
|---|---|
| `references/cli/architect-new.md` | Designing a new agent-ready CLI after the surface decision lands on CLI. |
| `references/cli/audit-checklist.md` | Auditing an existing CLI for stdout/stderr, exit codes, headless mode, structured errors, parsing reliability. |
| `references/cli/auth-headless.md` | CLI auth must work in CI, containers, remote shells, or non-interactive agent runs. |
| `references/cli/code-templates.md` | A small scaffold or implementation template is needed after CLI contract design. |
| `references/cli/exit-codes.md` | Exit-code taxonomy or retry/escalation classification is in scope. |
| `references/cli/flags-and-discovery.md` | Help text, standard flags, TTY detection, or CLI discovery is in scope. |
| `references/cli/iterative-pattern.md` | CLI needs validate-repair-advance phases, state tokens, or NDJSON progress. |
| `references/cli/output-envelope.md` | CLI JSON envelope, error object, pagination, or streaming output shape is in scope. |
| `references/cli/subprocess-harness.md` | A CLI must be exercised from a realistic agent subprocess harness. |

### MCP (`references/mcp/`)

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
| `references/mcp/patterns/client-compatibility.md` | Client support differences across MCP clients matter. |
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

## Script routing

Deterministic helpers are **preflight evidence only** — never a substitute for the audit.

| Script | Read first | Use when |
|---|---|---|
| `scripts/audit-cli.sh` | `scripts/audit-cli.md` | Quick static/behavioral CLI preflight on a safe local probe command. |
| `scripts/audit-mcp.sh` | `scripts/audit-mcp.md` | Conservative MCP source scan for registrations, schemas, transports, error patterns. |

## Final checks

Before declaring done:

- [ ] Mode is named explicitly (A/B/C/D/E).
- [ ] Surface recommendation uses the required five-line shape when surface was in scope.
- [ ] Mode A includes scorecard, findings, fix options with evidence, and rung reached.
- [ ] Mode B names workload, surface, command/tool set, output, error, auth, state, test plan, handoff skill.
- [ ] Every recommendation cites a `references/...` file or companion skill.
- [ ] MCP implementation handoff names `build-mcp-server-sdk-v1`, `build-mcp-server-sdk-v2`, or `build-mcp-use-server`.
- [ ] MCP test handoff names `test-by-mcpc-cli` when end-to-end verification is required.
- [ ] Verification rung claimed matches the rung actually reached.
