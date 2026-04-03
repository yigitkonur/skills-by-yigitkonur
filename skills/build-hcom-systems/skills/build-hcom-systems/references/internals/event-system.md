# hcom Event System — Complete Reference

Events are the nervous system of hcom. Every action is recorded, queryable, and subscribable.

## Event Types

### message (agent-to-agent communication)
```json
{
  "from": "luna",
  "text": "review complete, all tests pass",
  "scope": "mentions",
  "mentions": ["nova"],
  "intent": "inform",
  "thread": "review-1",
  "reply_to": 42,
  "reply_to_local": 42,
  "bundle_id": "bundle:abc123",
  "delivered_to": ["nova"],
  "sender_kind": "instance",
  "_relay": false
}
```

**Fields:**
- `from`: Sender instance name
- `text`: Message content
- `scope`: "broadcast" (everyone) or "mentions" (targeted)
- `mentions`: JSON array of mentioned agent base names
- `intent`: "request" (expect reply), "inform" (FYI), "ack" (acknowledge)
- `thread`: Thread identifier for conversation isolation
- `reply_to`: Referenced event ID
- `reply_to_local`: Local event ID (for relay dedup)
- `bundle_id`: Associated context bundle
- `delivered_to`: JSON array of recipients who received this
- `sender_kind`: "instance" (agent), "external" (--from flag), "system" (hcom-events)
- `_relay`: true if imported via relay (prevents re-sync loops)

### status (agent state changes)
```json
{
  "status": "active",
  "context": "tool:Bash",
  "detail": "git status"
}
```

**Fields:**
- `status`: active, listening, blocked, inactive, launching, error
- `context`: What triggered the change (tool:Bash, tool:Write, deliver:luna, poll, approval, stale:listening)
- `detail`: Specific info (command text, filename, approval reason)

**Common context patterns:**
- `tool:Bash` + detail="npm install" -- running shell command
- `tool:Write` + detail="src/main.py" -- writing file
- `tool:Read` + detail="config.toml" -- reading file
- `deliver:luna` -- delivering messages to luna
- `poll` -- idle polling
- `approval` -- waiting for user approval
- `stale:listening` -- marked inactive due to heartbeat timeout

### life (lifecycle transitions)
```json
{
  "action": "started",
  "by": "user",
  "reason": "launch",
  "snapshot": {
    "name": "luna",
    "status": "active",
    "tool": "claude",
    "tag": "worker",
    "directory": "/home/user/project"
  }
}
```

**Actions:** created, started, ready, stopped, batch_launched
**By:** user, script, system, remote
**Snapshot:** Instance state at time of event (for resume/fork)

### bundle (structured context packages)
```json
{
  "bundle_id": "bundle:a1b2c3d4",
  "title": "Auth Module Context",
  "description": "Full context for cross-agent debugging of auth module",
  "refs": {
    "events": ["123", "124-130"],
    "files": ["src/auth.py", "tests/test_auth.py"],
    "transcript": ["1-5:normal", "10:full", "20-30:detailed"]
  },
  "extends": "bundle:parent-id",
  "created_by": "luna"
}
```

---

## Event Recording Mechanism

### Recording Functions (db.rs, lines 1810-2400)

- `log_event(type, instance, data)` -> Returns event_id
- `log_event_with_ts(type, instance, data, timestamp)` -> Timestamped variant
- `log_status_event(instance, status, context, detail)` -> Status shorthand
- `log_life_event(instance, action, by, reason, snapshot)` -> Lifecycle shorthand

### What Creates Events

| Source | Event Type | When |
|--------|-----------|------|
| `hcom send` | message | Agent or script sends a message |
| Tool execution hooks | status | PreToolUse/PostToolUse fires |
| File operations (hooks) | status | Write/Read tool detected |
| Shell commands (hooks) | status | Bash tool detected |
| Agent lifecycle | life | create/start/stop |
| Bundle creation | bundle | `hcom send --title ...` or `hcom bundle prepare` |
| System notifications | message (sender_kind=system) | Subscription match, collision alert |

### Inline Subscription Checking

Every `log_event()` call triggers `check_event_subscriptions()` **synchronously** before returning:
- Scans all subscriptions in KV table
- Tests each against the new event
- Non-blocking: errors are logged, never propagated to caller
- This is how subscriptions deliver in real-time

---

## Query System

### Command: `hcom events [flags]`

### Flag-Based Filters (src/core/filters.rs)

Filters use `FilterMap` (HashMap<String, Vec<String>>):
- **Multiple values for same flag = OR semantics**: `--agent luna --agent nova` = luna OR nova
- **Different flags = AND semantics**: `--agent luna --type message` = agent is luna AND type is message

