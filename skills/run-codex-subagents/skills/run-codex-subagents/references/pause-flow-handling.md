# Request Handling: Approvals and Input

When a task blocks on a shell-command approval, file-write approval, or user-input question, it exits with code `2`. The `request` commands let you inspect and answer these without restarting the task.

## The Approval Flow

```
cli-codex-subagent run task.md --follow
   → exit 2 (blocked)

cli-codex-subagent request list
   → req_abc123  command_approval  tsk_xyz  "npm install express"

cli-codex-subagent request read req_abc123
   → type: command_approval
     command: "npm install express"
     task: tsk_xyz

cli-codex-subagent request answer req_abc123 --decision accept-session

cli-codex-subagent task follow tsk_xyz
   → resumes...
   → DONE completed
```

## Preventing Approvals Entirely

The best approach for autonomous runs: **skip approvals at spawn time**.

```bash
# Auto-approve everything (--auto-approve = --approval-policy never)
cli-codex-subagent run task.md --follow --auto-approve

# Fine-grained: only block if a command previously failed
cli-codex-subagent run task.md --follow --approval-policy on-failure

# Or in frontmatter:
# approval_policy: never
```

Approval policies:

| Policy | Behavior |
|--------|---------|
| `never` | Auto-approve all requests |
| `on-failure` | Auto-approve unless the command previously failed |
| `on-request` | Default — require explicit approval |
| `untrusted` | Strict — approve more request types explicitly |

---

## Request Types

### command_approval

Agent wants to run a shell command. Shown in the event stream as:
```
APPROVE cmd: npm install express @types/express
```

**Answer:**
```bash
cli-codex-subagent request answer req_abc123 --decision accept-session
# or: --decision accept-once   (approve just this command)
# or: --decision reject        (block the command)
```

### file_approval

Agent wants to write or modify files. Shown as:
```
APPROVE files: src/config.ts, package.json
```

**Answer:**
```bash
cli-codex-subagent request answer req_abc123 --decision accept-session
```

### user_input (question)

Agent asked a clarifying question with options. Shown as:
```
ASK   What color should I use? (1) Red  (2) Blue  (3) Green
```

**Answer by choice index (1-indexed):**
```bash
cli-codex-subagent request answer req_abc123 --choice 2
```

**Answer with free text:**
```bash
echo "Use blue, matching the brand guidelines" > /tmp/answer.txt
cli-codex-subagent request answer req_abc123 --text-file /tmp/answer.txt
```

**Custom payload (advanced):**
```bash
cli-codex-subagent request answer req_abc123 --json-file payload.json
```

### elicitation

The Codex runtime wants confirmation before a system-level action.

```bash
cli-codex-subagent request answer req_abc123 --decision accept-session
```

---

## Multiple Requests in Sequence

A task can block multiple times. After each `request answer`, follow the task again:

```bash
cli-codex-subagent run task.md --follow    # → exit 2

cli-codex-subagent request answer req_1 --decision accept-session
cli-codex-subagent task follow tsk_abc    # → exit 2 again

cli-codex-subagent request answer req_2 --choice 1
cli-codex-subagent task follow tsk_abc    # → DONE completed
```

---

## Diagnosing a Blocked Task

```bash
# 1. Find the task that blocked
cli-codex-subagent task list --status working

# 2. Find pending requests
cli-codex-subagent request list

# 3. Inspect what's needed
cli-codex-subagent request read req_abc123

# 4. Answer it
cli-codex-subagent request answer req_abc123 --decision accept-session

# 5. Resume
cli-codex-subagent task follow tsk_xyz
```

---

## Fixing Wrong Auto-Answers

With `--auto-approve`, the daemon auto-selects the first option for questions. If the wrong choice was made:
1. The task continues with the wrong answer
2. You see the AUTO event in `task follow` or `task events`
3. Steer with a corrective follow-up after the task completes:
   ```bash
   cli-codex-subagent task steer tsk_abc123 correction.md --follow
   ```
   Where `correction.md` says: "You used Red but I need Blue. Re-do the file with Blue."
4. Or: cancel the task and re-run with a better prompt that doesn't trigger the question.

---

## Events in the timeline

| Tag | Source |
|-----|--------|
| `AUTO` | Auto-answered question (auto-approve was on, or daemon auto-selected) |
| `APPROVE` | Auto-approved command or file approval |
| `ASK` | Request that requires manual `request answer` (exit code 2) |
