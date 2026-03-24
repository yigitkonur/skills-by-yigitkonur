# How hcom Works — Full Technical Reference

hcom (hook-comms) is a Rust CLI that connects AI coding agents across terminals via a shared SQLite database and per-tool hooks. It supports Claude Code, Codex, Gemini CLI, and OpenCode.

## Core Loop

```
Agent A runs tool → hook fires (~20ms) → checks DB for pending messages →
  delivers messages in hook output → Agent A sees messages in next turn
```

Messages are stored in `~/.hcom/hcom.db` (SQLite, WAL mode). Hooks fire on every tool call. The Stop hook is the primary delivery point -- it blocks with exit code 2 and injects messages as the "reason" field that the agent sees as a system message.

## Agent Identity System (3-Tier Binding)

Agent names are random 4-letter CVCV words (luna, nemo, bali). Identity is resolved through three tiers:

**Tier 1: Explicit `--name` flag**
- Direct lookup by name or 7-char hex agent_id
- Validation: lowercase `[a-z0-9_]+` or UUID or agent_id

**Tier 2: Process binding (`HCOM_PROCESS_ID`)**
- Every launched instance gets a unique UUID process ID
- Stored in `process_bindings` table: process_id -> instance_name
- Used by Codex agents that bind on first hcom command

**Tier 3: Session binding (`session_id`)**
- Claude: bound at SessionStart hook
- Codex: bound on codex-notify event
- Gemini: bound at BeforeAgent hook
- OpenCode: bound via plugin ceremony (TCP notify)

**Tags and display names:**
- `--tag worker` gives display name `worker-luna`
- `@worker-` routes to ALL agents with tag "worker"
- Name resolution: `tag-name` splits at hyphen, `luna:BOXE` splits at colon (remote)

## Message Scope and Routing

**Scope computation (messages.rs):**

1. **Broadcast** -- no @mentions in text or explicit_targets empty
   - `scope="broadcast"` in JSON
   - Delivered to all active/listening/recently-stopped agents

2. **Mentions** -- @mentions present
   - `scope="mentions"` with `mentions=["luna","nova"]` array
   - Only mentioned agents receive
   - @mention extraction: `MENTION_PATTERN` regex rejects emails, paths, underscore-prefixed
   - Valid: `@luna`, `@luna:BOXE` (remote), `@team-luna` (tag-name)
   - `@tag-` prefix matches all agents with that tag
   - Strict validation: unmatched mentions produce errors

**Delivery filter (should_deliver_to):**
- Skip own messages (sender == receiver)
- Broadcast -> deliver to everyone
- Mentions -> deliver only if receiver is in mentions array
- Cross-device: `receiver.split(':')[0]` matches `mention.split(':')[0]`

**Intent system:**
- `--intent request` -- sender expects a response (triggers auto-watch if recipient stops without replying)
- `--intent inform` -- FYI, no response needed
- `--intent ack` -- acknowledgment, no response needed

## Message Delivery Pipeline (5 Stages)

### Stage 1: Send Command
```bash
hcom send @luna @nova --thread review-1 --intent request -- "please review"
```
- Compute scope via `messages.rs::compute_scope()`
- Validate mentions against active/recent instances
- Create JSON payload with scope, mentions, intent, thread, etc.

### Stage 2: Event Logging
```json
{
  "from": "sender_name",
  "text": "please review",
  "scope": "mentions",
  "mentions": ["luna", "nova"],
  "intent": "request",
  "thread": "review-1",
  "delivered_to": ["luna", "nova"],
  "sender_kind": "instance"
}
```
Inserted into `events` table. Every INSERT triggers FTS5 index update and subscription checks.

### Stage 3: Hook Delivery (Claude, Gemini)
- On next hook fire (PreToolUse, PostToolUse, or Stop poll)
- `get_unread_messages(instance)` filtered by `should_deliver_to()`
- Max 50 messages per delivery (constant `MAX_MESSAGES_PER_DELIVERY`)
- Messages formatted as JSON in `hookSpecificOutput.additionalContext`
- Instance `last_event_id` cursor advanced after delivery
- Stop hook: blocks with exit code 2, messages in reason field

### Stage 4: PTY Injection (Codex, adhoc)
PTY delivery thread checks gate conditions before injecting text:

| Gate | What it checks | Why |
|------|----------------|-----|
| require_idle | status=="listening" | No injection during active processing |
| block_on_approval | No OSC9 approval prompt | Agent cannot respond while waiting for user |
| block_on_user_activity | No keystrokes for 500ms-3s | Prevents corruption of user input |
| require_ready_prompt | "? for shortcuts" visible | Tool is ready to accept input |
| require_prompt_empty | No user text in input box | Prevents overwriting user's typed text |

Tool-specific configs:
- Claude: disables ready_prompt check (unreliable in accept-edits mode)
- Gemini: requires ready_prompt (always visible)
- Codex: disables approval check when active

### Stage 5: Delivery Verification
- Monitor terminal for output change after injection
- 3 failed attempts -> mark status="blocked", reason="output_unstable"
- TCP notification wakes delivery thread instantly (no polling)

## Per-Tool Delivery Mechanisms

