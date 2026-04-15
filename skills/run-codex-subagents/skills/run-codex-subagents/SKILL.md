---
name: run-codex-subagents
description: "Use skill if you are orchestrating Codex coding agents with codex-worker across thread, turn, request, wait, and recovery flows for parallel or multi-step implementation work."
---

# run-codex-subagents

Use `codex-worker` as a CLI-first thread orchestrator. The modern surface is `run`, `send`, `read`, `logs`, `thread`, `turn`, `request`, `wait`, `doctor`, and `daemon`. Do not use retired `task`, `session`, `request answer`, `--choice`, `--text-file`, or `--auto-approve` examples.

## Install And Verify

Three install paths:

```bash
# 1. Throwaway (no install). Good for one-offs:
npx -y codex-worker --help

# 2. Global install. This is the canonical setup — puts the binary on PATH
#    so every shell, subagent, and editor can call it by name:
npm install -g codex-worker
codex-worker --version

# 3. Confirm the install landed on PATH:
which codex-worker
#   macOS with Homebrew-managed node: /opt/homebrew/bin/codex-worker
#   Other:  $(npm prefix -g)/bin/codex-worker
```

If `which codex-worker` prints nothing, your npm global bin is not on PATH. Check `npm prefix -g` — add its `bin/` subdirectory to `PATH` in `~/.zshrc` (or equivalent).

Then confirm the runtime is healthy:

```bash
codex-worker --output json doctor
```

Expect a JSON object with `node`, `codex`, `daemonRunning`, `stateRoot`, and `profiles`.

## Env Vars

Set inline for a single command, or export persistently. All variables are read per-call by the daemon, so inline overrides are always safe.

```bash
# Raise the per-turn idle watchdog from 30 min to 1 h, just for this run:
CODEX_WORKER_TURN_TIMEOUT_MS=3600000 codex-worker run task.md

# Disable the raw NDJSON firehose (rarely needed — it powers monitoring):
CODEX_WORKER_RAW_LOG=0 codex-worker run task.md

# Isolate the state root for sandboxed experiments:
CODEX_WORKER_STATE_DIR=/tmp/isolated codex-worker doctor

# Override the Codex profile dir:
CODEX_HOME=/path/to/alt codex-worker thread list
```

Persistent in `~/.zshrc`:

```bash
export CODEX_WORKER_TURN_TIMEOUT_MS=3600000
```

After changing a persistent value, `codex-worker daemon stop && codex-worker doctor` to pick up the new env. Full reference: `references/tool-reference.md`.

## Canonical Workflow

### 1. Start a new task from Markdown

Without a global install:

```bash
npx -y codex-worker run task.md
```

With a global install:

```bash
codex-worker run task.md
```

`run` creates a thread and starts its first turn from the Markdown file. If the command is attached to a TTY and not `--async`, it streams live notifications until the turn completes, fails, or blocks on a request.

### 2. Continue the same thread

```bash
codex-worker send <thread-id> followup.md
```

Use `send` when the prior turn already created the thread context you want to keep.

### 3. Background work and waiting

```bash
codex-worker --output json run task.md --async
codex-worker wait --thread-id <thread-id>
```

Async results include `threadId`, `turnId`, `job`, `pendingRequests`, and `actions`. Use `wait` when you only need terminal status, or `read` and `logs` when you need artifacts and recent output.

### 4. Protocol-first control

Use the protocol-first commands when you need explicit thread lifecycle control:

```bash
codex-worker --output json thread start --cwd /abs/project
codex-worker turn start <thread-id> prompt.md
codex-worker turn steer <thread-id> <turn-id> followup.md
codex-worker turn interrupt <thread-id> <turn-id>
```

`thread start` creates an idle thread. `turn start` adds a new turn to that thread. `turn steer` continues from a known turn boundary.

## Request Handling

Blocked turns surface through `request list`, `request read`, and `request respond`.

Approval requests:

```bash
codex-worker request list
codex-worker request read <request-id>
codex-worker request respond <request-id> --decision accept-session
```

Free-text or multiple-choice user-input requests:

```bash
codex-worker request respond <request-id> --question-id style --answer "Short"
```

Raw JSON payload when you need exact control:

```bash
codex-worker request respond <request-id> --json '{"answers":{"style":{"answers":["Short"]}}}'
```

For this CLI, multiple-choice answers are label-based. There is no supported `--choice` flag.

