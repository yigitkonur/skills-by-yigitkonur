---
name: run-openclaw-agents
description: Use skill if you are orchestrating OpenClaw multi-agent systems — spawning sub-agents, managing sessions, ACP routing, and cross-agent messaging.
---

# Orchestrate OpenClaw

Coordinate multi-agent work at runtime: spawn sub-agents, manage sessions, route messages between agents, and enforce safety constraints across the OpenClaw agent ecosystem.

## Trigger boundary

### Use this skill when

- Spawning sub-agents with `sessions_spawn` for parallel or delegated work
- Managing active sessions: listing, inspecting history, checking status, sending inter-session messages
- Routing work to ACP (Advanced Control Protocol) agents for specialized coordination
- Sending cross-platform messages via `message` (Discord, Slack, Telegram)
- Designing multi-agent pipelines: fan-out, fan-in, supervisor, chain-of-responsibility
- Choosing tool profiles to constrain what sub-agents can access
- Using `nodes` for cross-device hardware interaction (screenshots, GPS, camera)
- Waiting on sub-agent results with `sessions_yield` or polling `subagents`

### Do not use this skill when

- Setting up OpenClaw configuration, plugins, or initial environment (use OpenClaw setup skills)
- Building a new OpenClaw plugin (use `build-openclaw-plugin`)
- Building a new OpenClaw skill (use `build-openclaw-skill`)
- Doing browser automation without multi-agent coordination (use `run-agent-browser`)
- Planning work decomposition without runtime orchestration (use `plan-work` or `plan-issue-tree`)

## Non-negotiable rules

1. **Confirm risk level before every HIGH or VERY HIGH risk tool call.** `sessions_spawn`, `sessions_send`, `message`, and `nodes` can have irreversible side effects. State the action and its consequences before executing.
2. **Use the narrowest tool profile that satisfies the sub-agent's task.** Never spawn a sub-agent with full tool access when a restricted profile suffices.
3. **Always yield or poll sub-agents to completion.** Abandoned sub-agents waste resources and may leave work in an inconsistent state.
4. **Verify session existence before sending messages.** Use `sessions_list` or `session_status` before `sessions_send`.
5. **Never send cross-platform messages without explicit user confirmation.** The `message` tool reaches real humans on real platforms.
6. **Scope hardware access narrowly.** The `nodes` tool controls physical devices. Request only the specific capability needed (screenshot, GPS, camera) and confirm with the user.
7. **Prefer session reuse over session creation.** Check `sessions_list` for existing sessions that match the needed context before spawning new ones.

## Decision tree

Use this tree to route to the correct pattern. At each node, pick the branch that matches your situation.

```
START: What is the orchestration need?
|
+-- Spawn or delegate work to another agent?
|   |
|   +-- Single task, wait for result --> Simple spawn pattern
|   |   Read: references/sub-agent-patterns.md (Simple delegation)
|   |
|   +-- Multiple parallel tasks --> Fan-out pattern
|   |   Read: references/sub-agent-patterns.md (Fan-out)
|   |
|   +-- Chain of tasks, output feeds next --> Pipeline pattern
|   |   Read: references/sub-agent-patterns.md (Pipeline)
|   |
|   +-- Need specialized ACP agent --> ACP routing
|       Read: references/acp-routing.md
|
+-- Manage existing sessions?
|   |
|   +-- List or inspect sessions --> Session inspection
|   |   Read: references/session-management.md (Inspection)
|   |
|   +-- Send data between sessions --> Inter-session messaging
|   |   Read: references/session-management.md (Inter-session)
|   |
|   +-- Check or wait for sub-agent results --> Yield and poll
|   |   Read: references/session-management.md (Yield patterns)
|   |
|   +-- Stop or clean up sessions --> Session lifecycle
|       Read: references/session-management.md (Cleanup)
|
+-- Send messages to external platforms?
|   |
|   +-- Discord, Slack, Telegram, etc. --> Cross-platform messaging
|   |   Read: references/messaging-patterns.md
|   |
|   +-- Between OpenClaw agents only --> Inter-session messaging
|       Read: references/session-management.md (Inter-session)
|
+-- Access hardware on remote nodes?
|   |
|   +-- Screenshots, GPS, camera --> Node hardware access
|       Read: references/risk-and-security.md (Nodes)
|
+-- Design a multi-agent architecture?
    |
    +-- Supervisor that delegates and aggregates --> Supervisor pattern
    |   Read: references/sub-agent-patterns.md (Supervisor)
    |
    +-- Agents with different tool profiles --> Profile-constrained agents
    |   Read: references/sub-agent-patterns.md (Tool profiles)
    |
    +-- Need risk assessment for the pipeline --> Risk review
        Read: references/risk-and-security.md
```

## Workflow

### 1) Assess the orchestration need

Before calling any orchestration tool:

1. Identify what needs to happen (spawn, message, inspect, coordinate)
2. Classify each tool call by risk level (see Risk classification table below)
3. For HIGH and VERY HIGH risk calls, state the action and get user confirmation

**Risk classification:**

