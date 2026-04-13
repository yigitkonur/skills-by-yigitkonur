---
name: run-codex-subagents
description: "Use skill if you are orchestrating Codex coding agents via the cli-codex-subagent CLI — spawning tasks, monitoring timeline progress, handling approval requests, recovering partial work, or running multi-wave implementation plans."
---

# Orchestrate Codex Workers via CLI

You are an orchestrator. You dispatch work to Codex coding agents using the `cli-codex-subagent` CLI, monitor their progress in real time, recover from failures gracefully, and deliver verified results. The prompt file you write determines the quality of everything that follows.

## Prerequisites

The `cli-codex-subagent` daemon must be reachable. Check with:

```bash
cli-codex-subagent doctor
```

The daemon auto-starts on first use. If `doctor` shows errors, the Codex runtime may not be installed. Stop and tell the user.

## Core Loop

```
run task.md --follow
  ├── DONE completed  → use output / artifacts
  ├── exit 1 failed   → check disk for partial work → recover or retry
  ├── exit 2 blocked  → request list → request answer → task follow
  └── exit 3 reconnect error → retry or check network
```

### One-shot (most common)

```bash
cli-codex-subagent run task.md --follow --auto-approve
```

`--follow` streams all events and blocks until done. `--auto-approve` skips shell-command approval prompts.

### Async (fire-and-forget for parallel work)

```bash
# Spawn, get task id immediately
cli-codex-subagent run task.md --json
# Returns: { "taskId": "tsk_...", "sessionId": "ses_..." }

# Later: block until done
cli-codex-subagent task wait tsk_abc123

# Or stream events
cli-codex-subagent task follow tsk_abc123
```

## Command Reference

### Spawn a task

```bash
# Shorthand (most common)
cli-codex-subagent run task.md [options]

# Explicit
cli-codex-subagent task start task.md [options]
```

**Key flags:**

| Flag | What it does | When to use |
|------|-------------|-------------|
| `--effort <level>` | Reasoning depth: `none\|minimal\|low\|medium\|high\|xhigh` | Always — determines reliability |
| `--auto-approve` | Auto-accept all shell command approvals | Autonomous mode |
| `--approval-policy <p>` | `never\|on-failure\|on-request\|untrusted` | Fine-grained control |
| `--follow` | Stream events, block until terminal | Interactive / foreground runs |
| `--wait` | Block until terminal, no streaming | CI / scripted pipelines |
| `--session <sesId>` | Attach to existing session | Continue prior context |
| `--context-file <f>` | Prepend file as context (repeatable) | Supply reference files |
| `--output-schema <f>` | JSON Schema file for structured output | When structured JSON output required |
| `--label <label>` | Tag for filtering | Parallel batches |
| `--model <model>` | Override model | When specific model required |

**Frontmatter alternative** — put options in the task file header:

```markdown
---
label: "My Task"
effort: low
session: ses_abc123
context_files:
  - ./notes.md
  - ./schema.ts
output_schema: ./response-schema.json
---

Your task prompt goes here...
```

### Monitor a running task

```bash
# Stream live events (attach to already-running task)
cli-codex-subagent task follow tsk_abc123

# Stream as JSON for scripting
cli-codex-subagent task follow tsk_abc123 --stream-json
```

### Block until done

```bash
cli-codex-subagent task wait tsk_abc123
```

### Inspect task state

```bash
# Summary + artifact paths
cli-codex-subagent task read tsk_abc123

# Specific field (for scripting)
cli-codex-subagent task read tsk_abc123 --field status
cli-codex-subagent task read tsk_abc123 --field artifacts.handoffManifestPath

# Event log (all notifications)
cli-codex-subagent task events tsk_abc123

# Raw app-server events
cli-codex-subagent task events tsk_abc123 --raw

# Last N events only
cli-codex-subagent task events tsk_abc123 --tail 20
```

### List tasks

```bash
cli-codex-subagent task list
cli-codex-subagent task list --status failed
cli-codex-subagent task list --label "wave-1" --json
cli-codex-subagent task list --quiet   # ids only
```

### Steer (continue after completion)

```bash
cli-codex-subagent task steer tsk_abc123 followup.md [--follow] [--effort low]
```

Use when a prior task has **completed** and you want to continue in the same session with new instructions. The agent retains full prior context.

### Handle approvals and input requests

When a task blocks on a shell-command approval or user input, `--follow` exits with code `2` and prints the blocking request id.

```bash
# Find what's blocked
cli-codex-subagent request list

# Inspect the request
cli-codex-subagent request read req_abc123

# Answer an approval
cli-codex-subagent request answer req_abc123 --decision accept-session

# Answer a multiple-choice prompt (1-indexed)
cli-codex-subagent request answer req_abc123 --choice 1

# Answer with free text
cli-codex-subagent request answer req_abc123 --text-file answer.txt

# Advanced / custom payload
cli-codex-subagent request answer req_abc123 --json-file payload.json

# Then resume following
cli-codex-subagent task follow tsk_abc123
```

### Cancel a task

```bash
cli-codex-subagent task cancel tsk_abc123
```

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| `0` | Completed successfully | Use output |
| `1` | Task failed | Check partial work on disk, see recovery below |
| `2` | Blocked — needs `request answer` | `request list` → `request answer` → `task follow` |
| `3` | Reconnect / network error | Retry or check network |
| `5` | Task file not found | Use absolute path: `/path/to/task.md` |

## Event Stream Format

`--follow` and `task follow` print normalized events. Key line types:

| Tag | Meaning |
|-----|---------|
| `TURN` | New conversation turn metadata |
| `MSG` | Agent message text token |
| `FILE` | File written/changed: `path (kind)` |
| `TOKENS` | Token usage snapshot |
| `DONE` | Turn complete: `completed \| failed \| blocked` |

