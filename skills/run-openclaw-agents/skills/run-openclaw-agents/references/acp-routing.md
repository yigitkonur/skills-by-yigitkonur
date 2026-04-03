# ACP Routing

Guide to discovering, selecting, and coordinating with ACP (Advanced Control Protocol) agents in OpenClaw. Based on verified documentation from docs.openclaw.ai/tools/acp-agents.

## CRITICAL: ACP sandbox limitation

**ACP runs on the HOST, not inside the sandbox.** Sandboxed sessions CANNOT spawn ACP sessions. If your current session is sandboxed, you must use `runtime="subagent"` instead of `runtime="acp"`. Attempting to use `sandbox="require"` with `runtime="acp"` is unsupported and will fail.

This is the single most common ACP error. Always check your session's sandbox status before attempting ACP routing.

## What are ACP agents

ACP agents are specialized coordination agents within the OpenClaw ecosystem. They handle domain-specific orchestration tasks that would be complex or error-prone to build from scratch. Think of them as pre-built orchestration modules for common multi-agent patterns.

ACP agents differ from regular agents in that they:
- Are purpose-built for specific coordination patterns
- Have their own internal state management and tool access
- Can coordinate multiple sub-agents internally
- Expose a higher-level interface to the calling agent
- Run on the host via the ACP backend (not in sandbox)

## sessions_spawn for ACP -- verified schema

When spawning an ACP session, `sessions_spawn` accepts the following parameters:

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `task` | string | YES | -- | Initial prompt / task description for the agent |
| `runtime` | string | YES (for ACP) | `"subagent"` | Must be `"acp"` for ACP routing. Defaults to `"subagent"` if omitted |
| `agentId` | string | No | falls back to `acp.defaultAgent` | Target harness identifier (e.g. `"codex"`, `"claude"`, `"gemini"`) |
| `thread` | boolean | No | `false` | Request thread-binding for the session |
| `mode` | `"run"` or `"session"` | No | `"run"` | `"session"` keeps the agent alive for multi-turn interaction; requires `thread: true` |
| `cwd` | string | No | -- | Absolute working directory path, validated by the backend |
| `label` | string | No | -- | Operator-facing label for the session |
| `resumeSessionId` | string (UUID) | No | -- | Resume an existing ACP session by ID |
| `streamTo` | `"parent"` | No | -- | Streams progress back to the parent session as system events |

**Key distinction:** For ACP, `runtime: "acp"` is required. Without it, the spawn defaults to a local subagent, not an ACP agent.

**Example -- spawn an ACP session:**
```
sessions_spawn runtime="acp" agentId="codex" task="Refactor the auth module to use JWT" cwd="/home/user/project" label="auth-refactor"
```

**Example -- resume an existing ACP session:**
```
sessions_spawn runtime="acp" resumeSessionId="550e8400-e29b-41d4-a716-446655440000" task="Continue with the tests"
```

**Example -- multi-turn session with thread binding:**
```
sessions_spawn runtime="acp" agentId="claude" task="Design the API schema" thread=true mode="session"
```

## ACP configuration in openclaw.json

The ACP subsystem is configured in the `acp` section of `openclaw.json`:

### Core ACP config

| Key | Type | Required | Default | Description |
|---|---|---|---|---|
| `acp.enabled` | boolean | YES | -- | Master switch for ACP functionality |
| `acp.backend` | string | YES | -- | Backend identifier (e.g. `"acpx"`) |
| `acp.dispatch.enabled` | boolean | No | `true` | Enable ACP dispatch |
| `acp.defaultAgent` | string | No | -- | Fallback harness when `agentId` is omitted from spawn |
| `acp.allowedAgents` | array | No | -- | Whitelist of allowed agent harnesses, e.g. `["pi","claude","codex","opencode","gemini","kimi"]` |
| `acp.maxConcurrentSessions` | integer | No | `8` | Maximum number of concurrent ACP sessions |
| `acp.stream.coalesceIdleMs` | integer | No | `300` | Idle milliseconds before coalescing stream chunks |
| `acp.stream.maxChunkChars` | integer | No | `1200` | Maximum characters per stream chunk |
| `acp.runtime.ttlMinutes` | integer | No | `120` | Time-to-live for ACP sessions in minutes |

### ACPX plugin config

The `acpx` backend is configured as a plugin:

| Key | Type | Default | Description |
|---|---|---|---|
| `plugins.entries.acpx.enabled` | boolean | -- | Enable the ACPX plugin |
| `plugins.entries.acpx.config.command` | string | -- | Command to invoke the ACPX backend |
| `plugins.entries.acpx.config.expectedVersion` | string | -- | Expected version string, or `"any"` to skip version check |
| `plugins.entries.acpx.config.permissionMode` | string | `"approve-reads"` | One of: `"approve-all"`, `"approve-reads"`, `"deny-all"` |
| `plugins.entries.acpx.config.nonInteractivePermissions` | string | `"fail"` | One of: `"fail"`, `"deny"`. What happens when a permission prompt is unavailable in non-interactive mode |

### Thread binding config

| Key | Description |
|---|---|
| `session.threadBindings.enabled` | Enable thread-binding for sessions |
| `session.threadBindings.idleHours` | Idle timeout for thread-bound sessions |
| Per-channel `threadBindings` config | Channel-specific thread binding settings |

## /acp slash commands

OpenClaw exposes these `/acp` commands for managing ACP sessions:

