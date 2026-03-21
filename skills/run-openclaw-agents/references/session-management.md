# Session Management

Comprehensive guide to managing OpenClaw sessions: listing, inspecting, inter-session communication, yielding for results, and cleanup.

## Core tools

| Tool | Group | Risk | Purpose |
|---|---|---|---|
| `sessions_list` | `group:sessions` | LOW | List all active sessions with IDs, agent types, and status |
| `sessions_history` | `group:sessions` | LOW | View message history for a specific session |
| `session_status` | `group:sessions` | LOW | Check the current status of a session (running, completed, failed, idle) |
| `sessions_send` | `group:sessions` | HIGH | Send a message or data payload to another session |
| `sessions_yield` | `group:sessions` | LOW | Block and wait for a sub-agent session to return its result |
| `subagents` | `group:sessions` | LOW | List sub-agent sessions with status; can also stop a sub-agent |

## Inspection patterns

### Listing active sessions

Always start with `sessions_list` to understand the current landscape before taking action.

```
sessions_list
```

Returns: session IDs, associated agent IDs, session status (running, idle, completed, failed), creation time, and tool profile.

**When to use:**
- Before spawning a new session (check for reusable ones)
- Before sending inter-session messages (verify target exists)
- After completing orchestration (verify cleanup is needed)
- When debugging why a sub-agent is not responding

### Viewing session history

```
sessions_history session_id=SESSION_ID
```

Returns: the full message exchange for the session, including tool calls and their results.

**When to use:**
- After a sub-agent completes, to inspect its work
- When a sub-agent's result via `sessions_yield` is unclear or incomplete
- To audit what a sub-agent actually did (especially for HIGH risk operations)
- When debugging unexpected behavior

### Checking session status

```
session_status session_id=SESSION_ID
```

Returns: current status (running, idle, completed, failed), last activity time, and error information if failed.

**When to use:**
- Quick health check without loading full history
- When `sessions_yield` times out and you need to understand why
- Before attempting to send data to a session

## Inter-session messaging

### Sending messages between sessions

```
sessions_send session_id=TARGET_SESSION_ID message="payload"
```

**Risk level: HIGH.** This sends data to another active session and can trigger actions in that session.

**Pre-send checklist:**
1. Verify the target session exists: `sessions_list` or `session_status`
2. Verify the target session is in a state that can receive messages (running or idle, not completed or failed)
3. Confirm the message content is correct and intended
4. For sensitive data, confirm with the user before sending

**Use cases:**
- Passing intermediate results from one sub-agent to another in a pipeline
- Sending updated context or instructions to a running sub-agent
- Coordinating between parallel sub-agents (e.g., signaling one to start after another reaches a checkpoint)

**Anti-patterns:**
- Sending messages to completed or failed sessions (they cannot process them)
- Using inter-session messaging when `sessions_yield` would be simpler
- Sending large payloads without considering message size limits

## Yield patterns

### Blocking wait for sub-agent results

```
sessions_yield session_id=SUB_AGENT_SESSION_ID
```

This blocks until the sub-agent session completes and returns its final result.

**When to use:**
- Simple delegation: spawn one sub-agent, wait for its result
- Pipeline: yield from one stage before starting the next
- Fan-in: yield from all parallel sub-agents before aggregating

**Timeout handling:**
If `sessions_yield` takes longer than expected:
1. Check `session_status` to see if the sub-agent is still running or has failed
2. Check `sessions_history` to see what the sub-agent is doing
3. If stuck, stop the sub-agent via `subagents` and re-spawn with a clearer task

### Polling as an alternative to yield

When you need non-blocking status checks:

```
subagents
```

Lists all sub-agents with their current status. Useful when:
- Managing multiple parallel sub-agents and you do not want to block on any one
- You need to check progress without waiting for completion
- Implementing a supervisor pattern that reacts to sub-agent status changes

**Polling discipline:**
- Check status at reasonable intervals, not in a tight loop
- Use `sessions_yield` when you genuinely need to wait for a single result
- When polling multiple sub-agents, process completed ones immediately rather than waiting for all

## Session cleanup

### Why cleanup matters

Orphaned sessions consume resources and may hold tool access that should be released. Every orchestration workflow should end with a cleanup phase.

### Cleanup sequence

1. `subagents` -- list all sub-agents and their status
2. For each completed sub-agent: verify results were collected (via yield or history)
3. For each still-running sub-agent: decide whether to wait or stop
4. Stop any sub-agents that are no longer needed: `subagents stop session_id=SESSION_ID`
5. Final `sessions_list` to confirm no orphaned sessions remain

### When to leave sessions running

Some sessions should persist:
- Long-running monitoring agents that observe system state
- Sessions with expensive setup (authenticated contexts, loaded data) that will be reused
- Explicitly user-requested persistent sessions

In these cases, document which sessions are intentionally persistent and why.

## Session reuse guidelines

Before spawning a new session, check if an existing one can be reused:

| Existing session state | Can reuse? | How |
|---|---|---|
| Idle, same tool profile, same agent type | Yes | `sessions_send` with new task |
| Completed, same agent type | No | Spawn new; completed sessions cannot receive new work |
| Running, different task | No | Wait for completion or spawn separate session |
| Failed | No | Inspect error via `sessions_history`, then spawn new |
| Different tool profile needed | No | Spawn new with correct profile |

Reuse reduces setup overhead and maintains context that may benefit the next task.
