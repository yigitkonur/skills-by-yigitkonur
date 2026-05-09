---
name: optimize-agentic-cli
description: "Use skill if you are auditing a CLI for agent-readiness, designing agent-first command contracts, or adding iterative feedback loops for repairable machine-generated artifacts."
---

# optimize-agentic-cli

Make CLIs reliable for agent use. The priorities are stable machine output, semantic exit codes, non-interactive operation, explicit recovery paths, and help text that an agent can treat as an API contract. For workflows that improve outputs over multiple passes, design the CLI as an iterative feedback loop instead of a one-shot command.

## Trigger Boundary

Use this skill for:

- auditing or designing shell CLI command surfaces
- stdout/stderr contracts, JSON envelopes, exit codes, and structured errors
- non-interactive modes, destructive-flow flags, and dry-run behavior
- repair-loop command protocols for machine-generated artifacts

Do not use this skill for:

- MCP server architecture, MCP tool schemas, MCP transport/auth/session design, or protocol-level testing; route surface decisions through `optimize-agent-ergonomics` and MCP implementation/testing through the repo's MCP build/test skills
- vendor-specific operational answers when a vendor skill exists; use `use-railway` for Railway CLI and `use-linear-cli` for Linear CLI
- generic shell scripting unless the CLI contract itself is the problem

Common triggers:

- an agent keeps failing to parse a CLI result
- stdout mixes JSON with progress text
- every failure exits `1` with no structured error body
- a command hangs waiting for interactive confirmation
- a workflow validates, rejects, repairs, and resubmits generated artifacts
- a fresh CLI needs agent-first constraints from day one
- the surface decision is CLI-first, MCP-first, or hybrid

If the user is choosing between CLI, MCP, skills, or a hybrid, read `references/mcp-vs-cli-decision.md` before recommending an interface.

## Load Map

Read the smallest reference set that matches the task:

| Problem | Read |
|---|---|
| Output, JSON, stream separation, exit codes, structured errors | `references/output-contracts.md` |
| Retries, idempotency, async jobs, batch, timeout, pagination, rate limits | `references/execution-patterns.md` |
| Help, auth, config, flags, environment detection | `references/discovery-and-auth.md` |
| Generated artifact repair loops | `references/iterative-cli.md` |
| CLI vs MCP vs hybrid decisions | `references/mcp-vs-cli-decision.md` |
| Implementation code examples and real-world audits | `references/examples.md` |
| Agent wrapper and invocation patterns | `references/agent-integration.md` |

Canonical homes:

- JSON envelopes, structured errors, stream separation, and exit-code taxonomy live in `references/output-contracts.md`.
- Standard flags, help text, auth, config, and environment detection live in `references/discovery-and-auth.md`.
- Retry, idempotency, async, batch, timeout, pagination, rate-limit, and continuation patterns live in `references/execution-patterns.md`.

## Bundled Scripts

Use the scripts only for read-only discovery support:

| Script | Read first | Use for |
|---|---|---|
| `scripts/audit-cli-help.sh` | `scripts/audit-cli-help.md` | Inspect top-level and listed subcommand help for standard flags, examples, exit-code docs, and missing affordances. |
| `scripts/diff-cli-help.sh` | `scripts/diff-cli-help.md` | Compare captured help snapshots for command/flag additions, removals, and likely breaking changes. |

These scripts audit discoverability and drift only. They do not prove full agent-readiness and must not replace stdout/stderr, exit-code, non-interactive, and destructive-flow checks.

## Local Exemplars

- `use-linear-cli` is the strong agent-ready CLI model: JSON everywhere, `--dry-run`, `--id-only`, non-pager flags, an exit-code contract, and bulk mutation gates.
- `use-railway` is the drift-aware CLI model: installed-help snapshot, upstream-vs-local distinction, refresh scripts, and version-drift routing.

## Audit Workflow

Before recommending changes:

1. Inspect top-level help and each relevant subcommand help.
2. Check machine-readable output flags such as `--json`, `--output json`, `--quiet`, `--fields`, or `--jq`.
3. Test stdout/stderr separation with safe read-only commands.
4. Classify exit codes and structured errors from success, usage, auth, not-found, validation, conflict, and transient paths.
5. Check non-interactive behavior for prompt-prone commands.
6. Inspect destructive-flow safety: `--dry-run`, `--yes`, `--force`, and explicit confirmation semantics.
7. Verify documentation states realistic examples, output fields, and exit codes.

## Severity

Classify findings in agent terms:

| Severity | Use when |
|---|---|
| Critical | Agents cannot safely parse, continue, or avoid unintended side effects. Example: JSON mixed with progress text on stdout. |
| High | Agents can act but are likely to fail, retry incorrectly, or block. Example: prompts with no `--no-input` or `--yes` path. |
| Medium | Agents can finish with extra probing or brittle assumptions. Example: missing help examples or undocumented output fields. |
| Low | Polish or consistency issue with little task risk. Example: nonstandard flag alias when the long flag is documented. |

