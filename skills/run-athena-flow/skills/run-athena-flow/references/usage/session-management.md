# Session Management

Every Athena run creates a session persisted to SQLite at `~/.config/athena/sessions/<session-uuid>/session.db`.

## Browse Sessions

```bash
athena-flow sessions
```

Opens an interactive picker. Navigate with arrow keys, press Enter to resume.

Also available as a slash command during a session:

```
/sessions
```

## Resume

Resume the most recent session for the current project:

```bash
athena-flow resume
```

Resume a specific session by ID:

```bash
athena-flow resume <session-uuid>
```

Resume works by replaying `feed_events` from the SQLite store back into the timeline. The event feed populates with historical events, then new events stream in as they arrive.

## Resume in Exec Mode

```bash
athena-flow exec "continue previous work" --continue
athena-flow exec "continue" --continue=<session-uuid>
```

## Session Data Stored

Each session stores:

- **Runtime events** — raw hook events from the agent harness with full payloads
- **Feed events** — derived display events shown in the UI timeline
- **Adapter sessions** — Agent session records with token usage (input, output, cache read/write, context size)
- **Metadata** — project directory, timestamps, event count, label

## Session Statistics

During an active session:

| Command | Description |
|---------|-------------|
| `/stats` | Session-level statistics (event counts, duration) |
| `/context` | Token breakdown and current context window usage |

## Ephemeral Sessions

Skip session persistence entirely:

```bash
athena-flow exec "quick check" --ephemeral
```

No database file is created. The session cannot be resumed.

## WAL Mode

The database uses WAL (Write-Ahead Logging) with an exclusive write lock. This allows Athena's session registry to read sessions from other instances without contention.

## Degraded Mode

If the database cannot be opened (disk full, permissions, locked), Athena continues in **degraded mode**:

- Events are processed and displayed but not persisted
- The header indicates degraded state
- Session resume is unavailable
- New sessions continue to function for the current run