| Flag | Mapped Field | Compatible Types | Examples |
|------|-------------|-----------------|----------|
| `--agent` | `instance` | Any | `--agent luna --agent nova` (OR) |
| `--type` | `type` | Any | message, status, life, bundle |
| `--status` | `status_val` | status | active, listening, blocked |
| `--context` | `status_context` | status | tool:Bash, deliver:luna, tool:* |
| `--file` | `status_detail` | status | *.py, main.rs, *test* (glob) |
| `--cmd` | `status_detail` | status | =exact, ^prefix, $suffix, *glob, contains |
| `--from` | `msg_from` | message | agent name |
| `--mention` | `msg_mentions` | message | @-mentioned agent |
| `--intent` | `msg_intent` | message | request, inform, ack |
| `--thread` | `msg_thread` | message | thread name |
| `--reply-to` | `msg_reply_to` | message | event ID |
| `--action` | `life_action` | life | created, started, ready, stopped |
| `--after` | `timestamp` | Any | ISO-8601 timestamp |
| `--before` | `timestamp` | Any | ISO-8601 timestamp |
| `--collision` | FTS collision logic | status | Boolean flag (no value) |

### Shortcuts
- `--idle AGENT` expands to `--agent AGENT --status listening`
- `--blocked AGENT` expands to `--agent AGENT --status blocked`

### SQL WHERE Mode
```bash
hcom events --sql "type='status' AND status_val='active'"
```
**Combines with flags:** `--agent luna --file '*.py' --sql "status_val != 'listening'"` produces:
```sql
WHERE (agent_filters) AND (flag_filters) AND (custom_sql)
```

### Validation
- `validate_type_constraints()` ensures flag types don't conflict
- Cannot mix status flags (`--status`) with message flags (`--from`)

### events_v View SQL
```sql
CREATE VIEW events_v AS
SELECT id, timestamp, type, instance, data,
  json_extract(data, '$.from') as msg_from,
  json_extract(data, '$.text') as msg_text,
  json_extract(data, '$.scope') as msg_scope,
  json_extract(data, '$.mentions') as msg_mentions,
  json_extract(data, '$.intent') as msg_intent,
  json_extract(data, '$.thread') as msg_thread,
  json_extract(data, '$.reply_to') as msg_reply_to,
  json_extract(data, '$.delivered_to') as delivered_to,
  json_extract(data, '$.bundle_id') as bundle_id,
  json_extract(data, '$.sender_kind') as sender_kind,
  json_extract(data, '$.status') as status_val,
  json_extract(data, '$.context') as status_context,
  json_extract(data, '$.detail') as status_detail,
  json_extract(data, '$.action') as life_action
FROM events;
```

---

## Subscription Engine

### Creation: `hcom events sub [filters/SQL] [--once] [--for AGENT]`

### Storage
- KV table with key `events_sub:sub-{8-char-hash}`
- JSON value: `{id, caller, sql, filters, last_id, once, created}`
- Request-watches: `events_sub:reqwatch-{id}` with extra filter metadata

### Creation Logic

**Filter-based subscriptions** (`create_filter_subscription`):
1. Convert flags to SQL via `build_sql_from_flags()`
2. Combine with user `--sql` if present
3. Apply collision self-relevance filtering
4. ID = `SHA256(caller + filters + sql + once)[:8]`
5. Deduplication by ID (same caller+filter = same subscription)

**SQL-based subscriptions** (`events_sub_sql`):
1. Direct SQL validation
2. ID = `SHA256(caller + sql + once)[:8]`
3. Deterministic IDs prevent duplicates

### Matching Mechanism

When `log_event()` fires, `check_event_subscriptions()` runs synchronously:

1. **Recursion guards** skip:
   - Events from `sys_*` instances
   - Messages from `[hcom-events]` system sender
   - Messages with `sender_kind='system'`

2. For each subscription in KV:
   - Skip if `event_id <= last_id` (already processed)
   - Test SQL filter: `SELECT 1 FROM events_v WHERE id = ? AND (sql_filter)`
   - Special gates for request-watches (waterline check, reply guards)
   - If matches: format notification, send message, update cursor

### Notification Delivery

System message sent to caller from `[hcom-events]`:
```
[sub:abc12345] #42 status luna tool:Write /tmp/file.py
[sub:abc12345] #45 message nova -> luna "review complete"
```

Delivered via normal message delivery pipeline (hooks or PTY injection).

### --once Behavior
- Subscriptions marked `"once": true`
- On match: delete KV entry (no cursor update)
- Auto-removes after first match
- Listener must re-subscribe for next event

### Idempotent IDs
- Same SQL + caller = same hash = same subscription ID
- Prevents duplicate subscriptions via deterministic hash
- Dedup check: `if kv_get(sub_key).is_some() -> skip`