## Core Audit

Verify these first:

1. `--json` or equivalent exists and stdout is pure machine output.
2. Logs, spinners, and progress text go to stderr.
3. Exit codes distinguish usage, auth, not-found, conflict, validation, and transient failures.
4. Headless runs never block without a non-interactive flag or a clear error.
5. Error responses include a stable code plus retryability guidance.

If any of those fail, fix them before adding nicer features.

If a command must emit a non-JSON artifact such as a patch, diff, query, prompt block, or translation segment, keep stdout machine-readable anyway. Use one canonical artifact format plus a reserved, parseable sidecar or a separate status command. Do not mix in ad-hoc prose.

## Output Contract

Choose one deliverable shape based on the task:

### Audit report

Return:

- scorecard by audit dimension
- severity-ranked findings
- command evidence: exact safe command, stdout/stderr/exit-code observation
- why the issue matters for agents
- recommended fix
- verification command

### Refactored CLI contract

Return:

- proposed command grammar
- flags and non-interactive behavior
- stdout/stderr rules
- JSON envelope and stream format
- exit-code map
- migration notes for existing users and scripts

### Iterative repair-loop design

Return:

- phases and command family
- artifact channel
- validation response shape
- retry budget
- `next_action.command`
- finalization criteria

## Design Rules

- Prefer one stable envelope shape across commands.
- Treat stdout as the data channel and stderr as the operator channel.
- Keep command names and field types consistent across releases.
- Make destructive flows explicit with `--yes`, `--force`, or `--dry-run`.
- Document examples, output fields, and exit codes in `--help`.
- When a workflow can be repaired iteratively, return structured feedback that tells the agent what failed, what to fix, and what to run next.

## Minimal Output Contract

Aim for a stable JSON envelope like:

```json
{
  "ok": true,
  "result": {},
  "error": null,
  "schema_version": "v1"
}
```

And on failure:

```json
{
  "ok": false,
  "result": null,
  "error": {
    "class": "validation",
    "code": "MISSING_FLAG",
    "message": "Flag --target is required.",
    "retryable": false,
    "suggestion": "Run `mycli deploy --target <name>`."
  },
  "schema_version": "v1"
}
```

## Build Order

When repairing an existing CLI, work in this order:

1. Pure JSON output and stdout/stderr separation.
2. Structured errors and semantic exit codes.
3. Non-interactive flags and safe defaults.
4. Iterative feedback loops for commands that produce artifacts requiring repair or resubmission.
5. Better discovery through help text and examples.
6. Async, JSONL, or job-style flows if operations are long-running.

## Iterative CLI

Use an iterative CLI pattern when an agent is expected to generate an artifact, submit it, receive validation feedback, and improve it over multiple attempts.

Core loop:

```text
input artifact -> CLI validation -> structured diff/errors -> agent repair -> retry -> accepted artifact -> finalize
```

Typical fits:
- translation or localization workflows that operate batch by batch
- code generation or patch application that needs validation before acceptance
- manifest, config, or migration generation where the CLI can point out exact defects
- import, sync, or bulk-edit tools where partial progress and retryability matter

Each iteration should tell the agent:
- what stage it is in now
- whether the artifact was accepted, rejected, or only partially accepted
- what exactly failed, with identifiers or locations when possible
- whether the failure is retryable
- what command or action to run next
- how much progress is complete and how much work remains

One-shot read, list, get, or status commands do not need session state or staged repair commands. Use the simpler JSON envelope.

Read `references/iterative-cli.md` for the design pattern and case study.

## CLI Vs MCP

Stay with a CLI when:
- a mature CLI already exists and the workflow is command-shaped
- shell composition, files, or pipes are central to the task
- the agent only needs process execution plus stable parsing
- the operator is a developer or trusted local runtime

Prefer MCP when:
- the workflow needs per-user auth, approvals, or tenant isolation
- the agent benefits from typed tool schemas instead of shell parsing
- long interactive sessions or stateful tool orchestration dominate the use case
- no strong CLI exists and a shell wrapper would mostly reimplement a remote API

## Reference Routing

- `references/output-contracts.md` for JSON envelope design, schemas, and error fields.
- `references/execution-patterns.md` for async job models, retries, and long-running command flows.
- `references/discovery-and-auth.md` for help-driven discovery and auth handling.
- `references/iterative-cli.md` for feedback-loop CLIs that guide the agent through repair, resubmission, and finalization.
- `references/mcp-vs-cli-decision.md` for deciding whether a workflow should stay CLI-first, move to MCP, or split auth and discovery from execution.
- `references/examples.md` for worked audit and redesign examples.
- `references/agent-integration.md` for implementation patterns when another agent or service will invoke the CLI.

## Finish Criteria

Do not call a CLI agent-ready until:
- the five core audit checks pass
- the JSON shape is stable enough to script against
- the help text documents the command contract
- a non-interactive run can succeed or fail deterministically
- iterative workflows return enough structured feedback for an agent to repair output without human interpretation
