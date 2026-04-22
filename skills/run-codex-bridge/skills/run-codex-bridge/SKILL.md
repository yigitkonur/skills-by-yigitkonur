---
name: run-codex-bridge
description: Use skill if you are orchestrating Codex work through the released codex-worker CLI and need correct run/send/thread/turn, request-response, wait, logs, or recovery commands.
---

# Orchestrate Codex Work with codex-worker

Use this skill when delegating coding, research, verification, or follow-up work through the **released** `codex-worker` CLI.

This skill intentionally tracks the public installed surface, not unreleased repo-local commands. Re-check `codex-worker --help` before relying on anything outside the references below.

## Trigger Boundaries

Use this skill for:
- launching file-backed Codex work through `codex-worker run`
- continuing an existing thread through `send`, `thread resume`, or `turn steer`
- monitoring progress through `read`, `logs`, and `wait`
- answering blocked runtime requests through `request list`, `request read`, and `request respond`
- recovering failed or interrupted work from local artifacts and daemon state

Do not use for:
- MCP server setup or `mcpc` testing
- changing `codex-worker` source code unless the user explicitly asks
- general Codex/OpenAI documentation questions

## Prerequisites

1. Verify the CLI:

   ```bash
   codex-worker --help
   ```

2. If it is missing, install it first:

   ```bash
   sudo -v ; curl -fsSL https://github.com/yigitkonur/codex-worker/releases/latest/download/install.sh | sudo bash
   ```

   Or user-local:

   ```bash
   curl -fsSL https://github.com/yigitkonur/codex-worker/releases/latest/download/install.sh | bash -s -- --install-dir "$HOME/.local/bin"
   ```

   Fallback:

   ```bash
   npm install -g codex-worker
   ```

3. Confirm runtime health:

   ```bash
   codex-worker --output json doctor
   ```

4. Prompts are file-backed. Write a `.md` file before dispatching.

## Current Command Families

| Group | Commands | Best for |
|---|---|---|
| Friendly aliases | `run`, `send`, `read`, `logs` | fastest file-backed orchestration flows |
| Protocol-first control | `thread start/resume/read/list`, `turn start/steer/interrupt`, `request respond`, `wait` | explicit thread/turn/request control |
| Diagnostics | `doctor`, `daemon start/status/stop` | environment and daemon checks |
| Environment inspection | `model list`, `account read/rate-limits`, `skills list`, `app list` | runtime visibility and discovery |

There is **no** `task` layer, **no** `session` layer, **no** `monitor`, **no** `review`, **no** `exec`, and **no** `request answer` helper in the released CLI this skill targets.

## Canonical Workflow

### 1. Write the prompt file

Each prompt file should define:
- what the worker should do
- which files matter
- what must not be touched
- what success looks like
- which commands prove success

### 2. Start the work

Blocking one-shot:

```bash
codex-worker run task.md
```

Async launch:

```bash
codex-worker --output json run task.md --async
```

Supported `run` flags in the released CLI:
- `--cwd <dir>`
- `--model <id>`
- `--async`
- `--timeout <ms>`

### 3. Monitor and inspect

Use the returned `threadId`:

```bash
codex-worker wait --thread-id <thread-id> --timeout 300000
codex-worker read <thread-id> --tail 50
codex-worker logs <thread-id> --tail 100
```

Use:
- `wait` to block on terminal state
- `read` for thread state plus local artifact paths
- `logs` for readable execution output

### 4. Answer blocked requests

When the thread status becomes `waiting_request`:

```bash
codex-worker request list --status pending
codex-worker request read <request-id>
codex-worker request respond <request-id> --decision accept
```

For free-text answers:

```bash
codex-worker request respond <request-id> --answer "Yes" --question-id <id>
```

For unusual payloads, inspect first and then use raw JSON:

```bash
codex-worker request respond <request-id> --json '{"result":{"approved":true}}'
```

### 5. Continue or recover

Friendly continuation:

```bash
codex-worker send <thread-id> followup.md
```

Protocol-first continuation:

```bash
codex-worker turn steer <thread-id> <turn-id> followup.md
```

Interrupt an active turn:

```bash
codex-worker turn interrupt <thread-id> <turn-id>
```

