---
name: run-codex-subagents
description: "Use skill if you are orchestrating Codex coding agents via codex-worker CLI — spawning tasks, monitoring timeline progress, handling auto-answered questions, recovering partial work, or running multi-wave implementation plans."
---

# Orchestrate Codex Tasks with codex-worker

Use this skill when delegating coding, research, verification, or follow-up work to Codex workers through the `codex-worker` CLI.

This is a CLI skill. Use shell commands, local artifact paths, and shell-native control flow.

## Trigger Boundaries

Use this skill for:
- launching Codex work from Markdown prompt files
- monitoring async runs with `task follow` or `task wait`
- handling blocked requests with `request list`, `request read`, and `request answer`
- reusing sessions via `--session`, steering completed tasks, coordinating multi-wave batches
- recovering failed runs from `task read`, `task events`, `read`, `logs`, and `doctor`

Do not use for:
- MCP server setup or `mcpc` testing
- changing `codex-worker` source code unless the user explicitly asks
- general Codex/OpenAI documentation questions

## Prerequisites

1. Verify the CLI: `codex-worker --help` or `npx -y codex-worker --help`
2. If unavailable, stop and tell the user.
3. Confirm runtime health: `codex-worker --output json doctor`
4. Prompts are file-backed. Write a `.md` file before dispatching.

## Two Command Layers

`codex-worker` has two layers. Use whichever fits:

| Layer | Commands | Best for |
|---|---|---|
| **Agent-friendly** (recommended) | `task start`, `task steer`, `task follow`, `task list`, `task read`, `task events`, `task wait`, `task cancel`, `session list/read`, `request answer` | Agents orchestrating work — auto-resolves turn ids, supports `--follow`, `--compact`, `--plan` |
| **Protocol-first** | `run`, `send`, `thread start/resume/read/list`, `turn start/steer/interrupt`, `request respond`, `wait`, `read`, `logs` | Direct thread/turn control, scripting with explicit ids |

The `task` commands wrap thread/turn operations. `task start` ≈ `run`, but defaults to async and supports `--follow --compact`. Use `task` when you want the CLI to handle id resolution and event streaming.

## Canonical Workflow

### 1. Write a task file

Every task file should specify: what to do, which files matter, what not to touch, success criteria, and verification commands.

### 2. Start the task

**Recommended** — async start with live streaming:

```bash
codex-worker task start task.md --follow --compact
```

**One-shot blocking** (simpler but no streaming):

```bash
codex-worker run task.md
```

**Async start** (return immediately, monitor later):

```bash
codex-worker --output json run task.md --async
```

Key flags for `run` and `task start`:
- `--follow` — stream events until completion (recommended for agents)
- `--compact` — concise emoji-prefixed event output (with `--follow`)
- `--plan` — instruct agent to plan before implementing
- `--skip-plan` — skip planning, implement directly
- `--effort <level>` — reasoning effort hint: `low`, `medium`, `high`
- `--label <text>` — task label for tracking in multi-wave batches
- `--session <id>` — continue an existing session/thread
- `--model <id>` — override model selection
- `--cwd <dir>` — working directory
- `--async` — return immediately with ids
- `--timeout <ms>` — wait timeout

### 3. Monitor

```bash
codex-worker task follow <thread-id>                    # stream events
codex-worker task follow <thread-id> --compact           # concise output
codex-worker task wait <thread-id>                       # block until done
codex-worker task wait <thread-id> --follow --compact    # block + stream
codex-worker task read <thread-id>                       # current state
codex-worker task read <thread-id> --field status        # extract single field
codex-worker task events <thread-id> --tail 10           # recent events
codex-worker task events <thread-id> --raw               # raw JSONL events
codex-worker task list --status running                  # running tasks only
codex-worker task list --quiet                           # thread ids only
```

### 4. Unblock requests

When a task pauses on approval or user input:

```bash
codex-worker request list --status pending
codex-worker request read <request-id>
codex-worker request answer <request-id> --decision accept    # approval
codex-worker request answer <request-id> --answer "Yes"       # free text
codex-worker request answer <request-id> --choice 1           # pick option by number
codex-worker request answer <request-id> --text-file reply.md # answer from file
```

Then resume monitoring: `codex-worker task follow <thread-id>`

### 5. Continue or recover

```bash
# Continue with new instructions (auto-resolves latest turn):
codex-worker task steer <thread-id> followup.md --follow --compact

# Or send directly on the thread:
codex-worker send <thread-id> followup.md

# Cancel a running task:
codex-worker task cancel <thread-id>
```

For failed tasks, always inspect before retrying:

```bash
codex-worker task read <thread-id>
codex-worker task events <thread-id> --tail 20
codex-worker logs <thread-id>
```

## Compact Output Format

With `--follow --compact`, events render as single emoji-prefixed lines:

```
👤 Build a REST API for user management...
🔧 bash (completed)
📝 created: src/routes/users.ts
💬 I've created the user management API with...
✅ Turn completed
```

