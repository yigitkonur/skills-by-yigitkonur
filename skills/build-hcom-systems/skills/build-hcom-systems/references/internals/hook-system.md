# hcom Hook System Internals — Complete Reference

Hooks are the integration layer between AI tools and hcom. Each hook invocation takes ~20ms (compiled Rust, no runtime).

## Hook Registration (HOOK_REGISTRY)

Defined in `hooks/utils.rs`. 10 hook types total for Claude:

| Hook | Event Name | Command Suffix | Timeout | Tool |
|------|-----------|----------------|---------|------|
| SessionStart | SessionStart | sessionstart | None | Claude |
| UserPromptSubmit | UserPromptSubmit | userpromptsubmit | None | Claude |
| PreToolUse | PreToolUse | pre | None | Claude |
| PostToolUse | PostToolUse | post | 86400s | Claude |
| Stop | Stop | poll | 86400s | Claude |
| PermissionRequest | PermissionRequest | permission-request | None | Claude |
| SubagentStart | SubagentStart | subagent-start | None | Claude |
| SubagentStop | SubagentStop | subagent-stop | 86400s | Claude |
| Notification | Notification | notify | None | Claude |
| SessionEnd | SessionEnd | sessionend | None | Claude |

Categories: Stdin (all), Blocking (Stop, SubagentStop)

---

## Per-Tool Hook Details

### Claude Code (10 hooks, 3162 LoC)

**File:** `/Users/yigitkonur/dev/hcom-repo/src/hooks/claude.rs`

**Payload delivery:** JSON via stdin
**Exit codes:** 0=allow, 2=block with message delivery

**Hook lifecycle:**

| Hook | What hcom does |
|------|----------------|
| SessionStart | Bootstrap injection (`inject_bootstrap_once()`), session binding, set status="listening" |
| UserPromptSubmit | Status tracking, update last_stop |
| PreToolUse | Set status="active", log tool context (e.g., "tool:Bash: git status") |
| PostToolUse | Deliver pending messages if any, update status |
| **Stop (poll)** | **Primary delivery point**: set "listening", poll for messages, block (exit 2) with messages in reason |
| PermissionRequest | Set status="blocked", log approval request |
| SubagentStart | Register subagent, create instance row, set parent_session_id |
| SubagentStop | Cleanup subagent, freeze-period message delivery |
| Notification | Forward to event stream, update metrics |
| SessionEnd | Cleanup: remove session binding, set inactive |

**Special features:**
- **Fork bug workaround**: Extracts real session_id from `CLAUDE_ENV_FILE` path (not from payload which may be stale)
- **Subagent lifecycle**: start_task/end_task tracking, freeze-period message delivery during shutdown
- **Task tool hooking**: Intercepts Task (delegate) tool calls for subagent context
- **Vanilla instance binding**: Searches transcript file backwards in 64MB chunks for `[hcom:instance-name]` marker
- **Timing instrumentation**: Logs per-hook timing via `DispatchTiming` struct

### Gemini CLI (7 hooks, 2597 LoC)

**File:** `/Users/yigitkonur/dev/hcom-repo/src/hooks/gemini.rs`

**Hooks:**
- `gemini-sessionstart` -- Session binding, bootstrap
- `gemini-beforeagent` -- Pre-gate: skip if session not bound (quick DB query)
- `gemini-afteragent` -- Primary delivery point (deliver messages)
- `gemini-beforetool` -- Set status active, log tool context
- `gemini-aftertool` -- Deliver pending messages
- `gemini-notification` -- Forward to events
- `gemini-sessionend` -- Cleanup

**Special features:**
- **Transcript path derivation**: Searches `~/.gemini/chats/` for `rollout-{session_id}.json`
- **Version checking**: Requires Gemini >= 0.26.0 (reads from `package.json`)
- **Per-hook session binding**: Validates session before execution
- **Pre-gate optimization**: BeforeAgent skips non-participants (quick DB query)
- **Policy auto-approval**: `~/.gemini/policies/hcom.toml` with tool approval rules

### Codex (1 hook, 1205 LoC)

**File:** `/Users/yigitkonur/dev/hcom-repo/src/hooks/codex.rs`

**Single event:** `codex-notify` on agent-turn-complete

**Payload:** JSON via argv[2] (command-line argument, not stdin)

**Special features:**
- **No polling loop**: Unlike Claude/Gemini, messages delivered via PTY injection triggered by TranscriptWatcher
- **TCP notify endpoint**: Registered for PTY wake
- **Session binding**: Via `rebind_instance_session()` on first notify event
- **Thread ID extraction**: Searches `$CODEX_HOME/sessions/rollout-*-{thread-id}.jsonl`
- **Idle tracking**: Sets `idle_since` timestamp on turn completion

### OpenCode (4 handlers, 862 LoC)

**File:** `/Users/yigitkonur/dev/hcom-repo/src/hooks/opencode.rs`