Inspect before retrying:

```bash
codex-worker read <thread-id> --tail 50
codex-worker logs <thread-id> --tail 100
codex-worker doctor
```

## Quick Reference

| Need | Command |
|---|---|
| One-shot task | `codex-worker run task.md` |
| Async launch | `codex-worker --output json run task.md --async` |
| Continue an existing thread | `codex-worker send <thread-id> followup.md` |
| Inspect thread state | `codex-worker read <thread-id> --tail 50` |
| Inspect readable logs | `codex-worker logs <thread-id> --tail 100` |
| Wait for completion | `codex-worker wait --thread-id <thread-id> --timeout 300000` |
| Answer a request | `codex-worker request respond <request-id> ...` |
| Read raw request payload | `codex-worker request read <request-id>` |
| Start a thread explicitly | `codex-worker thread start --cwd /abs/project --model gpt-5.4` |
| Start a turn explicitly | `codex-worker turn start <thread-id> prompt.md` |

## Status Meanings

Use `read` or `thread list` output to reason about state:

| Status | Meaning | Next move |
|---|---|---|
| `running` | turn is active | `wait`, `read`, or `logs` |
| `waiting_request` | blocked on runtime input | `request list` → `request read` → `request respond` |
| `completed` | turn finished successfully | inspect artifacts or send a follow-up |
| `failed` | turn ended with an error | inspect `read`, `logs`, and `doctor` |
| `interrupted` | turn was cancelled or stopped | inspect and decide whether to resume or restart |
| `idle` | thread exists without an active turn | `send`, `turn start`, or `thread resume` |

## Machine-Readable Output

Use `--output json` for shell composition:

```bash
codex-worker --output json run task.md --async
codex-worker --output json read <thread-id>
codex-worker --output json thread list --cwd /abs/project
codex-worker --output json request list --status pending
```

Prefer JSON output over parsing text.

## State Layout

Default state root: `~/.codex-worker/` (override: `CODEX_WORKER_STATE_DIR`).

Key paths:
- `registry.json` — local thread/turn/request state
- `daemon.json` / `daemon.sock` — daemon connection info
- `workspaces/<hash>/threads/<id>.jsonl` — transcript events
- `workspaces/<hash>/logs/<id>.output` — readable log
- `workspaces/<hash>/logs/<id>.raw.ndjson` — raw protocol log when available

## Reference Files

| File | When to read |
|---|---|
| `references/command-reference.md` | Full current command and flag surface for the released `codex-worker` CLI |
| `references/orchestration-patterns.md` | Blocking, async, continuation, and multi-wave orchestration loops |
| `references/request-handling.md` | Correct `request respond` payload patterns |
| `references/recovery-and-diagnostics.md` | Failure triage, artifact reading, and doctor usage |
| `references/composability-and-exit-codes.md` | JSON mode, shell composition, and command behavior |
| `references/prompt-bundles.md` | Prompt-file behavior and continuation patterns |
| `references/prompt-writing.md` | Writing better Markdown prompt files |
| `references/runtime-config.md` | Runtime inheritance and model/provider behavior |
| `references/templates/coder-mission.md` | Implementation prompt template |
| `references/templates/research-mission.md` | Audit/exploration prompt template |
| `references/templates/batch-wave.md` | Multi-wave orchestration prompt template |
| `references/templates/test-runner.md` | Verification-focused prompt template |
| `references/scripts/batch-status.sh` | Thread-list summary helper for multi-run shells |
| `references/scripts/merged-monitor.sh` | Merge raw monitor streams for threads that expose raw logs |

## Guardrails

- Do not invent a `task` or `session` subcommand layer.
- Do not use `request answer`; the released CLI only exposes `request respond`.
- Do not assume unreleased flags such as `--follow`, `--plan`, `--skip-plan`, `--label`, or `--compact` unless `--help` shows them.
- Do not rely on `monitor`, `review`, `exec`, or `thread rollback` unless you have verified you are on a newer unreleased build; they are not part of the released surface this skill targets.
- Do not reuse stale turn ids without re-reading current thread state.
- Do not treat `waiting_request` as failure.
- Do not claim a run is irrecoverable until you have checked `read`, `logs`, and `doctor`.