| Command | Purpose |
|---|---|
| `/acp spawn` | Spawn a new ACP session |
| `/acp cancel` | Cancel a running ACP session |
| `/acp steer` | Send steering instructions to a running session |
| `/acp close` | Close/terminate an ACP session |
| `/acp status` | Check status of ACP sessions |
| `/acp set-mode` | Switch between `run` and `session` modes |
| `/acp set` | Set ACP configuration values |
| `/acp cwd` | Set working directory for an ACP session |
| `/acp permissions` | Manage permission settings for an ACP session |
| `/acp timeout` | Set or adjust session timeout |
| `/acp reset-options` | Reset ACP options to defaults |
| `/acp sessions` | List all ACP sessions |
| `/acp doctor` | Diagnose ACP configuration issues |
| `/acp install` | Install or update ACP backend |

## ACP error conditions

| Error | Cause | Resolution |
|---|---|---|
| Sandboxed session cannot spawn ACP | ACP runs on host, not in sandbox | Use `runtime="subagent"` instead, or run from an unsandboxed session |
| `sandbox="require"` unsupported with `runtime="acp"` | Incompatible settings | Remove the sandbox requirement or switch runtime |
| Permission prompt unavailable in non-interactive mode | `nonInteractivePermissions` is set to `"fail"` | Set to `"deny"` to silently deny, or ensure interactive mode |
| Thread binding owned by another user | Thread already bound | Use a different thread or wait for the binding to expire |
| Thread bindings unavailable for channel | Channel does not support thread binding | Use a supported channel or disable thread binding |
| Agent not in allowedAgents list | `acp.allowedAgents` whitelist blocks the agent | Add the agent harness to the whitelist |

## When to route to ACP vs. build custom

| Situation | Approach |
|---|---|
| A purpose-built ACP agent exists for this coordination pattern | Route to ACP with `runtime="acp"` |
| The coordination pattern is novel or highly specific to your workflow | Build custom using sub-agent patterns with `runtime="subagent"` |
| An ACP agent handles 80% of the need but misses edge cases | Use ACP and handle edge cases in the parent session |
| Multiple ACP agents need to work together | Orchestrate them as sub-agents from a supervisor pattern |
| Session is sandboxed | MUST use `runtime="subagent"` -- ACP is unavailable |

**Rule of thumb:** If you find yourself implementing multi-step coordination logic that reads like "spawn agent A, pass result to agent B, check condition, then spawn agent C" -- check if an ACP agent already handles that sequence. But if you are in a sandboxed session, you cannot use ACP.

## Discovering ACP agents

Use `agents_list` to see all available agents, including ACP agents:

```
agents_list
```

ACP agents are identified by their agent type or naming convention in the listing. The `acp.allowedAgents` config controls which harnesses are available.

**Selection criteria:**
- Match the ACP agent's described purpose to your coordination need
- Prefer an ACP agent over building custom coordination when one exists
- If multiple ACP agents could handle the task, choose the more specialized one
- Verify the target agent is in the `acp.allowedAgents` whitelist

## ACP coordination patterns

### Single ACP delegation

The simplest use: delegate an entire coordination workflow to an ACP agent.

1. Verify you are NOT in a sandboxed session
2. Find the matching ACP agent via `agents_list`
3. Spawn with `runtime="acp"`, clear task, and optionally `streamTo="parent"` for progress
4. Yield for the result
5. Process the high-level outcome

### Multi-turn ACP session

For interactive coordination requiring multiple exchanges:

1. Spawn with `mode="session"` and `thread=true`
2. Send follow-up instructions via `/acp steer`
3. Monitor with `/acp status`
4. Close with `/acp close` when done

### ACP as a stage in a pipeline

Use an ACP agent as one stage in a larger pipeline:

1. Earlier stages produce intermediate results
2. Spawn the ACP agent with those results as input in the `task` parameter
3. Yield for the ACP agent's coordination outcome
4. Use the outcome in subsequent stages

### Multiple ACP agents

When the workflow spans multiple coordination domains:

1. Verify `acp.maxConcurrentSessions` allows the needed parallelism (default: 8)
2. Identify which ACP agents cover which parts of the workflow
3. Determine dependencies between them (sequential or parallel)
4. Orchestrate them as sub-agents using fan-out or pipeline patterns
5. Aggregate their results

**Caution:** Multiple ACP agents may spawn their own sub-agents, creating nested orchestration. Monitor resource usage and session counts against the `acp.maxConcurrentSessions` limit.

## Monitoring ACP agents

Because ACP agents may run complex internal workflows:

- Use `session_status` or `/acp status` for quick health checks
- Use `sessions_history` to understand what the ACP agent is doing internally
- Use `streamTo="parent"` at spawn time to get real-time progress events
- Sessions have a TTL of `acp.runtime.ttlMinutes` (default 120 minutes) -- plan accordingly
- If an ACP agent appears stuck, inspect its history before stopping it -- it may be waiting for its own sub-agents
- Use `/acp doctor` to diagnose configuration issues

## ACP agent pitfalls

| Pitfall | Prevention |
|---|---|
| Spawning ACP from a sandboxed session | Check sandbox status first; use `runtime="subagent"` if sandboxed |
| Forgetting `runtime="acp"` in spawn | Without it, defaults to local subagent. Always set explicitly |
| Bypassing an existing ACP agent to build custom coordination | Check `agents_list` and `acp.allowedAgents` first |
| Treating ACP agents as simple sub-agents | Account for their internal complexity in timeout and monitoring |
| Not providing enough context in the task description | ACP agents need clear goals, inputs, expected outputs, and constraints |
| Nesting too many ACP agents | Keep nesting depth shallow (max 2-3 levels); deep nesting is hard to debug |
| Ignoring ACP agent internal failures | Inspect `sessions_history` even when the top-level result looks successful |
| Exceeding maxConcurrentSessions | Check current session count before spawning; default limit is 8 |
| Using `mode="session"` without `thread=true` | Session mode requires thread binding; spawn will fail without it |
