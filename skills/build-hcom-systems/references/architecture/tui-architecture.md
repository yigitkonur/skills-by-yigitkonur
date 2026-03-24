# hcom TUI Architecture — Complete Reference

High-performance operator dashboard built on ratatui + crossterm with dual-mode rendering, real-time agent monitoring, and full-text search.

## Framework

- **Rendering**: ratatui (Rust TUI library) with crossterm for terminal control
- **Theme**: Tokyo Night palette (blue, cyan, green, red, yellow, orange, magenta)
- **Event loop**: Adaptive tick rate (80ms animating, 350ms idle)
- **Data source**: SQLite via `DataSource` trait (read-only, `query_only=ON`)

## Rendering Architecture

**Entry point:** `render/mod.rs::render(frame, app)`

### Panel Layout

**Inline mode** (ViewMode::Inline):
- Agent list only (single panel, bottom overlay)
- Uses `Viewport::Inline(height)` -- bottom panel overlay on scrollback
- Timeline limit: 200 events (memory-constrained)

**Vertical mode** (ViewMode::Vertical):
- Fullscreen alternate screen (`EnterAlternateScreen`)
- Left panel: Agent list (active, remote, stopped in collapsible sections)
- Right panel: Messages feed, events timeline, or command output
- Bottom: Input area (compose, search, command palette)
- Mouse support enabled

### Sub-render Modules

| Module | What it renders |
|--------|----------------|
| `render/agents.rs` | Agent list with status icons, tags, unread counts, spinner for launching |
| `render/messages.rs` | Message feed, events timeline, command output with search/filter |
| `render/launch.rs` | Launch panel: tool selector, count, tag, terminal preset |
| `render/text.rs` | Text formatting, span truncation, syntax highlighting for messages |

### Status Icons
- Active: green dot
- Listening: blue circle
- Blocked: yellow lock
- Launching: animated spinner (10 frames, tick-driven)
- Inactive: gray dash

## State Management

### DataState (`state.rs`)
```rust
struct DataState {
    agents: Vec<Agent>,              // Active agents
    remote_agents: Vec<Agent>,       // Remote agents (via relay)
    stopped_agents: Vec<Agent>,      // Recently stopped agents
    messages: Vec<Message>,          // Timeline messages
    events: Vec<Event>,              // Timeline events
    relay_enabled: bool,
    relay_status: String,
    relay_error: Option<String>,
    search_results: Option<(Vec<Message>, Vec<Event>)>,  // FTS results
}
```

### UiState (`state.rs`)
```rust
struct UiState {
    // Navigation
    cursor: usize,
    selected: BTreeSet<usize>,       // Multi-select for batch operations

    // Input
    input: String,
    input_cursor: usize,
    input_scroll: usize,             // Multi-line compose scroll

    // Modes
    mode: InputMode,                 // Navigate, Compose, CommandOutput, Launch, Relay
    view_mode: ViewMode,             // Inline or Vertical

    // Overlays
    search_active: bool,
    search_query: String,
    command_palette: Option<CommandPalette>,
    tag_overlay: bool,

    // Inline ejection
    eject_filter: Option<String>,
    inline_filter_changed: bool,
    needs_resize: bool,
    needs_clear_replay: bool,

    // UI chrome
    flash_message: Option<(String, Instant)>,
    help_visible: bool,
    confirm_dialog: Option<ConfirmDialog>,
    relay_popup: bool,
}
```

### App Struct (`app.rs`)
```rust
pub struct App {
    pub data: DataState,
    pub ui: UiState,
    pub ejector: Ejector,                     // Inline scrollback ejector
    pub(crate) source: Box<dyn DataSource>,   // DB or mock
    pub(crate) rpc_client: Option<RpcClient>,
}
```

## Inline vs Fullscreen Modes

### Inline Mode
- Bottom panel overlay using `Viewport::Inline(height)`
- Agent list only, no messages panel
- **Ejector system**: Incremental output to terminal scrollback
  - `eject_new()`: Append new events/messages since last watermark (200 lines/tick)
  - `eject_command_output()`: Print command results
  - `begin_replay()`: Full refresh after filter/search changes