**Handlers:**
- `opencode-start` -- Session binding, bootstrap injection, TCP notify registration
- `opencode-status` -- Status updates (listening/active/blocked + context)
- `opencode-read` -- Message delivery endpoint (plugin polls)
- `opencode-stop` -- Cleanup

**Payload:** argv-based flag parsing (not JSON stdin)

**Special features:**
- OpenCode passes SQLite database path as transcript
- Notify endpoint registration for plugin callbacks
- Re-binding detection for reconnection scenarios
- Plugin endpoint TCP notification for instant message delivery
- Event ID initialization from `HCOM_LAUNCH_EVENT_ID` env var

---

## Hook Installation Paths

```
Claude:
  ~/.claude/settings.json (hook entries in top-level)
  $HCOM_DIR/../.claude/settings.json (sandbox mode)

Gemini:
  ~/.gemini/settings.json (hooksConfig.enabled = true)
  ~/.gemini/policies/hcom.toml (auto-approval rules)
  $HCOM_DIR/../.gemini/ (sandbox)

Codex:
  ~/.codex/config.toml (notify line)
  ~/.codex/rules/hcom.rules (execution policy)
  $HCOM_DIR/../.codex/ (sandbox)

OpenCode:
  $XDG_DATA_HOME/opencode/plugins/hcom/plugin.json
  $XDG_DATA_HOME/opencode/plugins/hcom/hcom-hook.js
  (default: ~/.local/share/opencode/)
```

Installation managed by `commands/hooks.rs::cmd_hooks_add()` which dispatches to tool-specific setup functions:
- `hooks/claude.rs::setup_claude_hooks()`
- `hooks/gemini.rs::setup_gemini_hooks()` + `setup_gemini_policy()`
- `hooks/codex.rs::setup_codex_hooks()`
- `hooks/opencode.rs::install_opencode_plugin()`

---

## Message Delivery Within Hooks

### Common Flow (all tools)

1. **Instance resolution** (`common::init_hook_context`):
   - Path 1: `HCOM_PROCESS_ID` -> process_bindings table
   - Path 2: session_id -> session_bindings table
   - Path 3: Transcript marker fallback (search file backwards in 64MB chunks)

2. **Message fetching** (`common::deliver_pending_messages`):
   ```
   get_unread_messages(instance_name)
     -> limit to MAX_MESSAGES_PER_DELIVERY (50)
     -> advance last_event_id cursor
     -> format using messages::format_messages_json()
     -> update instance status to ST_ACTIVE
   ```

3. **Hook output format**:
   - Claude/Gemini: JSON wrapper with `hookSpecificOutput.additionalContext`
   - Codex: No direct message delivery (uses PTY injection)
   - OpenCode: JSON response from `handle_read()` endpoint

4. **Bootstrap injection** (`common::inject_bootstrap_once`):
   - One-time per instance lifecycle (checked via `name_announced` flag)
   - Includes instance name, network status, relay status
   - Injected on SessionStart or resume

---

## Status Tracking

### Per-Hook Status Updates

| Hook | Status Set | Context Example |
|------|-----------|-----------------|
| SessionStart | listening | "start" |
| PreToolUse | active | "tool:Bash", "tool:Write", "tool:Read" |
| PostToolUse | listening (no msgs) or active (delivering) | "deliver:luna" |
| Stop (poll) | listening -> active on message arrival | "poll" |
| PermissionRequest | blocked | "approval" |
| SubagentStart | active | "subagent:nova" |

### Metadata Updated by Hooks

| Field | When updated | By what |
|-------|-------------|---------|
| `last_event_id` | Message delivery | Any delivery hook |
| `session_id` | Session binding | SessionStart, codex-notify, opencode-start |
| `transcript_path` | Set from hook payload | SessionStart or derived |
| `directory` | Captured from context | SessionStart |
| `idle_since` | Turn completion | codex-notify, Stop hook |
| `tcp_mode` | TCP endpoint registered | Any hook with TCP notify |
| `status_time` | Every status change | Any hook |
| `last_stop` | Every hook invocation | Heartbeat update |

---

## Collision Detection

### Mechanism

Two agents edit same file within 30s -> both get notification via subscription system.

**SQL query pattern:**
```sql
SELECT DISTINCT e1.instance, e2.instance, e1.status_detail
FROM events_v e1
JOIN events_v e2 ON e1.status_detail = e2.status_detail
  AND e1.instance != e2.instance
  AND ABS(julianday(e1.timestamp) - julianday(e2.timestamp)) * 86400 < 30
WHERE e1.type = 'status'
  AND e1.status_context LIKE 'tool:Write%'
```

**Prevention mechanisms:**
1. **Process binding table**: Maps process_id -> instance_name, prevents multiple hcom instances in same process
2. **Session binding table**: Enforces 1:1 session -> instance relationship
3. **Stale placeholder cleanup**: `cleanup_stale_placeholders()` purges "pending" instances not bound within timeout
4. **Vanilla binding guard**: Only binds if instance is in `pending` list, early return if no session_id

