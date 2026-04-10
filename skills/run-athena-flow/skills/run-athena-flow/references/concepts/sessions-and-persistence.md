# Sessions and Persistence

Every Athena run is persisted to SQLite. You can resume any session, inspect its history, and pick up where you left off.

## Storage Location

```
~/.config/athena/sessions/<session-uuid>/session.db
```

Each session gets its own isolated database file.

## Schema (v4)

Five tables:

### `session`

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT | Session UUID |
| `project_dir` | TEXT | Working directory |
| `created_at` | INTEGER | Unix timestamp |
| `updated_at` | INTEGER | Unix timestamp |
| `label` | TEXT | Human-readable label |
| `event_count` | INTEGER | Total events |

### `runtime_events`

Raw hook events as received from the agent harness.

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT | Event UUID |
| `seq` | INTEGER (UNIQUE) | Sequence number |
| `timestamp` | INTEGER | Unix timestamp |
| `hook_name` | TEXT | Original hook name |
| `adapter_session_id` | TEXT | Agent session ID |
| `payload` | JSON | Full event payload |

### `feed_events`

Derived display events for the UI. One runtime event can produce multiple feed events.

| Column | Type | Description |
|--------|------|-------------|
| `event_id` | TEXT | Feed event UUID |
| `runtime_event_id` | TEXT | Source runtime event |
| `seq` | INTEGER (UNIQUE) | Display sequence |
| `kind` | TEXT | Feed event kind |
| `run_id` | TEXT | Run context |
| `actor_id` | TEXT | Actor (user/agent/subagent) |
| `timestamp` | INTEGER | Unix timestamp |
| `data` | JSON | Display data |

### `adapter_sessions`

Agent session records with token accounting.

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | TEXT | Agent session ID |
| `started_at` | INTEGER | Start timestamp |
| `ended_at` | INTEGER | End timestamp |
| `model` | TEXT | Model used |
| `source` | TEXT | Harness source |
| `tokens_input` | INTEGER | Input tokens |
| `tokens_output` | INTEGER | Output tokens |
| `tokens_cache_read` | INTEGER | Cache read tokens |
| `tokens_cache_write` | INTEGER | Cache write tokens |
| `tokens_context_size` | INTEGER | Context window size |

### `schema_version`

Migration version tracking.

## Resume

Resume the most recent session:

```bash
athena-flow resume
```

Resume a specific session:

```bash
athena-flow resume <session-uuid>
```

Browse sessions interactively:

```bash
athena-flow sessions
```

Resume works by replaying `feed_events` from the store back into the timeline. The event feed populates with historical events, then new events stream in as they arrive.

## Resume in Exec Mode

```bash
athena-flow exec "continue previous work" --continue
athena-flow exec "continue" --continue=<session-uuid>
```

## WAL Mode

The database uses WAL (Write-Ahead Logging) with an exclusive write lock. This allows Athena's session registry to read sessions from other instances without contention.

## Degraded Mode

If the database cannot be opened (disk full, permissions), Athena continues in **degraded mode** — events are processed and displayed but not persisted. The header indicates degraded state, and session resume is unavailable.

## Ephemeral Mode

Skip persistence entirely:

```bash
athena-flow exec "check status" --ephemeral
```

No session database is created. The session cannot be resumed.

## Session Statistics

During an active session:

- `/stats` — Session-level statistics (event counts, duration)
- `/context` — Token breakdown and current context window usage