- On resize: clears viewport, reconstructs terminal, replays filtered content
- Detects cursor position via ANSI escape sequences before entering
- Synchronized updates: `BeginSynchronizedUpdate` / `EndSynchronizedUpdate` to reduce flicker

### Vertical Mode
- Fullscreen with `EnterAlternateScreen`
- Side-by-side panels (agents + messages)
- Timeline limit: 5000 events
- Mouse support enabled
- Simpler rendering (no ejection, direct frame draw)

### Switching
- Triggered by Ctrl+V or window too small for vertical
- Breaks run loop, clears screen, reinitializes viewport

## RPC Communication

### RpcClient (`rpc_async.rs`)
- **Thread-based**: Spawns dedicated worker thread with mpsc channels
- **Non-blocking**: Submit operations, drain results on each tick
- **~5ms overhead**: Commands run as subprocesses (not in-process) to avoid stdout corruption

### Operations

| Operation | What it does |
|-----------|-------------|
| `Send` | Send @mention messages to agents |
| `KillAgent` | Kill agent + close pane |
| `ForkAgent` | Clone session with new identity |
| `KillPid` | Kill specific PID |
| `Tag` | Set display name/tag |
| `Launch` | Spawn new agent (Claude/Gemini/Codex/OpenCode) |
| `RelayToggle` | Enable/disable relay |
| `RelayStatus` | Check relay status |
| `RelayNew` | Create relay group |
| `RelayConnect` | Join relay group |
| `Command` | Run arbitrary hcom subcommand |

### Result Handling (`actions.rs`)
- `apply_rpc_result()`: Dispatches result by operation type
- Updates UI state: flash messages, reload data, enter output mode
- Inline mode: marks `pending_eject_cmd` to trigger ejection
- Vertical mode: enters `CommandOutput` input mode

## Data Synchronization

### DataSource Trait (`data.rs`)
```rust
trait DataSource {
    fn load(&mut self) -> DataState;                         // Full snapshot
    fn load_if_changed(&mut self) -> Option<DataState>;      // Only if DB changed
    fn load_all_stopped(&mut self) -> Vec<Agent>;            // All stopped agents
    fn search_timeline(&mut self, query: &str, limit: usize) -> (Vec<Message>, Vec<Event>);
}
```

### DbDataSource (`db.rs`)
- SQLite backend: `~/.hcom/hcom.db`
- Lazy connection with WAL journal, 3s timeout
- **Read-only**: `query_only=ON` (TUI never writes to DB)
- **Change detection**: `PRAGMA data_version` + config.toml mtime
- Caches snapshot; only reloads if version changed
- **FTS search**: Full-text search across events/messages

### Reload Strategy
- On tick: 120ms when animating, 350ms when idle
- Cursor stability: preserves selected agent by name across reloads
- Search persistence: updates FTS results if query active
- Relay status transition detection: shows "connected" text for 5s

## Input Handling (`input.rs`)

### Navigate Mode (default)

| Key | Action |
|-----|--------|
| `j/k` or arrows | Move cursor up/down |
| `Space` | Select/deselect agent (multi-select) |
| `Enter` | Compose message to selected agents |
| `/` | Open search overlay |
| `!` | Open command palette |
| `#` | Open tag overlay |
| `l` | View agent logs/messages |
| `o` | Open relay config popup |
| `Ctrl+S` | Toggle "show all stopped" agents |
| `Ctrl+V` | Toggle inline/vertical mode |
| `Ctrl+R` | Open relay popup |
| `?` | Toggle help |
| `q` | Quit |

### Compose Mode

| Key | Action |
|-----|--------|
| Type | Accumulate message body |
| `Ctrl+A/E` | Start/end of line |
| `Ctrl+W/U` | Delete word / delete to start |
| `Ctrl+Enter` | Send message |
| `Esc` | Cancel compose |

### Overlay Modes (Search/Command/Tag)

| Key | Action |
|-----|--------|
| Type | Filter/search text |
| `Up/Down` | Browse palette suggestions (Command only) |
| `Enter` | Apply (execute command, set tag, search) |
| `Esc` | Cancel overlay |