## Recovery And Inspection

Read the thread record and recent transcript/log tail:

```bash
codex-worker read <thread-id>
codex-worker logs <thread-id>
```

Use JSON when scripting:

```bash
codex-worker --output json read <thread-id>
codex-worker --output json thread list --limit 20
```

Important artifact fields from `read`:
- `artifacts.rawLogPath` — firehose NDJSON; the source of truth for live monitoring and post-mortems
- `artifacts.transcriptPath` — deduplicated structured transcript
- `artifacts.logPath` — plain-text tail (noisy for assistant deltas)
- `artifacts.recentEvents`
- `artifacts.displayLog`

Read `references/guides/log-artifacts.md` before tailing anything. Do not poll `Status:` to infer progress — it only flips at turn boundaries.

Default state root is `~/.codex-worker`. Override it with `CODEX_WORKER_STATE_DIR` when you need isolation.

## Translation Table For Old Docs

| Retired form | Use now |
|---|---|
| `cli-codex-subagent ...` | `codex-worker ...` |
| `task start` | `run` or `thread start` + `turn start` |
| `task follow` | foreground `run` / `send`, or `wait` + `read` / `logs` |
| `task read` | `read` or `thread read` |
| `task list` | `thread list` |
| `task steer` | `turn steer` |
| `task cancel` | `turn interrupt` |
| `request answer` | `request respond` |
| `--choice 1` | `--question-id <id> --answer "<label>"` |
| `~/.cli-codex-subagent/...` or `~/.mcp-codex-worker/...` | `~/.codex-worker/...` |

## Routing Guide

Read these references based on the work at hand:

- `references/tool-reference.md` for the current command surface, flags, env vars, and install commands.
- `references/guides/log-artifacts.md` for `rawLogPath`, `transcriptPath`, `logPath`, and when each is authoritative — read this before tailing anything.
- `references/resources-reference.md` for thread records, artifact paths, and state layout.
- `references/pause-flow-handling.md` for blocked turns and `request respond` payloads.
- `references/orchestration-patterns.md` for sequential, parallel, and steer-based execution patterns.
- `references/event-types.md` for live stream and persisted transcript event shapes.
- `references/timeline-format.md` for what `read`, `logs`, and TTY streaming actually show.
- `references/guides/auto-answer-behavior.md` for the current no-auto-answer behavior and safe response patterns.
- `references/guides/context-files.md` for structuring Markdown prompt files and inlining extra context.
- `references/guides/developer-instructions.md` for `thread start --developer-instructions` and `--base-instructions`.
- `references/guides/failure-diagnosis.md` for interpreting failed turns, blocked requests, and daemon/runtime issues.
- `references/guides/fleet-mode.md` for `CODEX_ENABLE_FLEET=1` behavior.
- `references/guides/labels-and-tracking.md` for naming and tracking waves without legacy label flags.
- `references/guides/mission-protocol-prompts.md` for prompt structure and mission-writing rules.
- `references/guides/monitoring-patterns.md` for `read`, `logs`, `wait`, and artifact-tail workflows.
- `references/guides/parallel-dispatch.md` for multi-thread async launch patterns.
- `references/guides/partial-work-recovery.md` for salvaging failed work on disk before retrying.
- `references/scripts/diagnostic-queries.md` for `jq`, shell, and Python snippets against transcript and log artifacts.
- `references/templates/batch-wave.md` for a reusable wave launcher and manifest pattern.
- `references/templates/coder-mission.md` for implementation-task prompt files.
- `references/templates/planning-mission.md` for planning-only prompt files.
- `references/templates/quick-diagnostic.md` for one-command probes.
- `references/templates/research-mission.md` for exploration and audit prompts.
- `references/templates/test-runner.md` for test-only prompt files.

Helper scripts shipped alongside this skill:
- `references/scripts/batch-status.sh`
- `references/scripts/merged-monitor.sh`

## Operating Rules

- Prefer `run` for one-shot work and `send` for follow-ups on the same thread.
- Prefer `thread start` plus `turn start` when you need explicit setup before the first turn.
- Use `--output json` for scripting and parsing. Text output is for interactive use.
- Treat `read` as the source of truth for artifacts, pending requests, and tracked turns.
- Recover partial work before retrying: inspect the workspace, build, test, then decide whether to `send` or start a new thread.