This is the recommended default for agent use. It keeps context lean while showing meaningful progress.

## Quick Reference Table

| Need | Command |
|---|---|
| One-shot with streaming | `codex-worker task start task.md --follow --compact` |
| Async launch, monitor later | `codex-worker --output json run task.md --async` then `task follow <id>` |
| Plan before implementing | `codex-worker task start task.md --follow --compact --plan` |
| Continue same thread | `codex-worker task steer <id> followup.md --follow --compact` |
| Check task status | `codex-worker task read <id> --field status` |
| List failed tasks | `codex-worker task list --status failed` |
| Handle blocked request | `request list` → `request read` → `request answer` |
| Diagnose a failure | `task read` + `task events` + `logs` + `doctor` |
| Batch parallel tasks | separate `.md` files + `run task.md --async --label wave-1` for each |

## Handling Results

| Status | Meaning | Next move |
|---|---|---|
| `running` | task is active | `task follow`, `task wait`, or `task read` |
| `waiting_request` | blocked on runtime input | use `request` commands |
| `completed` | finished successfully | inspect artifacts or `task steer` |
| `failed` | ended with error | inspect artifacts, recover, retry |
| `interrupted` | cancelled or stopped | inspect artifacts, retry or steer |
| `idle` | thread created, no active turn | `turn start` or `task start --session` |

## Effort Levels

`task start` and `run` accept `--effort low|medium|high`.

- `low` — narrow edits, deterministic file work
- `medium` — multi-step implementation or refactors
- `high` — deep synthesis, complex architectural work

Do not compensate for vague prompts by raising effort. Tighten the task file first.

## Protocol-First Commands

When you need explicit thread/turn control:

```bash
codex-worker thread start --cwd /abs/project --model gpt-5.4
codex-worker turn start <thread-id> prompt.md
codex-worker turn steer <thread-id> <turn-id> followup.md
codex-worker turn interrupt <thread-id> <turn-id>
codex-worker thread list --limit 20
codex-worker read <thread-id> --tail 50
codex-worker logs <thread-id> --tail 100
codex-worker wait --thread-id <id> --timeout 300000
```

## Session Management

```bash
codex-worker session list                    # list all sessions/threads
codex-worker session read <session-id>       # read session state
```

To continue work in an existing session:

```bash
codex-worker task start task.md --session <session-id> --follow --compact
codex-worker run task.md --session <session-id>
```

## Runtime Inspection

```bash
codex-worker doctor                          # check prerequisites
codex-worker model list                      # available models
codex-worker account read                    # account info
codex-worker account rate-limits             # current limits
codex-worker daemon status                   # daemon state
```

## Machine-Readable Output

Use `--output json` for scripting:

```bash
codex-worker --output json task read <thread-id>
codex-worker --output json task list
codex-worker --output json run task.md --async
```

## State Layout

Default state root: `~/.codex-worker/` (override: `CODEX_WORKER_STATE_DIR`).

Key paths:
- `registry.json` — threads, turns, jobs, requests
- `daemon.json` / `daemon.sock` — daemon connection info
- `workspaces/<hash>/threads/<id>.jsonl` — transcript events
- `workspaces/<hash>/logs/<id>.output` — execution log

## Do This, Not That

| Do this | Not that |
|---|---|
| `task start --follow --compact` for live visibility | fire-and-forget without monitoring |
| `request answer` for blocked runs | assume the runtime auto-answered |
| `--output json` + `task read --field` for scripting | parse text output |
| inspect artifacts before retrying failures | immediately rerun the same prompt |
| `--session <id>` for intentional continuity | reuse sessions casually across unrelated tasks |
| `--plan` when work is complex | let the agent decide on plan vs. no-plan |

## Reference Files

| File | When to read |
|---|---|
| `references/command-reference.md` | Full command surface, all flags, output modes |
| `references/orchestration-patterns.md` | Sequential, parallel, session, batch patterns |
| `references/request-handling.md` | Handling blocked requests, answer payloads |
| `references/recovery-and-diagnostics.md` | Failed tasks, artifacts, doctor output |
| `references/composability-and-exit-codes.md` | Exit-code contracts, shell composability, scripting behavior |
| `references/prompt-bundles.md` | Multi-file prompt bundle structure and reuse patterns |
| `references/prompt-writing.md` | Writing effective Markdown task files |
| `references/runtime-config.md` | Runtime config inheritance, CODEX_HOME |
| `references/templates/coder-mission.md` | Implementation task template |
| `references/templates/research-mission.md` | Exploration/audit template |
| `references/templates/batch-wave.md` | Multi-wave orchestration template |
| `references/templates/test-runner.md` | Test execution template |

## Guardrails

- Do not mention MCP tools, MCP resources, or `task:///...` URIs.
- Do not assume blocked requests are auto-answered.
- Do not invent CLI flags. Run `--help` to verify before using.
- Do not reuse stale thread/request ids without reading their current state.
- Do not claim a task is irrecoverable until you have inspected `task read`, `task events`, `logs`, and `doctor`.