### Recipient Parsing (`input/compose.rs`)
- Format: `@agent1 @agent2 message body`
- Parses `@name` tokens; rest is body
- Deduplicates; preserves punctuation in body

## Command Palette (`model.rs`)

- Filterable list of hcom commands (list, log, kill, fork, tag, etc.)
- `CommandPalette` struct: all suggestions + filtered indices + cursor position
- Invoked with `!`
- Shows suggestions, highlights matches, browse with arrows
- Enter executes selected command

## Key Capabilities

### Batch Operations
- Multi-select agents with Spacebar
- Message all selected: Enter -> compose -> send to all
- Kill/fork all: confirmation dialogs with timeout animations

### Full-Text Search
- Active via `/` overlay
- Searches messages + events in DB via FTS5
- Filters timeline in real-time
- Inline: triggers ejector replay with filtered content

### Agent Status Monitoring
- Real-time heartbeat tracking
- Status computation: Active, Listening, Blocked, Launching, Inactive
- Stale detection: PTY blocked (tui:* context), heartbeat timeout
- Launching spinner (10 frames, tick-driven animation)

### Relay Integration
- Ctrl+R: Open relay popup
- Toggle enable/disable
- View status, create token, connect remote instance
- Inline popup or inline text banner ("Relay connected" for 5s)

## Main Event Loop (`app.rs`, lines 204-350)

```
loop {
    drain_rpc_results()           // Apply pending RPC results

    if break_conditions:          // needs_resize, should_quit, switch_viewport
        break

    if dirty:
        if inline_mode:
            sync_update_start()
            handle_replay/eject()  // Incremental output
        render::render()           // Ratatui frame draw
        if inline_mode:
            sync_update_end()

    poll(80ms or 500ms)           // Adaptive: 80ms animating, 500ms idle
    handle_events()               // Key, paste, mouse, resize
    debounce_resize()             // 160ms cooldown for inline viewport

    increment_tick()              // Spinner frames
    data_reload()                 // 120ms or 350ms reload interval
    expire_flash/confirm()        // Auto-dismiss messages
}
```

**Dirty flag triggers:** RPC results, key/mouse events, paste, animations (spinner, flash, launching state)

## Inline Ejection System

**Problem:** Terminal scrollback corruption on resize; ratatui's autoresize does not work well with inline viewport.

**Solution:** `Ejector` struct tracks watermarks:
- `last_event_row_id`: Last event ejected
- `last_msg_id`: Last message ejected
- `eject_new()`: Append only events/messages since watermark (200 lines/tick)
- `begin_replay()`: Clear and full refresh after filter/search change
- Uses direct ANSI sequences: positioning, clearing, text

**Replay:** On filter/search change, rebuild items, apply filter, emit lines gradually to avoid stalls.

## File Reference

| File | Purpose |
|------|---------|
| `src/tui/app.rs` | App struct, main run loop, lifecycle |
| `src/tui/state.rs` | DataState + UiState definitions |
| `src/tui/render/mod.rs` | Main render dispatcher |
| `src/tui/render/agents.rs` | Agent list rendering |
| `src/tui/render/messages.rs` | Message/event timeline |
| `src/tui/render/launch.rs` | Launch panel |
| `src/tui/render/text.rs` | Text formatting utilities |
| `src/tui/input.rs` | Key/paste/mouse dispatch |
| `src/tui/input/compose.rs` | Compose mode, recipient parsing |
| `src/tui/rpc_async.rs` | Async RPC client (thread-based) |
| `src/tui/commands.rs` | Subprocess command execution |
| `src/tui/actions.rs` | RPC result application |
| `src/tui/data.rs` | DataSource trait |
| `src/tui/db.rs` | SQLite datasource + FTS |
| `src/tui/inline/eject.rs` | Inline scrollback ejection |
| `src/tui/theme.rs` | Tokyo Night color palette |
| `src/tui/status.rs` | Agent status computation |
| `src/tui/model.rs` | Command palette model |
| `src/tui/config.rs` | Config integration |