| Tool | Mechanism | Latency | How it works |
|------|-----------|---------|--------------|
| Claude | Hook output (JSON additionalContext) | under 1s | Stop hook blocks, delivers messages as reason |
| Codex | PTY text injection | 1-3s | codex-notify triggers delivery, text injected into terminal |
| Gemini | Hook output (same as Claude) | under 1s | AfterAgent hook delivers messages |
| OpenCode | Plugin TCP endpoint | under 1s | TypeScript plugin calls handle_read() |

## Bootstrap Injection

On first hook fire (SessionStart for Claude, BeforeAgent for Gemini, opencode-start for OpenCode), each agent receives a system context wrapped in `<hcom_system_context>` XML. The bootstrap contains:

**Universal section (~600 tokens):**
- Instance name, display name, authority rules ("Prioritize @bigboss over others")
- Binding marker requirement: `[hcom:instance_name]` in first response
- Response rules: request -> always respond, inform -> only if useful, ack -> don't respond
- Full command reference: send, list, transcript, events, bundle, spawn, resume, fork, kill, run, term, config
- Active instances snapshot (up to 8, grouped by tool)
- Available scripts list

**Conditional sections:**
- TAG_NOTICE: if tagged, explains `@tag-` group messaging
- RELAY_NOTICE: if relay enabled, explains remote suffixes `luna:BOXE`
- HEADLESS_NOTICE: if background, explains all communication via hcom send
- UVX_CMD_NOTICE: if using alternate command (uvx, poetry run, etc.)

**Tool-specific delivery rules:**
- Claude/Gemini(launched)/OpenCode: "Messages auto-arrive via <hcom> tags, end your turn to receive"
- Codex(launched): "<hcom> tags trigger `hcom listen 1` command"
- Adhoc/non-launched: "Messages do NOT arrive automatically, use CONNECTED MODE"

**Claude-only SUBAGENTS section:**
- Explains how to spawn subagents via Task with background=true
- Subagents get own hcom context and random name
- Parent-child relationship tracked via parent_session_id

**Subagent bootstrap (simpler):**
- Parent relationship, announcement instruction
- Delivery rules, abbreviated command reference
- No subagent spawning capability (prevents infinite recursion)

## Event System

All activity is logged as events in the `events` table (type: message, status, life, bundle):

```sql
-- The events_v view flattens JSON for easy querying
SELECT * FROM events_v WHERE msg_from='luna' AND msg_thread='review-1'
```

**Subscriptions (reactive event watching):**
```bash
hcom events sub --idle worker-luna           # Notify when worker goes idle
hcom events sub --file "*.py" --once         # One-shot: next .py file edit
hcom events sub --collision                  # Two agents edit same file within 30s
```

- Stored in KV table as SQL filters with SHA256-based idempotent IDs
- Every `log_event()` call checks all subscriptions synchronously
- Match triggers system message from `[hcom-events]` to subscriber
- `--once` subscriptions auto-delete after first match

**FTS5 full-text search:**
- Indexes: message text, sender, instance, status context, detail, life action
- Used by TUI search and transcript search

## Instance Lifecycle State Machine

```
launching (status_context="new", age < 30s)
  |
  v
listening (idle, ready for messages)
  |       |
  v       v
active    blocked (approval prompt, OSC9)
  |
  v
listening (hook sets when done with turn)
  |
  v (heartbeat timeout: 35s TCP, 10s no-TCP; or 5min activity timeout)
inactive (cleaned up)
```

**Heartbeat thresholds:**
- With TCP notify: 35 seconds
- Without TCP notify: 10 seconds
- Activity timeout: 5 minutes (any status)
- Launch timeout: 30 seconds (launching -> inactive if no session binding)
- Wake grace: 60 seconds after system sleep detected (wall-clock vs monotonic drift)

**Status icons in TUI:** active (green dot), listening (blue circle), blocked (yellow lock), launching (spinner), inactive (gray dash)

## Cross-Device Relay

MQTT pub/sub via public brokers (TLS). Three default brokers tried in order:
1. `broker.emqx.io:8883`
2. `broker.hivemq.com:8883`
3. `test.mosquitto.org:8886`

**Setup:**
```bash
hcom relay new                    # Machine A: generates join token (~24 chars)
hcom relay connect <token>        # Machine B: joins group
hcom send @luna:BOXE -- "hello"   # Cross-device message
```

**Sync mechanism:**
- Push cycle: every 5 seconds (or instant via TCP notify)
- Topic per device: `{relay_id}/{device_uuid}` (retained state)
- Control topic: `{relay_id}/control` (non-retained stop/kill commands)
- Device short IDs: 4-char CVCV words (BOXE, VUNO) via FNV-1a hash

**Remote instances:**
- Appear with suffix: `luna:BOXE`
- Status synced, age always 0 (trust remote)
- LWT (Last Will & Testament): empty payload on disconnect triggers cleanup

## Hook Performance (~20ms per invocation)

| Stage | Typical Time |
|-------|-------------|
| init (dirs + DB open) | 0.5-1ms |
| session resolve | 0.2-0.5ms |
| instance lookup | 1-3ms |
| vanilla binding | 1-2ms |
| handler logic | 2-5ms |
| **total** | **5-15ms** |

Optimizations:
- Pre-gate: skip entirely if no hcom instances exist
- Lazy transcript search: only if no session binding found
- TCP notification: poll-based wake instead of busy loop
- Panic guard: all handlers wrapped to catch panics, return fallback
