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
- Choosing the target agent or configured child tool policy for delegated work
- Using `nodes` for cross-device hardware interaction (screenshots, GPS, camera)
- Collecting child results via announce replies, `session_status`, `sessions_history`, or bounded `sessions_send` follow-ups

### Do not use this skill when

- Setting up OpenClaw configuration, plugins, or initial environment (use OpenClaw setup skills)
- Building a new OpenClaw plugin (use `build-openclaw-plugin`)
- Building a new OpenClaw skill (use `build-openclaw-skill`)
- Doing browser automation without multi-agent coordination (use `run-agent-browser`)
- Planning work decomposition without runtime orchestration (use `plan-issue-tree`)

## Non-negotiable rules

1. **Confirm risk level before every HIGH or VERY HIGH risk tool call.** `sessions_spawn`, `sessions_send`, `message`, and `nodes` can have irreversible side effects. State the action and its consequences, then wait for an explicit `YES` or equally direct approval.
2. **Use the narrowest effective child tool surface.** `sessions_spawn` does not take a per-call tool profile. Constrain delegated work by choosing the right target agent and by relying on the runtime's configured sub-agent tool policy.
3. **Always collect child results or status to completion.** `sessions_spawn` is non-blocking. Use announce replies, `session_status`, `sessions_history`, or bounded `sessions_send` follow-ups instead of assuming the child finished.
4. **Verify session existence before sending messages.** Use `sessions_list` or `session_status` before `sessions_send`.
5. **Never send cross-platform messages without explicit user confirmation.** The `message` tool reaches real humans on real platforms.
6. **Scope hardware access narrowly.** The `nodes` tool controls physical devices. Request only the specific capability needed (screenshot, GPS, camera) and confirm with the user.
7. **Prefer session reuse over session creation.** Check `sessions_list` for existing sessions that match the needed context before spawning new ones.

## Runtime assumptions and preflight

This skill requires the OpenClaw orchestration tool surface itself: `agents_list`, `sessions_list`, `sessions_history`, `sessions_send`, `sessions_spawn`, `session_status`, and any messaging/node tools you plan to use. `/subagents` controls are optional operator commands, not the core agent tool surface.

Before Step 1:

1. Inspect the current tool inventory and confirm those names are actually exposed.
2. If tool inventory is not visible, do a read-only smoke test with `agents_list` and `sessions_list`.
3. If any required tool is missing or blocked, stop immediately. This skill is not a generic subagent-playbook template.
4. If the runtime only exposes another orchestration system, use that system's native skill instead of translating OpenClaw commands by hand.
5. Do not use presence or absence of an `openclaw` CLI binary as the gate. This skill is about runtime tools, not local shell setup.

Use this confirmation template for HIGH and VERY HIGH risk calls:

```text
HIGH-RISK ACTION
Tool: sessions_spawn or sessions_send
What will happen: start or steer TARGET_SESSION_OR_AGENT for TASK
Why this is needed: REASON
Possible side effects: new agent execution, inherited tool access, persistent session state
Reply YES to proceed.
```

For `message` or `nodes`, include the exact target/capability and an irreversibility warning before waiting for explicit approval. Do not treat implied assent as approval.

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
|   +-- Check or wait for sub-agent results --> Completion and inspection
|   |   Read: references/session-management.md (Completion patterns)
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
    +-- Agents with different configured tool surfaces --> Profile-constrained agents
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
| `sessions_spawn` | HIGH | Creates new agent with tool access |
| `sessions_send` | HIGH | Sends data between sessions, can trigger actions |
| `message` | VERY HIGH | Sends messages to real humans on external platforms |
| `nodes` | VERY HIGH | Controls physical hardware across devices |

### 2) Choose the child tool surface

`sessions_spawn` does not accept a per-call `tool_profile`. A child's capabilities come from the target agent configuration plus the runtime's `tools.subagents.tools` policy.

When the runtime uses OpenClaw tool profiles, the base profiles are:

| Profile | Tools available | Use when |
|---|---|---|
| `minimal` | `session_status` only | Nearly tool-less children or sessions that will be built up explicitly in config |
| `coding` | File I/O, runtime, sessions, memory, image | Code generation, refactoring, testing, repo inspection |
| `messaging` | `message`, `sessions_list`, `sessions_history`, `sessions_send`, `session_status` | Communication and coordination tasks |
| Full (no restriction) | All tools | Only when the task genuinely requires unrestricted access |

Rules:

- Start with the narrowest configured option that can already do the job.
- `minimal` is not a generic read-only worker unless the runtime explicitly adds more tools to it.
- OpenClaw child runs are broad by default unless the runtime narrows them. Do not assume a spawned child is safe just because you did not ask for extra tools.
- If the available target agents do not expose the required tool surface safely, stop and say the runtime config must change.

### 3) Execute the orchestration pattern

