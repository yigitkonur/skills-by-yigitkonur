---
name: run-codex-subagents
description: "Use skill if you are orchestrating Codex coding agents via mcp-codex-worker MCP tools — spawning tasks, monitoring timeline progress, handling auto-answered questions, recovering partial work, or running multi-wave implementation plans."
---

# Orchestrate Codex Workers

You are an orchestrator. You dispatch work to Codex coding agents, monitor their progress in real time, recover from failures gracefully, and deliver verified results. The prompt you write determines the quality of everything that follows.

## Prerequisites

5 MCP tools must be available from the `codex-worker` server:
- `spawn-task` — create and start a task
- `wait-task` — block until done, failed, or paused
- `respond-task` — answer a paused task
- `message-task` — steer a running task
- `cancel-task` — abort tasks

If missing, the server isn't connected. Stop and tell the user.

## The Core Loop

```
spawn-task → Monitor(timeline) → wait-task
  ├── completed    → use output
  ├── failed       → check disk for partial work → recover or retry
  ├── input_required → already auto-answered, check [auto-answer] in output
  └── working      → check Monitor events → wait again or abort
```

### MUST: Start the Monitor after every spawn

```
Monitor({
  command: "tail -f {disk_paths.timeline_log}",
  description: "Task {task_id} progress",
  timeout_ms: {task_timeout},
  persistent: false
})
```

Without this you are blind between spawn and completion. The timeline streams one-liners like `CMD npm test → exit=0 (1.2s)` and `THINK Considering approach...` so you see exactly what the agent is doing. Read `references/guides/monitoring-patterns.md` for merged multi-task monitors and diagnostic commands.

## Choosing Reasoning Level

The single most important parameter. It determines whether the task completes.

| Level | When | Reliability | Typical tokens |
|---|---|---|---|
| `gpt-5.4(low)` | 1-3 commands, simple file ops | ~100% | ~15K |
| `gpt-5.4(medium)` | Multi-step coding, refactoring | ~50-70% | 30-110K |
| `gpt-5.4(high)` | Complex multi-file reasoning | ~30-50% | 60-110K |
| `gpt-5.4(xhigh)` | Deep research, architecture | Untested | — |

**Default to `low` unless the task genuinely needs planning.** Higher reasoning = more tokens consumed thinking = higher chance of process exit before execution. A task that can be expressed as "run these 3 commands" should always use `low`. Read `references/guides/reasoning-levels.md` for the full decision framework.

## Writing Prompts That Work

Minimum: `{what to do} + {which files} + {expected outcome} + {what NOT to touch}`

For complex tasks, write a MISSION_PROTOCOL brief with: Context (why this exists, what happened before, what to read) → Mission Objective (observable end-state) → Hard Constraints → Definition of Done (binary, specific, verifiable) → Verification Commands.

Templates for common patterns:
- `references/templates/coder-mission.md` — file creation, extraction, refactoring
- `references/templates/research-mission.md` — codebase exploration
- `references/templates/quick-diagnostic.md` — single-command diagnostic
- `references/templates/batch-wave.md` — parallel wave dispatch

Read `references/guides/mission-protocol-prompts.md` for the complete prompt-writing framework.

## Task Types

| Type | Route to | Example |
|---|---|---|
| `coder` | Code writing/editing (default) | "Create BluetoothController.swift" |
| `tester` | Test execution | "Run swift test and report results" |
| `planner` | Decomposition | "Break this feature into 5 tasks" |
| `researcher` | Exploration | "Read every file under src/auth/ and summarize" |
| `general` | Anything else | "List all TODO comments in the project" |

Read `references/guides/task-types.md` for detailed routing guidance.

## Key Parameters

| Parameter | What it does | When to use |
|---|---|---|
| `reasoning` | Model + effort level | Always — determines reliability |
| `cwd` | Working directory | Always — agent sees files here |
| `labels` | Tags for filtering | Parallel batches — distinguish tasks |
| `developer_instructions` | System-level constraints | Cross-cutting rules (coding conventions, safety) |
| `context_files` | Prepend files as context | When agent needs specific file content upfront |
| `depends_on` | Task dependency chain | Sequential pipelines |
| `timeout_ms` | Hard time limit | Always — prevents runaway tasks |

Read `references/tool-reference.md` for full parameter schemas and response shapes.

## Handling Results

### Completed
Output in `output` array. Token usage in `token_usage` with `pct_used` percentage. Use the result directly.

### Failed (process exit)
**Don't panic — check for partial work.** The Codex agent often completes 80%+ of the work before dying. The recovery pattern:

1. `git status` or `ls` — new files?
2. Files exist → try building
3. Build passes → run tests
4. Tests pass → commit the agent's work yourself
5. Tests fail → fix the specific errors (you do 20%, agent did 80%)

Read `references/guides/partial-work-recovery.md` for the full pattern.

### Auto-answered questions
The MCP server auto-selects the first (recommended) option when the agent asks questions via `request_user_input`. You see `[auto-answer]` in the output. If wrong, steer via `message-task`. Read `references/guides/auto-answer-behavior.md`.

### Failure footers — always append these
When a task fails, include:
```
Task failed. Recovery options:
- View timeline: read task:///{id}/timeline
- View events: read task:///{id}/events
- Retry: spawn-task with same params
- If auto-answered wrong: retry + steer via message-task after spawn
```

## Parallel Dispatch

Spawn all tasks in one message. They run concurrently.

