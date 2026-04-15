---
name: optimize-cli-for-agents
description: "Use skill if you are auditing a CLI for agent-readiness, fixing output contracts, or designing a new CLI with AI agents as primary operators."
---

# optimize-cli-for-agents

Make CLIs reliable for agent use. The priorities are stable machine output, semantic exit codes, non-interactive operation, explicit recovery paths, and help text that an agent can treat as an API contract.

## When To Use

Use this skill when:
- an agent keeps failing to parse a CLI result
- stdout mixes JSON with progress text
- every failure exits `1` with no structured error body
- a command hangs waiting for interactive confirmation
- you are designing a fresh CLI and want agent-first constraints from day one
- you need to decide whether a workflow should stay CLI-first, move to MCP, or split into a hybrid

If the user is choosing between CLI, MCP, skills, or a hybrid, read `references/mcp-vs-cli-decision.md` before recommending an interface.

## Core Audit

Verify these first:

1. `--json` or equivalent exists and stdout is pure machine output.
2. Logs, spinners, and progress text go to stderr.
3. Exit codes distinguish usage, auth, not-found, conflict, validation, and transient failures.
4. Headless runs never block without a non-interactive flag or a clear error.
5. Error responses include a stable code plus retryability guidance.

If any of those fail, fix them before adding nicer features.

## Design Rules

- Prefer one stable envelope shape across commands.
- Treat stdout as the data channel and stderr as the operator channel.
- Keep command names and field types consistent across releases.
- Make destructive flows explicit with `--yes`, `--force`, or `--dry-run`.
- Document examples, output fields, and exit codes in `--help`.

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
4. Better discovery through help text and examples.
5. Async, JSONL, or job-style flows if operations are long-running.

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
- `references/mcp-vs-cli-decision.md` for deciding whether a workflow should stay CLI-first, move to MCP, or split auth and discovery from execution.
- `references/examples.md` for worked audit and redesign examples.
- `references/agent-integration.md` for implementation patterns when another agent or service will invoke the CLI.

## Finish Criteria

Do not call a CLI agent-ready until:
- the five core audit checks pass
- the JSON shape is stable enough to script against
- the help text documents the command contract
- a non-interactive run can succeed or fail deterministically