Follow the pattern identified in the decision tree. Each pattern is documented in detail in the corresponding reference file.

**Common execution sequence:**

1. `agents_list` -- discover available agents
2. `sessions_list` -- check for reusable sessions
3. `sessions_spawn` -- create sub-agent (if no reusable session) and capture the returned `childSessionKey` / session identifier
4. Collect progress or results with announce replies, `session_status`, `sessions_history`, or `sessions_send ... timeoutSeconds=N`
5. Use `runTimeoutSeconds` on spawn when the child must finish within a bounded window
6. Decide whether to reuse, auto-archive, or delete the session

### 4) Verify and clean up

After orchestration completes:

- Confirm all delegated sessions returned results or an explicit terminal state
- Verify no sessions are left in a running state unless intentionally persistent
- For messaging: confirm delivery where possible
- Aggregate results if using fan-out or supervisor patterns

## Do this, not that

| Do this | Not that |
|---|---|
| Check `sessions_list` before spawning a new session | Spawn new sessions without checking for reusable ones |
| Constrain delegated work through target-agent choice and child tool policy | Assume `sessions_spawn` can set a per-call tool profile |
| Confirm with the user before `message` or `nodes` calls | Send external messages or access hardware without confirmation |
| Capture `childSessionKey` from `sessions_spawn` and inspect via status/history or announce replies | Fire-and-forget sub-agents without collecting results |
| State the risk level and consequences before HIGH/VERY HIGH calls | Execute high-risk calls silently |
| Back off between `session_status` or `sessions_list` checks | Poll in a tight loop or assume a child completed when it may have failed |
| Route to ACP agents for specialized coordination | Build custom coordination logic when an ACP agent already handles it |
| Use `cleanup: "delete"` for disposable runs or document why a session stays alive | Leave orphaned sessions running |

## Recovery paths

- **Sub-agent is stuck or unresponsive:** Check `session_status`, then inspect `sessions_history`. If operator controls are available, use `/subagents info` or `/subagents kill`; otherwise re-spawn only after you understand why the run stalled.
- **Session not found when sending messages:** Re-run `sessions_list` to verify the `sessionKey` / `sessionId`. Sessions may have terminated, been archived, or been deleted between listing and sending.
- **External message delivery fails:** Check the platform and channel configuration. Verify the message target exists. Do not retry without user confirmation.
- **Fan-out results are inconsistent:** Use `sessions_history` to inspect each sub-agent's work. Identify the divergent agent and either re-run it or reconcile manually.
- **Child tool surface is too restrictive:** Inspect the error, then choose a different target agent or broader sub-agent policy. Do not invent unsupported `sessions_spawn` parameters.
- **Nodes hardware access fails:** Verify the target node is online and the specific capability (screenshot, GPS, camera) is available. Read `references/risk-and-security.md`.

## Steering anti-patterns

1. **Over-spawning.** Creating a sub-agent for every small task. If the work can be done in the current session in a few steps, do not spawn.
2. **Blind child-surface assumptions.** Assuming spawned children are read-only or narrowly scoped when the runtime may actually allow broad non-session tools by default.
3. **Fire-and-forget messaging.** Sending `message` calls to external platforms without confirming the target, content, and timing with the user.
4. **Orphaned sessions.** Spawning sub-agents and never checking their status or cleaning them up.
5. **Polling without backoff.** Checking `session_status` or `sessions_list` in a tight loop instead of using reasonable intervals and bounded waits.
6. **ACP bypass.** Building custom multi-step coordination when a purpose-built ACP agent already handles the pattern.

## Reference routing

Read the smallest set that covers your current need:

| Need | Reference |
|---|---|
| Spawning sub-agents, fan-out, pipelines, supervisor patterns, tool profiles | `references/sub-agent-patterns.md` |
| Session lifecycle: listing, history, inter-session messaging, completion patterns, cleanup | `references/session-management.md` |
| ACP agent discovery, routing, and coordination patterns | `references/acp-routing.md` |
| Cross-platform messaging: Discord, Slack, Telegram, confirmation workflows | `references/messaging-patterns.md` |
| Risk levels, confirmation protocols, hardware access, security boundaries | `references/risk-and-security.md` |

### Minimal reading sets

**Spawn a sub-agent for a single task:**
- `references/sub-agent-patterns.md` (Simple delegation section)
- `references/risk-and-security.md` (Risk classification only)

**Fan-out parallel work:**
- `references/sub-agent-patterns.md` (Fan-out section)
- `references/session-management.md` (Completion patterns section)

**Send cross-platform messages:**
- `references/messaging-patterns.md`
- `references/risk-and-security.md`

**Design a multi-agent architecture:**
- `references/sub-agent-patterns.md` (all sections)
- `references/acp-routing.md`
- `references/session-management.md`
- `references/risk-and-security.md`
