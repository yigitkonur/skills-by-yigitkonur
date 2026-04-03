# Session Management

Comprehensive guide to managing OpenClaw sessions: listing, inspecting, inter-session communication, completion tracking, and cleanup.

## Core tools

| Tool | Group | Risk | Purpose |
|---|---|---|---|
| `sessions_list` | `group:sessions` | LOW | List all active sessions with IDs, agent types, and status |
| `sessions_history` | `group:sessions` | LOW | View message history for a specific session |
| `session_status` | `group:sessions` | LOW | Check the current status of a session (running, completed, failed, idle) |
| `sessions_send` | `group:sessions` | HIGH | Send a message or data payload to another session |
| `sessions_spawn` | `group:sessions` | HIGH | Start a child run and receive a `childSessionKey` for later inspection |

`/subagents` is an operator command family, not part of the core agent tool surface documented here. If the active channel exposes it, use it as an auxiliary control plane for inspect/kill/log actions.

## Inspection patterns

### Listing active sessions

Always start with `sessions_list` to understand the current landscape before taking action.

```
sessions_list
```

Returns: session keys, session IDs, associated agent IDs, session status, creation/update timestamps, and optional recent messages.

**When to use:**
- Before spawning a new session (check for reusable ones)
- Before sending inter-session messages (verify target exists)
- After completing orchestration (verify cleanup is needed)
- When debugging why a sub-agent is not responding

### Viewing session history

```
sessions_history sessionKey=SESSION_KEY
```

You may also pass a `sessionId` returned by `sessions_list`; OpenClaw resolves it back to the canonical `sessionKey`.

Returns: the full message exchange for the session, including tool calls and their results.

**When to use:**
- After a sub-agent completes, to inspect its work
- When an announce reply or bounded wait result is unclear or incomplete
- To inspect what a sub-agent actually did (especially for HIGH risk operations)
- When debugging unexpected behavior

### Checking session status

```
session_status sessionKey=SESSION_KEY
```

`session_status` also accepts a `sessionId`.

Returns: current status (running, idle, completed, failed), last activity time, and error information if failed.

**When to use:**
- Quick health check without loading full history
- When a child run appears stalled and you need to understand why
- Before attempting to send data to a session

## Inter-session messaging

### Sending messages between sessions

```
sessions_send sessionKey=TARGET_SESSION_KEY message="payload" timeoutSeconds=30
```

**Risk level: HIGH.** This sends data to another active session and can trigger actions in that session.

**Pre-send checklist:**
1. Verify the target session exists: `sessions_list` or `session_status`
2. Verify the target session is in a state that can receive messages (running or idle, not completed or failed)
3. Confirm the message content is correct and intended
4. Because `sessions_send` is HIGH risk, state the target session, payload purpose, and consequences, then wait for an explicit `YES` or equally direct approval before sending
5. If the payload contains sensitive data, call that out explicitly in the confirmation
6. Decide whether this is a bounded wait (`timeoutSeconds > 0`) or a fire-and-forget relay (`timeoutSeconds = 0`)

**Use cases:**
- Passing intermediate results from one sub-agent to another in a pipeline
- Sending updated context or instructions to a running sub-agent
- Coordinating between parallel sub-agents (e.g., signaling one to start after another reaches a checkpoint)

**Anti-patterns:**
- Sending messages to completed or failed sessions (they cannot process them)
- Sending to a session you have not revalidated recently
- Sending large payloads without considering message size limits

## Completion patterns

### Understand the spawn result first

`sessions_spawn` is always non-blocking. It returns `status: "accepted"` immediately together with a `runId` and `childSessionKey`.

Treat `childSessionKey` as the handle you will use for follow-up inspection:

- `session_status` for quick health checks
- `sessions_history` for transcript inspection
- `sessions_send` for follow-up turns in a running child session
- Runtime-generated announce replies for one-shot child completion summaries

Do not invent a `sessions_yield` step. The current session tools do not provide one.

### One-shot child runs

**When to use:**
- Simple delegation where the child should complete one task and report back
- Pipeline stages where the next stage depends on the child's output
- Fan-out branches that should converge after their announce replies arrive

Recommended control points:

1. Set `runTimeoutSeconds` on `sessions_spawn` if the child must finish within a bounded window
2. Wait for the announce reply in the requester session
3. If the announce is delayed or unclear, inspect `session_status` and `sessions_history`
4. If operator controls are available, `/subagents info` or `/subagents log` can help diagnose without guessing

### Interactive or persistent child sessions

Use this when the child stays alive for follow-up instructions:

1. Spawn with the appropriate session mode (`thread: true` and `mode: "session"` when supported and needed)
2. Capture the returned `childSessionKey`
3. Send follow-up turns with `sessions_send sessionKey=... timeoutSeconds=N`
4. If `sessions_send` returns `status: "timeout"`, the run is still active; inspect `sessions_history` later instead of assuming failure

### Polling discipline

When you need non-blocking status checks:

```
session_status sessionKey=SESSION_KEY
```

Useful when:
- Managing multiple parallel child sessions and you do not want to block on any one
- You need a quick health check before choosing a deeper inspection path
- Implementing a supervisor pattern that reacts to terminal states or repeated stalls

**Polling discipline:**
- Check status at reasonable intervals, not in a tight loop
- Use `sessions_history` when status alone is not enough
- When polling multiple child sessions, process completed ones immediately rather than waiting for all

## Session cleanup

### Why cleanup matters

Orphaned sessions consume resources and may hold tool access that should be released. Every orchestration workflow should end with a cleanup decision.

### Cleanup sequence

1. Decide up front whether the child is disposable (`cleanup: "delete"`) or reusable (`cleanup: "keep"`)
2. For each completed child session: verify results were collected via announce reply or history
3. For each still-running child session: decide whether to keep waiting, steer it with `sessions_send`, or terminate it through operator controls if available
4. Re-run `sessions_list` to confirm only intentional sessions remain
5. Document any intentionally persistent sessions so the next operator does not treat them as orphaned

**Defaults that matter:**

- `cleanup: "keep"` leaves the session in place for reuse or later inspection
- `cleanup: "delete"` archives immediately after announce
- Auto-archive is still best-effort and normally happens later even when you keep the session
- Stopping/killing a child is currently an operator-plane action (`/subagents kill`, `/stop`) when those controls are available

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
| Idle, same agent type, same intended scope | Yes | `sessions_send` with new task |
| Completed, same agent type | No | Spawn new; completed sessions cannot receive new work |
| Running, different task | No | Wait for completion or spawn separate session |
| Failed | No | Inspect error via `sessions_history`, then spawn new |
| Different tool surface or different target agent needed | No | Spawn new with the correct target/runtime constraints |

Reuse reduces setup overhead and maintains context that may benefit the next task.
