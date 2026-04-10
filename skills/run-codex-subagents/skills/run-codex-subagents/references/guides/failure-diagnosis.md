# Failure Diagnosis: Reading Timelines and Events to Understand Why

When a task fails, the answer is always in the timeline and events files. This guide teaches you to read them like a flight recorder.

## Exit Code Interpretation

| Code | Signal  | Meaning                                        |
|------|---------|------------------------------------------------|
| 0    | null    | Clean shutdown. NOT a crash. Process decided to exit. |
| 1    | null    | Error exit. Check STDERR in events.jsonl.       |
| null | SIGKILL | OOM kill. Process exceeded memory limit.         |
| null | SIGTERM | Graceful termination. Timeout or external kill.  |
| 137  | null    | SIGKILL via exit code (128 + 9). Same as OOM.   |
| 143  | null    | SIGTERM via exit code (128 + 15). Timeout.       |

The most common exit is `code=0, signal=null`. This is confusing because it looks like success. It means the process shut down cleanly — but "cleanly" includes "decided to stop because thinking budget was exhausted" or "received a shutdown signal and exited gracefully."

## STDERR Analysis

Extract STDERR from events.jsonl:

```bash
# Get all stderr output
jq -r 'select(.type == "stderr") | .content' /path/events.jsonl
```

### Common STDERR patterns

**Auth token expired:**
```
Error: authentication token has expired. Please re-authenticate.
```
Fix: Refresh the auth token before spawning. Tokens expire every ~2 hours.

**Rate limited:**
```
Error: rate limit exceeded. Retry after 30 seconds.
```
Fix: Wait, then re-spawn. Or reduce parallel task count.

**request_user_input unavailable:**
```
Error: request_user_input tool is not available in this context
```
This means the agent tried to ask a question but the MCP bridge couldn't handle it. Usually happens when the auto-answer mechanism fails.

**Model overloaded:**
```
Error: model is currently overloaded. Please try again later.
```
Fix: Wait 2-5 minutes, re-spawn.

## Timeline Pattern Recognition

### Pattern 1: STARTED → EXIT (Immediate Death)

```
17:05:20.100 STARTED reasoning=low
17:05:20.846 EXIT code=1 signal=null
```

The agent never executed a single command. Causes:
- Auth failure (check STDERR)
- Invalid configuration
- Process-level crash before agent initialization

**Diagnosis steps:**
```bash
jq -r 'select(.type == "stderr") | .content' events.jsonl
jq -r 'select(.type == "exit")' events.jsonl
```

### Pattern 2: STARTED → THINK → EXIT (Reasoning Budget Exhausted)

```
17:05:20.100 STARTED reasoning=high
17:05:35.200 THINK "I need to analyze the architecture..."
17:05:55.300 THINK "Considering three approaches..."
17:06:15.400 THINK "The delegate pattern seems best..."
17:06:25.846 EXIT code=0 signal=null
```

Agent spent all its tokens thinking and never acted. Causes:
- Reasoning level too high for the task
- Prompt too open-ended (agent can't converge on an approach)

**Fix:** Re-spawn at `low` reasoning with a more prescriptive prompt.

### Pattern 3: STARTED → CMD → THINK → EXIT (Mid-Execution Death)

```
17:05:20.100 STARTED reasoning=low
17:05:22.200 CMD read ContentView.swift
17:05:24.300 THINK "I see the music hover section..."
17:05:26.400 WRITE MusicHoverController.swift
17:05:28.500 CMD edit ContentView.swift
17:05:30.846 EXIT code=0 signal=null
```

Agent was actively working when the process died. Causes:
- Shared-process death (another task killed it)
- Token budget genuinely exhausted after productive work
- Auth token expired mid-session

**Diagnosis:** Check if other tasks exited at the exact same timestamp. If yes → shared-process death. If no → check token usage or auth.

**Recovery:** Partial work is very likely on disk. Follow partial-work-recovery.md.

### Pattern 4: STARTED → AUTO → THINK → EXIT (Auto-Answer Then Death)

```
17:05:20.100 STARTED reasoning=low
17:05:22.200 CMD read ContentView.swift
17:05:30.300 AUTO "Apply these changes? → Yes (Recommended)"
17:05:31.400 THINK "Applying changes..."
17:05:34.846 EXIT code=0 signal=null
```

The AUTO event shows the agent asked a question and got an auto-answer. The death followed shortly after. Causes:
- The 4-second question timeout triggered a process exit
- The auto-answer sent the agent down a wrong path that caused an error
- Process shutdown was already in progress when auto-answer arrived

**Diagnosis:**
```bash
# Find the auto-answer event
jq 'select(.type == "auto_answer")' events.jsonl

# Check time between auto-answer and exit
jq -r 'select(.type == "auto_answer" or .type == "exit") | 
  "\(.timestamp) \(.type)"' events.jsonl
```

If the gap between AUTO and EXIT is exactly 4 seconds, it's the question timeout.

### Pattern 5: STARTED → CMD → CMD → CMD → EXIT (Productive Then Done)

```
17:05:20.100 STARTED reasoning=low
17:05:22.200 CMD read BluetoothPopupController.swift
17:05:24.300 CMD read ContentView.swift
17:05:28.400 WRITE MusicHoverController.swift
17:05:32.500 CMD edit ContentView.swift
17:05:36.600 CMD edit project.pbxproj
17:05:38.700 CMD xcodebuild build
17:05:55.846 EXIT code=0 signal=null
```

This is likely a SUCCESSFUL completion, not a failure. The agent read, wrote, verified, and exited. Check the task result — it may have returned successfully.

## jq Commands for Diagnosis

```bash
# Full timeline reconstruction
jq -r '"\(.timestamp) \(.type) \(.content // .command // "")"' events.jsonl

# Just commands executed
jq -r 'select(.type == "command") | "\(.timestamp) \(.command)"' events.jsonl

# Files written
jq -r 'select(.type == "write") | .path' events.jsonl

# Exit details
jq 'select(.type == "exit")' events.jsonl

# Time between start and exit
jq -r 'select(.type == "start" or .type == "exit") | "\(.timestamp) \(.type)"' events.jsonl

# All errors
jq -r 'select(.type == "stderr" or .type == "error") | .content' events.jsonl

# Auto-answer decisions
jq 'select(.type == "auto_answer")' events.jsonl
```

## Shared-Process Death Diagnosis

When you suspect shared-process death:

```bash
# Compare exit timestamps across tasks
for dir in /path/sessions/task-*/; do
  task=$(basename "$dir")
  ts=$(jq -r 'select(.type == "exit") | .timestamp' "$dir/events.jsonl")
  echo "$task: $ts"
done
```

If two or more tasks show the exact same exit timestamp (within 100ms), it's shared-process death. All tasks died because one task caused the process to exit.

## The 80/20 Rule

80% of failures come from four causes. Check these first:

1. **Reasoning level too high** — fix: use `low`
2. **Shared-process death** — fix: recover partial work
3. **Auth token expiration** — fix: refresh before long waves
4. **Prompt too vague** — fix: preempt questions in the brief