### Orphan Detection (Claude-specific)
- `subagent_posttooluse` checks if stdin is closed (POLLERR | POLLNVAL, not POLLHUP)
- Detects dead parent in subagent context
- Triggers cleanup if parent process terminated

---

## Performance (~20ms per hook invocation)

### Timing Breakdown (DispatchTiming)

| Stage | Typical Time | What it does |
|-------|-------------|--------------|
| init_ms (dirs + DB init) | 0.5-1.0ms | Open DB, check paths |
| session_ms (get_real_session_id) | 0.2-0.5ms | Extract session from env/payload |
| resolve_ms (instance lookup) | 1-3ms | 3-tier identity resolution |
| bind_ms (vanilla binding) | 1-2ms | Transcript marker search if needed |
| handler_ms (hook logic) | 2-5ms | Tool-specific handler |
| **total_ms** | **5-15ms** | End-to-end |

### Optimizations

- **Fast path for non-participants**: `hook_gate_check()` returns 0 if no instances exist in DB
- **Lazy transcript search**: Only searches if no session binding found
- **Pre-gate for BeforeAgent**: Gemini skips hook if session not bound (quick DB query)
- **Pending instance cache**: `get_pending_instances()` skips file I/O if cache empty
- **TCP notification**: Poll-based wake (30s timeout with `libc::poll()`) instead of busy-loop

### TCP Notification (from common::poll_messages)

- Sets up listening socket on random port: `127.0.0.1:0`
- Registers port in `notify_endpoints` table (kind="pty")
- Uses `libc::poll()` for non-blocking accept with timeout
- Senders call `instances::notify_instance_endpoints()` to TCP-wake
- Enables sub-second message delivery instead of waiting for next hook fire

### Panic Guard

All handlers wrapped in `dispatch_with_panic_guard()`:
- Catches panics via `std::panic::catch_unwind()`
- Returns fallback result (exit 0, empty string) instead of crashing host AI tool
- Logs panic location + message to stderr

---

## Router Integration

**Hook dispatch flow (from router.rs):**

```
main()
  -> router::dispatch()
    -> resolve_action(argv)
      -> is_hook(cmd_token) check against CLAUDE_HOOKS, GEMINI_HOOKS, CODEX_HOOKS, OPENCODE_HOOKS
      -> Action::Hook { hook, args }
    -> match on hook type:
      - CLAUDE_HOOKS -> dispatch_claude_hook(hook)
      - GEMINI_HOOKS -> dispatch_gemini_hook(hook)
      - CODEX_HOOKS -> dispatch_codex_hook(args)
      - OPENCODE_HOOKS -> dispatch_opencode_hook(hook, args)
```

**Hook detection constants (router.rs):**
- 10 Claude hooks (lines 17-28)
- 7 Gemini hooks (lines 31-39)
- 1 Codex hook (line 42)
- 4 OpenCode hooks (lines 45-50)

---

## Summary: Hook Architecture Comparison

| Aspect | Claude | Gemini | Codex | OpenCode |
|--------|--------|--------|-------|----------|
| **Input** | stdin (JSON) | stdin (JSON) | argv[2] (JSON) | argv flags |
| **Hooks** | 10 | 7 | 1 | 4 |
| **Message Delivery** | Hook output | Hook output | PTY injection | Plugin endpoint |
| **Session Binding** | SessionStart | BeforeAgent | codex-notify | opencode-start |
| **Transcript Path** | Hook payload | Derived from session_id | Derived from thread_id | OpenCode DB |
| **Status Updates** | Per hook | Fewer hooks | On turn-complete | On status/idle |
| **Panic Safety** | Yes | Yes | Yes | Yes |
| **Blocking Hooks** | Stop, SubagentStop | None | None | None |
| **TCP Notify** | Yes (poll) | No | Yes (notify) | Yes (plugin) |
| **Auto-Approval** | Plugin settings | Policy TOML | Rules TOML | Plugin settings |
| **Vanilla Support** | Via transcript marker | Via marker | Via marker | No |

---

## File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `src/hooks/mod.rs` | ~200 | Shared types (HookPayload, HookResult) |
| `src/hooks/common.rs` | ~800 | Shared functions (deliver_pending_messages, poll_messages, init_hook_context) |
| `src/hooks/utils.rs` | ~150 | Hook registry and categories |
| `src/hooks/family.rs` | ~300 | Tool family abstraction (extract_tool_detail, bind_vanilla_instance) |
| `src/hooks/claude.rs` | 3162 | Claude hook dispatcher (10 hooks) |
| `src/hooks/gemini.rs` | 2597 | Gemini hook dispatcher (7 hooks) |
| `src/hooks/codex.rs` | 1205 | Codex notify handler (1 event) |
| `src/hooks/opencode.rs` | 862 | OpenCode plugin handlers (4 endpoints) |
| `src/router.rs` | ~300 | CLI router with hook detection |
| `src/commands/hooks.rs` | ~500 | `hcom hooks add/remove` commands |