Full events (including reasoning, commands, MCP calls) are in:

```bash
cli-codex-subagent task events tsk_abc123
```

## Choosing Effort Level

The single most important parameter. It determines whether the task completes.

| Level | When | Reliability | Typical tokens |
|-------|------|-------------|----------------|
| `low` | 1–3 commands, simple file ops | ~100% | ~15K |
| `medium` | Multi-step coding, refactoring | ~50–70% | 30–110K |
| `high` | Complex multi-file reasoning | ~30–50% | 60–110K |
| `xhigh` | Deep research, architecture | Untested | — |

**Default to `low` unless the task genuinely needs planning.** Higher effort = more reasoning tokens = higher chance of process exit before execution. A task expressible as "run these 3 commands" should always use `low`.

## Writing Prompts That Work

Minimum: `{what to do} + {which files} + {expected outcome} + {what NOT to touch}`

For complex tasks, use a MISSION_PROTOCOL brief:

```markdown
---
effort: medium
label: "Feature: auth-refresh"
---

## Context
{Why this exists, what happened before, which files to read first}

## Mission
{Observable end-state — what exists / passes after success}

## Hard Constraints
- Do not modify {file}
- Do not install new dependencies

## Definition of Done
- [ ] {Binary, verifiable condition 1}
- [ ] {Binary, verifiable condition 2}

## Verification Commands
{Exact commands to run to confirm success}
```

## Parallel Dispatch

Spawn all tasks in one shell invocation. They run concurrently through the daemon.

```bash
# Async spawn — returns immediately with task ids
cli-codex-subagent run task-a.md --json   # note the taskId
cli-codex-subagent run task-b.md --json
cli-codex-subagent run task-c.md --json

# Block until each completes
cli-codex-subagent task wait tsk_111
cli-codex-subagent task wait tsk_222
cli-codex-subagent task wait tsk_333

# Or follow all simultaneously in separate terminals (or tmux panes)
cli-codex-subagent task follow tsk_111
```

**Warning: shared process.** All parallel tasks share one Codex process. If one triggers a crash, siblings may also die. Design for this:
- Don't batch your most critical task with experimental ones
- Completed tasks survive (results captured before exit)
- Check `task list --status failed` for casualties

## Handling Results

### Completed (`exit 0`)

Output is in the task artifacts directory:

```bash
cli-codex-subagent task read tsk_abc123
# Shows: status, session, artifact paths, event/summary tails
```

### Failed (`exit 1`) — check for partial work first

**Don't panic — the agent often completes 80%+ before failing.**

```bash
# 1. Check what was written to disk
git status   # or: ls -la <cwd>

# 2. Files exist → try building
npm run build  # or your build command

# 3. Build passes → run tests
npm test

# 4. Tests pass → commit the agent's work yourself
git add -A && git commit -m "Partial: agent completed 80%"

# 5. Tests fail → fix specific errors (you do 20%, agent did 80%)
```

### Blocked (`exit 2`) — answer the request

```bash
# Find pending request
cli-codex-subagent request list

# Inspect what it's asking
cli-codex-subagent request read req_abc123

# Answer and resume
cli-codex-subagent request answer req_abc123 --decision accept-session
cli-codex-subagent task follow tsk_abc123
```

### Failure footer — always append when a task fails

```
Task failed. Recovery options:
- View events: cli-codex-subagent task events <taskId>
- Read state:  cli-codex-subagent task read <taskId>
- Retry:       cli-codex-subagent run task.md --follow
- If blocked:  cli-codex-subagent request list
```

## Steering: Continuing After Completion

Use `task steer` when you want to iterate on a completed task without losing session context:

```bash
# Step 1: initial task
cli-codex-subagent run step1.md --wait

# Step 2: build on it in same session (use the task id from step 1)
cli-codex-subagent task steer tsk_step1id step2.md --follow
```

The steered task runs in the same session, so the agent remembers prior context.

## Multi-Wave Pipelines (Sequential Dependencies)

```bash
# Wave 1: plan (fast, low effort)
cli-codex-subagent run plan.md --effort low --wait

# Wave 2: implement (depends on plan output)
cli-codex-subagent run impl.md --effort medium --follow

# Wave 3: test (steer from impl task to keep session context)
cli-codex-subagent task steer tsk_impl_id test.md --follow
```

## Decision Tree

```
What do you need?
├── Quick single command  → run task.md --effort low --follow --auto-approve
├── Multi-step coding     → run task.md --effort medium --follow
├── Multiple independent  → async run each → task wait or task follow each
├── Tasks with deps       → wait wave N → run wave N+1
├── Continue in context   → task steer <taskId> followup.md --follow
├── Cancel work           → task cancel <taskId>
├── Diagnose failure      → task events <taskId> → task read <taskId>
├── Answer approval       → request list → request answer <reqId>
└── After blocking (exit 2) → request answer <reqId> → task follow <taskId>
```

## Session Management

```bash
# List sessions
cli-codex-subagent session list

# Read a session
cli-codex-subagent session read ses_abc123

# Start a task in an existing session (preserves context)
cli-codex-subagent run task.md --session ses_abc123 --follow
```

## Daemon Management

```bash
cli-codex-subagent daemon status   # Is it running?
cli-codex-subagent daemon stop     # Stop gracefully
cli-codex-subagent daemon run      # Run in foreground (debug)
cli-codex-subagent doctor          # Full readiness check
```

## Model and Account Inspection

```bash
cli-codex-subagent model list      # Available models
cli-codex-subagent account         # Rate limits and account info
```
