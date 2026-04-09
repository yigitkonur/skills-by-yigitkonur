---
name: run-codex-subagents
description: "Use skill if you are orchestrating coding tasks via mcp-codex-worker MCP tools: spawning parallel agents, waiting for results, handling approvals, batch cancellation, or multi-wave execution plans."
---

# Run Codex Subagents

Orchestrate one or more Codex coding agents as subworkers through the mcp-codex-worker MCP server. Spawn tasks, wait for completion, handle approval pauses, send follow-up messages, cancel tasks, and monitor progress via live resources.

## Trigger boundary

Use when:
- Dispatching coding work to Codex subagents via MCP tools
- Running a multi-task implementation plan in waves
- Handling approval requests from a running Codex agent
- Monitoring task progress via scoreboard or detail resources
- Cancelling or batch-cancelling tasks

Do NOT use when:
- Building the mcp-codex-worker server itself (use `build-mcp-use-server`)
- Testing the MCP server with mcpc CLI (use `test-by-mcpc-cli`)
- Working directly in Claude Code without MCP delegation

## Prerequisites

The mcp-codex-worker MCP server must be connected. Verify these 5 tools are available:

- `mcp__codex-worker__spawn-task`
- `mcp__codex-worker__wait-task`
- `mcp__codex-worker__respond-task`
- `mcp__codex-worker__message-task`
- `mcp__codex-worker__cancel-task`

If tools are missing, the MCP server is not connected. Check your MCP server configuration.

## Core workflow

Every task follows this lifecycle:

```
spawn-task → wait-task ──┬── completed → done
                         ├── failed → read detail, retry or abort
                         ├── input_required → respond-task → wait-task (loop)
                         └── timeout → wait-task again or cancel-task
```

### The 5 tools

| Tool | Purpose | When to use |
|---|---|---|
| `spawn-task` | Create and start an agent | Beginning of any coding task |
| `wait-task` | Block until done or paused | After spawn, after respond |
| `respond-task` | Answer an agent's question | When wait returns `input_required` |
| `message-task` | Send follow-up to active agent | Mid-flight course correction |
| `cancel-task` | Abort one or many tasks | Cleanup, timeout, wrong direction |

### The 4 resources

| URI | What it shows |
|---|---|
| `task:///all` | Scoreboard — all tasks with status badges |
| `task:///{id}` | Detail — metadata, provider session, timestamps |
| `task:///{id}/log` | Summary — last 20 output lines |
| `task:///{id}/log.verbose` | Full — complete output history |

## Decision tree

```
What do you need?
├── Run a single coding task
│   └── Use Case 1: Single task
├── Run multiple independent tasks
│   └── Use Case 2: Parallel wave
├── Run tasks with dependencies
│   └── Use Case 3: Sequential chain
├── Handle an agent asking for approval
│   └── Use Case 4: Pause flow
├── Send a correction to a running agent
│   └── Use Case 5: Mid-flight steer
├── Continue work after a task completes
│   └── Use Case 6: Continuation
└── Abort tasks
    └── Use Case 7: Cancel and cleanup
```

---

## Use Case 1: Single task

Spawn one agent, wait for it, done.

**spawn-task:**
```
prompt: "Create src/utils/slugify.ts that exports a slugify(text: string): string function. Handle Unicode, collapse hyphens, trim edges."
cwd: "/path/to/project"
task_type: "coder"
```

**Key `spawn-task` parameters:**
- `prompt` (required) — be specific: include file paths, function names, expected behavior
- `cwd` — working directory. The agent sees files here. Defaults to server cwd.
- `task_type` — routes to provider. `coder` (default), `tester`, `planner`, `researcher`, `general`
- `model` — override provider default. Omit to use server config.
- `timeout_ms` — max execution time (1,000–3,600,000 ms)
- `developer_instructions` — system-level constraints injected before the prompt

**Response:** `{ task_id, status, poll_frequency, provider_session_id, resources }`

Then **wait-task** with the returned `task_id`:
```
task_id: "bold-falcon-42"
timeout_ms: 120000
poll_interval_ms: 2000
```

**`wait-task` returns when:**
- `completed` — task finished successfully
- `failed` — task errored (check `task:///{id}` for error message)
- `input_required` — agent needs approval or input (go to Use Case 4)
- `cancelled` — someone cancelled the task
- Timeout elapsed — returns current status; call wait-task again or cancel

## Use Case 2: Parallel wave

Spawn multiple tasks simultaneously. Each runs in an independent agent.

**Spawn all tasks first (do NOT wait between spawns):**
```
spawn-task: { prompt: "Task A...", cwd: "/project" }  → task_id: "able-fox-1"
spawn-task: { prompt: "Task B...", cwd: "/project" }  → task_id: "brave-cat-2"
spawn-task: { prompt: "Task C...", cwd: "/project" }  → task_id: "calm-dog-3"
```

**Monitor all via scoreboard resource:**
Read `task:///all` to see live status:
```
tasks -- 3 total (1 done, 2 busy)
[done] able-fox-1 -- "Task A..." (15s)
[busy] brave-cat-2 -- "Task B..." (8s)
[busy] calm-dog-3 -- "Task C..." (8s)
```