---

## FTS5 Full-Text Search

### Virtual Table
```sql
CREATE VIRTUAL TABLE events_fts USING fts5(searchable, tokenize='unicode61');
```

### Index Content (via trigger)
```sql
CREATE TRIGGER events_fts_insert AFTER INSERT ON events BEGIN
  INSERT INTO events_fts(rowid, searchable) VALUES (
    new.id,
    COALESCE(json_extract(new.data, '$.text'), '') || ' ' ||
    COALESCE(json_extract(new.data, '$.from'), '') || ' ' ||
    COALESCE(new.instance, '') || ' ' ||
    COALESCE(json_extract(new.data, '$.context'), '') || ' ' ||
    COALESCE(json_extract(new.data, '$.detail'), '') || ' ' ||
    COALESCE(json_extract(new.data, '$.action'), '') || ' ' ||
    COALESCE(json_extract(new.data, '$.reason'), '')
  );
END;
```

### Searchable Fields (concatenated)
Message text, sender, instance name, status context (tool type), detail (filename/command), life action, reason.

### Query Usage (TUI, src/tui/db.rs)
```sql
SELECT * FROM events e
JOIN events_fts ON events_fts.rowid = e.id
WHERE events_fts MATCH ?1
ORDER BY events_fts.rank
```

---

## Bundle System

### Structure
```json
{
  "bundle_id": "bundle:a1b2c3d4",
  "title": "Auth Module Context",
  "description": "Full context for cross-agent debugging",
  "refs": {
    "events": ["123", "124-130"],
    "files": ["src/auth.py", "tests/test_auth.py"],
    "transcript": ["1-5:normal", "10:full", "20-30:detailed"]
  },
  "extends": "bundle:parent-id",
  "created_by": "luna"
}
```

### Transcript Detail Levels
- `normal`: Truncated output (default)
- `full`: Complete text without tool I/O
- `detailed`: Complete text with tool I/O, file edits, Bash output

### Inline Bundle Creation
```bash
hcom send @reviewer --title "Auth Context" \
  --description "Refactored auth module" \
  --transcript 1-20:full \
  --files src/auth.py,tests/test_auth.py \
  --events 42-50 \
  --intent request -- "Review this"
```

### Validation
- Required: title, description, refs (events OR files OR transcript)
- Transcript refs must include detail level: `"3-14:normal"` or `{"range": "3-14", "detail": "normal"}`
- File existence warnings (non-fatal)
- Max size estimate: 15,000 lines (prevents massive dumps)
- Extends: parent bundle reference (non-blocking validation)

### Bundle Chaining
`--extends bundle:parent-id` creates incremental context. Child bundle inherits parent's refs and adds new ones.

---

## Reactivity and Agent-to-Agent Workflows

### Subscription Listening
```bash
# Agent A subscribes to B going idle
hcom events sub --idle worker-B --once
# A's hook delivers system notification when B enters listening status
```

### Request-Watch Pattern
- Special subscription type with waterline gate and reply guards
- Tracks if watched target replied to a request
- Cancels automatically on reply (race-safe with concurrent logging)
- Used internally for `--intent request` auto-monitoring

### Collision Detection
```bash
hcom events sub --collision
```
- Notifies when two agents edit same file within 30s
- SQL: `EXISTS` join checking file_context + detail + time proximity
- Self-relevance filter prevents agent matching own writes

### File Change Monitoring
```bash
hcom events sub --file "src/*.py"
# Triggers when any agent writes a matching file
```

### Status-Driven Workflows
```bash
hcom events sub --agent nova --status blocked
# Triggers when nova gets blocked (e.g., approval prompt)
```

---

## File Reference

| File | Key Functions | Purpose |
|------|---------------|---------|
| `src/commands/events.rs` | `cmd_events()`, `events_sub_filter()`, `create_filter_subscription()` | Event query, subscription creation |
| `src/commands/listen.rs` | `cmd_listen()`, `listen_loop()`, `listen_with_filter()` | Blocking wait with filters |
| `src/core/filters.rs` | `build_sql_from_flags()`, `expand_shortcuts()`, `validate_type_constraints()` | Flag parsing, SQL generation |
| `src/core/bundles.rs` | `create_bundle_event()`, `validate_bundle()`, `parse_inline_bundle_flags()` | Bundle creation and validation |
| `src/core/detail_levels.rs` | `DetailLevel`, `validate_detail_level()` | Transcript detail enums |
| `src/db.rs` (278-430) | Schema: events table, events_v view, events_fts | Storage schema |
| `src/db.rs` (1810-2400) | `log_event()`, `check_event_subscriptions()`, `send_sub_notification()` | Recording, matching, notification |