**Warning: shared process.** All parallel tasks share one Codex process. If one triggers an exit, all siblings die at the same millisecond. Design for this:
- Don't batch your most critical task with experimental ones
- Completed tasks survive (results captured before exit)
- Check scoreboard for same-timestamp EXIT events

Merge monitor streams:
```
Monitor({
  command: "for id in {id1} {id2} {id3}; do tail -f ~/.mcp-codex-worker/tasks/$id/timeline.log | sed --unbuffered 's/^/[$id] /' & done; wait",
  description: "Wave N parallel tasks",
  timeout_ms: 300000,
  persistent: false
})
```

Read `references/guides/parallel-dispatch.md` and `references/orchestration-patterns.md`.

## Resources (7 URIs)

| URI | Returns | Use for |
|---|---|---|
| `task:///all` | Scoreboard: badges, labels, timing, pending questions | Track all tasks |
| `task:///{id}` | Metadata: reasoning, cwd, timestamps, status | Inspect one task |
| `task:///{id}/log` | Last 20 summary lines | Quick output |
| `task:///{id}/log.verbose` | Full disk-backed transcript | Deep inspection |
| `task:///{id}/events` | Full JSONL (all notifications) | Debug trace |
| `task:///{id}/events/summary` | Filtered JSONL (no deltas/hooks) | Clean events |
| `task:///{id}/timeline` | One-liner per meaningful event | Progress overview |

Read `references/resources-reference.md` for response shapes and examples.

## Timeline Format

The timeline is your primary monitoring tool. Each line:
```
HH:MM:SS TAG     detail
```

| Tag | Meaning |
|---|---|
| VERSION | Server version stamp |
| STARTED | Task began |
| TURN | New conversation turn |
| THINK | Agent reasoning (with summary if available) |
| PLAN | Agent's plan with status icons: [✓] done [→] active [ ] pending |
| CMD | Command executed: `{cmd} → exit={code} ({duration})` |
| FILE | File changed: `{path} ({kind})` |
| MSG | Agent message (truncated at 200 chars) |
| MCP | MCP tool call: `{server}/{tool} → {status}` |
| TOKENS | Token usage: `{used} / {window} ({pct}%)` |
| AUTO | Auto-answered question: `{question} → "{answer}"` |
| APPROVE | Approval request (auto-accepted) |
| ASK | Waiting for orchestrator input |
| STDERR | Process error output |
| EXIT | Process exited: `code={N} signal={S}` |
| DONE | Turn completed: `{status}` |

Read `references/timeline-format.md` for all 16 types with examples.

## Decision Tree

```
What do you need?
├── Quick single command → spawn(low) → wait → done
├── Multi-step coding → spawn(medium) + Monitor → wait → recover if needed
├── Multiple independent tasks → spawn all + merged Monitor → wait each
├── Tasks with dependencies → depends_on or sequential spawn→wait
├── Steer running task → message-task → wait-task
├── Cancel work → cancel-task (single or batch array)
├── Diagnose failure → read timeline → check events → check disk
└── Continue after completion → spawn new task in same cwd
```

## Reference Index

### Guides (read for understanding)
| File | Covers |
|---|---|
| `references/guides/reasoning-levels.md` | When to use low/medium/high/xhigh with reliability data |
| `references/guides/mission-protocol-prompts.md` | Writing MISSION_PROTOCOL briefs that produce quality work |
| `references/guides/partial-work-recovery.md` | Recovering 80%-done work from failed tasks |
| `references/guides/parallel-dispatch.md` | Wave execution, shared-process risk, batch design |
| `references/guides/monitoring-patterns.md` | Monitor integration, merged streams, diagnostics |
| `references/guides/developer-instructions.md` | System-level instruction injection |
| `references/guides/task-types.md` | Coder vs planner vs tester vs researcher routing |
| `references/guides/token-budget.md` | Context usage, reasoning overhead, budget estimation |
| `references/guides/failure-diagnosis.md` | Reading timelines, exit codes, STDERR analysis |
| `references/guides/auto-answer-behavior.md` | How requestUserInput auto-resolves and steering |
| `references/guides/labels-and-tracking.md` | Labels, scoreboard filtering, batch management |
| `references/guides/fleet-mode.md` | Multi-profile execution |
| `references/guides/context-files.md` | Prepending files, size considerations |

### Templates (copy-paste starters)
| File | For |
|---|---|
| `references/templates/coder-mission.md` | Standard coding task |
| `references/templates/research-mission.md` | Codebase exploration |
| `references/templates/planning-mission.md` | Architecture decomposition |
| `references/templates/quick-diagnostic.md` | Single-command check |
| `references/templates/batch-wave.md` | Parallel wave dispatch |
| `references/templates/test-runner.md` | Test suite execution |

### Specs (exact schemas)
| File | Covers |
|---|---|
| `references/tool-reference.md` | All 5 tools: parameters, responses, constraints |
| `references/pause-flow-handling.md` | 5 pause types, auto-answer, response formats |
| `references/orchestration-patterns.md` | 8 execution patterns with examples |
| `references/timeline-format.md` | All 16 timeline line types |
| `references/event-types.md` | Codex notification types and where they're captured |
| `references/resources-reference.md` | All 7 resource URIs with response shapes |

### Scripts (ready to run)
| File | Does |
|---|---|
| `references/scripts/diagnostic-queries.md` | jq one-liners for event analysis |
| `references/scripts/merged-monitor.sh` | Multi-task merged timeline monitor |
| `references/scripts/batch-status.sh` | Wave status checker |