| Tool | Risk | Why |
|---|---|---|
| `sessions_list` | LOW | Read-only listing |
| `sessions_history` | LOW | Read-only history |
| `session_status` | LOW | Read-only status check |
| `agents_list` | LOW | Read-only agent listing |
| `subagents` | LOW | Read-only sub-agent status |
| `sessions_yield` | LOW | Passive wait for results |
| `sessions_spawn` | HIGH | Creates new agent with tool access |
| `sessions_send` | HIGH | Sends data between sessions, can trigger actions |
| `message` | VERY HIGH | Sends messages to real humans on external platforms |
| `nodes` | VERY HIGH | Controls physical hardware across devices |

### 2) Choose the tool profile for sub-agents

When spawning sub-agents, select the narrowest profile:

| Profile | Tools available | Use when |
|---|---|---|
| `minimal` | Read-only tools, no file writes, no network | Information gathering, analysis, summarization |
| `coding` | File read/write, shell, git | Code generation, refactoring, testing |
| `messaging` | `message`, `sessions_send` | Communication tasks only |
| Full (no restriction) | All tools | Only when the task genuinely requires unrestricted access |

Rule: start with `minimal` and escalate only if the task cannot complete.

### 3) Execute the orchestration pattern

Follow the pattern identified in the decision tree. Each pattern is documented in detail in the corresponding reference file.

**Common execution sequence:**

1. `agents_list` -- discover available agents
2. `sessions_list` -- check for reusable sessions
3. `sessions_spawn` -- create sub-agent (if no reusable session)
4. `sessions_yield` or poll `subagents` -- wait for results
5. `sessions_history` -- inspect results
6. Clean up: stop sub-agents via `subagents`

### 4) Verify and clean up

After orchestration completes:

- Confirm all sub-agents returned results (check `subagents` status)
- Verify no sessions are left in a running state unless intentionally persistent
- For messaging: confirm delivery where possible
- Aggregate results if using fan-out or supervisor patterns

## Do this, not that

| Do this | Not that |
|---|---|
| Check `sessions_list` before spawning a new session | Spawn new sessions without checking for reusable ones |
| Use the narrowest tool profile for sub-agents | Give every sub-agent full tool access by default |
| Confirm with the user before `message` or `nodes` calls | Send external messages or access hardware without confirmation |
| Use `sessions_yield` to wait for sub-agent results | Fire-and-forget sub-agents without collecting results |
| State the risk level and consequences before HIGH/VERY HIGH calls | Execute high-risk calls silently |
| Poll `subagents` status when yield times out | Assume a sub-agent completed when it may have failed |
| Route to ACP agents for specialized coordination | Build custom coordination logic when an ACP agent already handles it |
| Clean up sub-agents after work completes | Leave orphaned sessions running |

## Recovery paths

- **Sub-agent is stuck or unresponsive:** Check status with `subagents`. If stuck, stop it and re-spawn with a clearer task description or different tool profile.
- **Session not found when sending messages:** Re-run `sessions_list` to verify the session ID. Sessions may have terminated between listing and sending.
- **External message delivery fails:** Check the platform and channel configuration. Verify the message target exists. Do not retry without user confirmation.
- **Fan-out results are inconsistent:** Use `sessions_history` to inspect each sub-agent's work. Identify the divergent agent and either re-run it or reconcile manually.
- **Tool profile is too restrictive:** The sub-agent will fail with permission errors. Inspect the error, escalate to the next profile level, and re-spawn.
- **Nodes hardware access fails:** Verify the target node is online and the specific capability (screenshot, GPS, camera) is available. Read `references/risk-and-security.md`.

## Steering anti-patterns

1. **Over-spawning.** Creating a sub-agent for every small task. If the work can be done in the current session in a few steps, do not spawn.
2. **Full-access default.** Giving sub-agents unrestricted tool profiles out of convenience. This creates unnecessary risk surface.
3. **Fire-and-forget messaging.** Sending `message` calls to external platforms without confirming the target, content, and timing with the user.
4. **Orphaned sessions.** Spawning sub-agents and never checking their status or cleaning them up.
5. **Polling without backoff.** Checking `subagents` status in a tight loop instead of using `sessions_yield` with a reasonable timeout.
6. **ACP bypass.** Building custom multi-step coordination when a purpose-built ACP agent already handles the pattern.

## Reference routing

Read the smallest set that covers your current need:

| Need | Reference |
|---|---|
| Spawning sub-agents, fan-out, pipelines, supervisor patterns, tool profiles | `references/sub-agent-patterns.md` |
| Session lifecycle: listing, history, inter-session messaging, yield, cleanup | `references/session-management.md` |
| ACP agent discovery, routing, and coordination patterns | `references/acp-routing.md` |
| Cross-platform messaging: Discord, Slack, Telegram, confirmation workflows | `references/messaging-patterns.md` |
| Risk levels, confirmation protocols, hardware access, security boundaries | `references/risk-and-security.md` |

### Minimal reading sets

**Spawn a sub-agent for a single task:**
- `references/sub-agent-patterns.md` (Simple delegation section)
- `references/risk-and-security.md` (Risk classification only)

**Fan-out parallel work:**
- `references/sub-agent-patterns.md` (Fan-out section)
- `references/session-management.md` (Yield patterns section)

**Send cross-platform messages:**
- `references/messaging-patterns.md`
- `references/risk-and-security.md`

**Design a multi-agent architecture:**
- `references/sub-agent-patterns.md` (all sections)
- `references/acp-routing.md`
- `references/session-management.md`
- `references/risk-and-security.md`
