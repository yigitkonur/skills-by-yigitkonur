# Monitoring Patterns: Seeing What Agents Are Doing

Without monitoring, agent failures are invisible. You spawn a task, wait, and get back either a result or a cryptic error. Monitoring transforms this into a live stream of agent activity. It is non-optional for any serious Codex workflow.

## The Monitor Tool

The Monitor tool streams events as background notifications. You start it and continue working — events arrive asynchronously. This is fundamentally different from running `tail -f` in a blocking shell.

### Basic Pattern: One Task

After every `spawn-task`, immediately start monitoring:

```
spawn-task(prompt="...", reasoning="low")
→ returns task_id="abc-123"

Monitor(tail -f /path/to/sessions/abc-123/timeline.log)
```

You are now free to do other work. Each new line in the timeline arrives as a notification.

### Parallel Pattern: Multiple Tasks

For parallel dispatch, merge multiple tails with prefixes:

```
Monitor(
  tail -f /path/sessions/task-a/timeline.log | sed 's/^/[music] /' &
  tail -f /path/sessions/task-b/timeline.log | sed 's/^/[timer] /' &
  tail -f /path/sessions/task-c/timeline.log | sed 's/^/[gesture] /'
)
```

Output arrives interleaved with labels:
```
[music]   STARTED reasoning=low
[timer]   STARTED reasoning=low
[gesture] STARTED reasoning=low
[music]   THINK "Reading ContentView.swift to understand..."
[timer]   CMD read FastNotch/ContentView.swift
[music]   CMD create MusicHoverController.swift
[gesture] THINK "I need to understand the gesture handling..."
```

### Quick Check: Is It Still Alive?

When you just need to know the current state without streaming:

```bash
tail -1 /path/sessions/task-a/timeline.log
```

Returns the last event. If it's `EXIT`, the task is done or dead. If it's `CMD` or `THINK`, the task is still running.

## Timeline Event Types

| Event   | Meaning                              | Example                          |
|---------|--------------------------------------|----------------------------------|
| STARTED | Task process launched                | `STARTED reasoning=low`          |
| THINK   | Agent is reasoning (internal)        | `THINK "Analyzing the pattern"`  |
| CMD     | Agent executed a shell command        | `CMD read ContentView.swift`     |
| WRITE   | Agent wrote/modified a file          | `WRITE Controllers/Music.swift`  |
| AUTO    | Auto-answered a question             | `AUTO "Apply changes? → Yes"`    |
| EXIT    | Process terminated                   | `EXIT code=0 signal=null`        |

## What to Watch For

### Healthy Progress
```
STARTED → THINK → CMD(read) → THINK → CMD(read) → THINK → WRITE → CMD(read) → 
WRITE → CMD(build) → THINK → WRITE(fix) → CMD(build) → EXIT
```

Agent reads, thinks, writes, verifies, fixes, verifies again. This is the ideal flow.

### Stuck in Thinking
```
STARTED → THINK → THINK → THINK → THINK → THINK → EXIT
```

Agent spent its entire budget reasoning and never executed a command. Two possible causes:
1. Reasoning level too high (downgrade to `low`)
2. Prompt too vague (agent can't decide what to do)

### Immediate Death
```
STARTED → EXIT
```

Process-level failure. Check STDERR for auth errors, rate limits, or configuration issues.

### Approval Gate Death
```
STARTED → THINK → CMD → THINK → CMD → AUTO → THINK → EXIT
```

The `AUTO` event means the agent asked a question and got an auto-answer. If the auto-answer was wrong, the agent may have gone down a bad path. If the EXIT follows shortly after AUTO, the process may have died at the approval gate.

### Productive Death
```
STARTED → THINK → CMD → WRITE → CMD → WRITE → CMD → WRITE → EXIT
```

Agent created files, then died. High probability of recoverable partial work. Check git status immediately.

## The events.jsonl File

For deeper diagnosis, each task also writes an `events.jsonl` file with structured JSON:

```bash
# Last 5 events with full detail
tail -5 /path/sessions/task-a/events.jsonl | jq .
```

```json
{
  "type": "command",
  "timestamp": "2026-04-10T17:05:20.123Z",
  "command": "cat FastNotch/ContentView.swift",
  "exit_code": 0
}
{
  "type": "exit",
  "timestamp": "2026-04-10T17:05:25.846Z",
  "code": 0,
  "signal": null
}
```

The events.jsonl is the forensic record. The timeline.log is the live operational view.

## Monitoring Was Instrumental In

### Diagnosing auth token crash
Timeline showed STARTED → EXIT with no commands. events.jsonl STDERR showed `authentication token expired`. Led to discovery that tokens need refresh every 2 hours.

### Discovering shared-process death
Two task timelines showed EXIT at identical millisecond timestamp. This was impossible for independent processes — proved the shared-process model.

### Identifying 4-second question timeout
Timeline showed AUTO event followed by EXIT 4 seconds later. events.jsonl showed the auto-answer was sent but the process had already begun shutdown. Led to understanding that `request_user_input` has a 4-second timeout.

### Catching wrong auto-answers
Timeline showed AUTO → agent took wrong path → build failures → EXIT. The AUTO event revealed the agent was asked "Use delegate pattern or closure pattern?" and auto-selected "delegate" when the codebase used closures. Led to prompt improvement: put the correct choice first and mark it "(Recommended)".

## Monitor After Recovery

After recovering partial work and committing, if you need to spawn a follow-up task, monitor it with context:

```
Monitor(tail -f /path/sessions/followup-task/timeline.log | sed 's/^/[followup] /')
```

This lets you see if the follow-up is reading the right files and building on the recovered work correctly.

## Anti-Patterns

1. **Not monitoring at all** — You'll discover failures 5 minutes later when `wait-task` returns. By then you've lost context on what the agent was doing.

2. **Blocking on monitor output** — The Monitor tool is non-blocking. Don't wait for it to produce output before continuing your work.

3. **Monitoring only one task in a parallel batch** — If the process dies, you need timestamps from ALL tasks to diagnose shared-process death.

4. **Ignoring AUTO events** — Every AUTO event is a decision the agent made without your input. Review them to catch wrong paths early.

5. **Not checking events.jsonl after failures** — The timeline is a summary. The events file has the STDERR output, exact timestamps, and exit codes you need for real diagnosis.