**Wait for each (order doesn't matter):**
```
wait-task: { task_id: "able-fox-1", timeout_ms: 120000 }
wait-task: { task_id: "brave-cat-2", timeout_ms: 120000 }
wait-task: { task_id: "calm-dog-3", timeout_ms: 120000 }
```

**Wave execution pattern:** For implementation plans with dependencies, group tasks into waves. Within a wave, tasks are independent. Between waves, earlier tasks must complete first.

```
Wave 1: [A, B, C] → spawn all, wait all
Wave 2: [D, E]    → spawn all, wait all (depends on Wave 1 outputs)
Wave 3: [F]       → spawn, wait (depends on Wave 2)
```

## Use Case 3: Sequential chain

Tasks share a working directory. The second task reads files the first task created.

```
spawn-task: { prompt: "Create schema.prisma with User and Post models", cwd: "/project" }
wait-task: { task_id: "..." }  → completed

spawn-task: { prompt: "Read schema.prisma and generate a migration SQL file", cwd: "/project" }
wait-task: { task_id: "..." }  → completed
```

The second agent sees `schema.prisma` because both share the same `cwd`.

**Use `depends_on` for explicit ordering:**
```
spawn-task: { prompt: "Task B", depends_on: ["task-id-of-A"] }
```
Tasks with unmet dependencies start in `submitted` state and auto-transition to `working` when dependencies complete.

## Use Case 4: Pause flow (approvals and questions)

When wait-task returns `input_required`, the agent is paused. The response includes a `pending_question` with a `type` field. Match the type to the correct respond-task shape.

**5 pause types and how to respond:**

| Pause type | Why it paused | respond-task fields |
|---|---|---|
| `user_input` | Agent has questions | `type: "user_input"`, `answers: { "q1": "answer" }` |
| `command_approval` | Agent wants to run a shell command | `type: "command_approval"`, `decision: "accept"` or `"reject"` |
| `file_approval` | Agent wants to write/modify files | `type: "file_approval"`, `decision: "accept"` or `"reject"` |
| `elicitation` | MCP server asking for confirmation | `type: "elicitation"`, `action: "accept"` or `"decline"` |
| `dynamic_tool` | Agent invoked an external tool | `type: "dynamic_tool"`, `result: "..."` or `error: "..."` |

**Approval loop pattern:**
```
wait-task → input_required (pending_question.type = "command_approval")
respond-task: { task_id, type: "command_approval", decision: "accept" }
wait-task → may return input_required again (next approval) or completed
```

Always call wait-task again after respond-task — the agent may have more questions.

For full parameter details: `references/pause-flow-handling.md`

## Use Case 5: Mid-flight steer

If an agent is going in the wrong direction, send a correction without cancelling.

```
message-task: {
  task_id: "brave-cat-2",
  message: "Stop working on the database migration. Instead focus on the API endpoint only."
}
```

**Constraint:** message-task only works on **active** tasks. If the task already completed, it returns a terminal-status rejection. See Use Case 6 for post-completion continuations.

## Use Case 6: Continuation after completion

A completed task's thread cannot receive new messages via message-task (FSM terminal state). Instead, spawn a new task in the **same `cwd`** — the new agent sees all files the previous agent created.

```
# First task created utils.ts
spawn-task: { prompt: "Create utils.ts with helpers", cwd: "/project" }
wait-task → completed

# New task reads utils.ts and builds on it
spawn-task: { prompt: "Read utils.ts and add unit tests in utils.test.ts", cwd: "/project" }
wait-task → completed
```

## Use Case 7: Cancel and cleanup

**Single cancel:**
```
cancel-task: { task_id: "calm-dog-3" }
→ { cancelled: ["calm-dog-3"], already_terminal: [], not_found: [] }
```

**Batch cancel (end of wave or abort all):**
```
cancel-task: { task_id: ["task-1", "task-2", "task-3", "bogus-id"] }
→ { cancelled: ["task-1", "task-2"], already_terminal: ["task-3"], not_found: ["bogus-id"] }
```

**Response categories:**
- `cancelled` — tasks that were actively running and got interrupted
- `already_terminal` — tasks already completed/failed/cancelled (no-op)
- `not_found` — unknown task IDs

**Note:** Cancel is best-effort. Fast-completing tasks may finish before the interrupt arrives.

## Wire states

Every status returned by tools maps to SEP-1686:

| Wire state | Meaning | Your action |
|---|---|---|
| `submitted` | Queued, not yet started | Wait |
| `working` | Agent is executing | Wait |
| `input_required` | Agent paused, needs response | Call respond-task |
| `completed` | Done successfully | Read results |
| `failed` | Errored | Read task detail for error |
| `cancelled` | Interrupted | Move on |
| `unknown` | Crash recovery fallback | Investigate or retry |

## Common pitfalls

| Pitfall | Fix |
|---|---|
| Vague prompts | Include file paths, function names, expected behavior |
| Waiting between parallel spawns | Spawn ALL tasks first, then wait for each |
| Calling message-task on completed tasks | Spawn a new task in the same cwd instead |
| Ignoring input_required | Always respond, then wait again |
| Not checking poll_frequency | Use the returned value as your poll interval |
| Missing cwd | Agent works in server's cwd — may not be your project |

## Guardrails

- Always include `cwd` when tasks operate on a specific project
- Always call wait-task after respond-task (agent may have more questions)
- Use batch cancel-task for cleanup after parallel waves
- Read `task:///all` scoreboard between waves to verify state
- Check `task:///{id}` detail resource for error messages on failed tasks
- Do not assume task completion order in parallel waves

## Reference routing

| File | Read when |
|---|---|
| `references/tool-reference.md` | Need exact parameter types, constraints, and response shapes for all 5 tools |
| `references/orchestration-patterns.md` | Planning multi-wave execution, dependency chains, or parallel dispatch |
| `references/pause-flow-handling.md` | Handling any of the 5 pause types with respond-task |
