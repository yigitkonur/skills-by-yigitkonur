---
name: audit-agentic-cli
description: Use skill if you are auditing or designing a CLI for agent/LLM consumption — stable JSON output, exit codes, non-interactive flags, or iterative repair loops for machine-generated artifacts.
---

# audit-agentic-cli

Make a CLI an agent can drive without human babysitting. The contract: pure machine-readable stdout, semantic exit codes, non-interactive defaults, structured errors with retry guidance, and — for workflows that produce repairable artifacts — an iterative feedback loop the agent can finish on its own.

## When To Use

Trigger this skill when the user is doing CLI-only agent-readiness work:

- *"make my CLI agent-friendly"* / *"audit CLI for LLM use"*
- *the agent keeps failing to parse a CLI result*
- *stdout mixes JSON with progress text or spinners*
- *every failure exits 1 with no structured error body*
- *a command hangs waiting for an interactive prompt*
- *the workflow validates, rejects, repairs, and resubmits a generated artifact*
- *a fresh CLI needs agent-first constraints from day one*
- *help text is unreliable as a contract for an agent caller*

Do **not** use this skill for:

- **Surface choice (CLI vs MCP vs hybrid).** Make the surface decision first using your normal architecture process. Only after the surface decision is fixed as CLI does this skill apply.
- **MCP server audits, schemas, transports, auth, or context budgets.** Route to `audit-agentic-mcp` for audit/architecture, `build-mcp-server-sdk-v1` / `build-mcp-server-sdk-v2` / `build-mcp-use-server` for implementation, `test-by-mcpc-cli` for live MCP verification.
- **Vendor CLI operations** when a vendor skill exists. Use `run-railway` instead.
- **Generic shell scripting** unrelated to the CLI's agent contract.

## Five Core Audit Checks

Before recommending features, verify these. If any fail, fix them first.

1. `--json` (or equivalent) exists and **stdout is pure machine output** — no progress, no banners, no prose.
2. Logs, spinners, banners, and progress go to **stderr**.
3. **Exit codes** distinguish success, usage error, auth, not-found, conflict, validation, and transient/retryable failures — not all `0` or `1`.
4. Headless runs **never block** without an explicit `--no-input`/`--yes` path or a clear non-interactive error.
5. Error responses include a stable **error code** and a **retryable** boolean (or equivalent guidance).

When a command must emit a non-JSON artifact (patch, diff, query, prompt, translation), keep stdout one canonical artifact format and put status on stderr or in a sidecar — never mix prose into the data channel.

## Severity Rubric

Classify findings in agent terms, not human-UX terms.

| Severity | Use when |
|---|---|
| Critical | Agents cannot safely parse, continue, or avoid unintended side effects (e.g. JSON mixed with progress on stdout; destructive command with no `--dry-run`/`--yes`). |
| High | Agents act but are likely to fail, retry incorrectly, or block (e.g. prompt with no `--no-input`; opaque exit `1` for every error class). |
| Medium | Agents finish only with extra probing or brittle assumptions (e.g. undocumented output fields, missing help examples). |
| Low | Polish or consistency only (e.g. nonstandard alias when long flag is documented). |

## Minimum Output Envelope

Aim for one stable JSON envelope across all commands.

Success:

```json
{ "ok": true, "result": {}, "error": null, "schema_version": "v1" }
```

Failure:

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

Stdout = data channel. Stderr = operator channel. Exit code = semantic class. All three must agree.

## Build Order (Repair Existing CLI)

When fixing an existing CLI, do the work in this order. Skipping ahead wastes effort.

1. Pure JSON output and stdout/stderr separation.
2. Structured errors and semantic exit codes.
3. Non-interactive flags and safe defaults (`--no-input`, `--yes`, `--dry-run`).
4. Iterative feedback loops for any command whose output the agent might need to repair.
5. Discovery: help text, examples, documented exit codes and output fields.
6. Async / JSONL / job-style flows for long-running operations.

## Audit Workflow

Before recommending changes:

1. Inspect top-level help and each relevant subcommand. Use `scripts/audit-cli-help.sh` (read `scripts/audit-cli-help.md` first) to capture standard flags, examples, and missing affordances.
2. Look for machine-readable output flags: `--json`, `--output json`, `--quiet`, `--fields`, `--jq`.
3. Test stdout/stderr separation on safe read-only commands.
4. Classify exit codes across success, usage, auth, not-found, validation, conflict, and transient paths.
5. Probe non-interactive behavior on prompt-prone commands.
6. Inspect destructive flow safety: `--dry-run`, `--yes`, `--force`, explicit confirmation semantics.
7. Verify help documents realistic examples, output fields, and exit codes.
8. If auditing a CLI you've snapshotted before, diff with `scripts/diff-cli-help.sh` (read `scripts/diff-cli-help.md` first) to spot command/flag drift.

## Iterative Repair Loop

Use this pattern when an agent generates an artifact, the CLI validates it, and the agent must repair on rejection.

```
input artifact -> CLI validation -> structured diff/errors -> agent repair -> retry -> accepted -> finalize
```

Typical fits: translation/localization batches, code generation with validation gates, manifest/config/migration generation, bulk import or sync.

Each iteration must tell the agent:

- current stage
- accepted / rejected / partial
- what failed, with identifiers or locations
- whether the failure is retryable
- the next command to run (`next_action.command`)
- progress complete vs work remaining

One-shot read/list/get/status commands do not need this — use the simpler envelope.

For the full design pattern and a worked case study, read `references/iterative-cli.md`.

## Design Rules

- One stable envelope shape across all commands.
- Stdout = data. Stderr = operator. Exit code = semantic class.
- Command names and field types stay consistent across releases.
- Destructive flows are explicit: `--yes`, `--force`, `--dry-run`.
- `--help` documents examples, output fields, and exit codes.
- For repairable workflows, return enough structure for an agent to fix and retry without human interpretation.

## Output Contract (Deliverable Shape)

Pick one based on the task.

**Audit report:** scorecard by audit dimension, severity-ranked findings, command evidence (exact safe command + observed stdout/stderr/exit), why it matters for agents, recommended fix, verification command.

**Refactored CLI contract:** proposed command grammar, flags and non-interactive behavior, stdout/stderr rules, JSON envelope and stream format, exit-code map, migration notes for existing users and scripts.

**Iterative repair-loop design:** phases and command family, artifact channel, validation response shape, retry budget, `next_action.command`, finalization criteria.

## Local Exemplars

- `linear-cli` — strong agent-ready CLI: JSON everywhere, `--dry-run`, `--id-only`, non-pager flags, exit-code contract, bulk-mutation gates.
- `run-railway` — drift-aware CLI: installed-help snapshot, upstream-vs-local distinction, refresh scripts, version-drift routing.

## Reference Routing

Read the smallest reference set that matches the task.

| Problem | Read |
|---|---|
| JSON envelopes, schemas, error fields, stream separation, exit-code taxonomy | `references/output-contracts.md` |
| Retries, idempotency, async jobs, batch, timeout, pagination, rate limits | `references/execution-patterns.md` |
| Help, auth, config, flags, environment detection | `references/discovery-and-auth.md` |
| Iterative repair-loop CLI design and case study | `references/iterative-cli.md` |
| CLI vs MCP vs hybrid (when surface is still in question) | `references/mcp-vs-cli-decision.md` |
| Worked code examples (Go, Python, Node, Rust, Shell) and real-world audits | `references/examples.md` |
| Patterns for the agent or service that calls the CLI | `references/agent-integration.md` |

These are canonical homes — do not duplicate their content here.

## Bundled Scripts

Read-only discovery support. Do not treat them as agent-readiness proofs.

| Script | Read first | Use for |
|---|---|---|
| `scripts/audit-cli-help.sh` | `scripts/audit-cli-help.md` | Inspect top-level and subcommand help for standard flags, examples, exit-code docs, and missing affordances. |
| `scripts/diff-cli-help.sh` | `scripts/diff-cli-help.md` | Compare captured help snapshots for command/flag additions, removals, and likely breaking changes. |

These cover discoverability and drift only. They do not replace stdout/stderr, exit-code, non-interactive, and destructive-flow checks — run those by hand.

## Finish Criteria

Do not call a CLI agent-ready until:

- The five core audit checks pass.
- The JSON envelope is stable enough to script against across commands.
- `--help` documents the command contract (examples, output fields, exit codes).
- A non-interactive run can succeed or fail deterministically with no human keystroke.
- Any iterative workflow returns enough structured feedback for an agent to repair without human interpretation.
