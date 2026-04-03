# hcom PTY and Terminal Management — Complete Reference

How hcom spawns, monitors, and injects into agent terminal sessions. The PTY system is essentially a "window manager for AI agents."

## Terminal Spawning (3 Modes)

**Entry point:** `src/terminal.rs::launch_terminal()` (lines 915-1215)

### Mode 1: Background (non-interactive)
- Spawns with `setsid()` to detach into own session
- Redirects stdout/stderr to log file: `~/.hcom/.tmp/logs/background_<timestamp>_<rand>.log`
- Returns `LaunchResult::Background(log_file, pid)` immediately

### Mode 2: Run-Here (blocking, same terminal)
- Uses `execve()` to replace entire process with bash script
- Inherits terminal; stays in same session/pane
- Resolves from `detect_terminal_from_env()` to support same-terminal close-on-kill
- Never returns (process replaced)

### Mode 3: New Window/Pane (default for multi-agent)
- Auto-detect terminal preset -> create bash script -> spawn in new pane/tab
- Smart detection priority:
  1. Inside kitty -> uses `kitty-split` if KITTY_WINDOW_ID detected
  2. Inside wezterm -> uses `wezterm-split` if WEZTERM_PANE detected
  3. Inside tmux -> uses `tmux-split` if TMUX_PANE detected
  4. Inside zellij -> uses `zellij` if ZELLIJ_PANE_ID detected
  5. Detect available terminals via socket/CLI tools
  6. Fallback: macOS Terminal.app or Linux gnome-terminal

### Script Creation (`create_bash_script()`)
- Generates bash script with environment variables
- Unsets AI tool markers (`CLAUDECODE`, `GEMINI_CLI`, `CODEX_SANDBOX`, etc.) to prevent inheritance
- Injects required binaries into PATH for minimal environments
- Handles Termux edge case (node shebangs for npm-installed tools)
- Makes script executable (`0755`)
- Path: `~/.hcom/.tmp/launch/<tool>_<instance>_<pid>_<rand>.sh`

### Run-Here Logic
```
will_run_in_current_terminal(count, background, run_here, terminal, inside_ai_tool):
  - run_here explicit flag -> same window
  - terminal="here" -> same window
  - inside_ai_tool=true -> new terminal (prevent nesting)
  - background=true -> new terminal
  - count > 1 -> new terminal (batch launch needs multiple)
  - Otherwise: count == 1 -> same window
```

---

## 24 Built-In Terminal Presets

**Location:** `src/shared/terminal_presets.rs` (381 lines)

### Preset Structure
```rust
pub struct TerminalPreset {
    pub binary: Option<&'static str>,        // e.g., "kitty"
    pub app_name: Option<&'static str>,      // e.g., "kitty" or "WezTerm"
    pub open: &'static str,                  // Command template with {script}
    pub close: Option<&'static str>,         // Close template with {pane_id}
    pub pane_id_env: Option<&'static str>,   // Env var for pane ID
    pub platforms: &'static [&'static str],  // ["Darwin", "Linux", "Windows"]
}
```

### Complete Preset List

| Category | Presets |
|----------|---------|
| **Multiplexers** | tmux, tmux-split, zellij, cmux |
| **Smart Launchers** | kitty (auto-split), wezterm (auto-split), kitty-window, wezterm-window, wezterm-tab |
| **macOS Native** | terminal.app, iterm, ghostty |
| **Linux** | gnome-terminal, konsole, xterm, tilix, terminator |
| **Windows** | windows-terminal, mintty, wttab |
| **Tab Utilities** | ttab (macOS) |
| **Modern** | waveterm (wsh), alacritty |

### Environment Detection (`detect_terminal_from_env()`)

Checks in order:
1. `KITTY_WINDOW_ID` -> kitty
2. `WEZTERM_PANE` -> wezterm
3. `TMUX_PANE` -> tmux
4. `ZELLIJ_PANE_ID` -> zellij
5. TOML custom presets with `pane_id_env` defined
6. `TERM_PROGRAM` -> ghostty, iTerm, Terminal.app

### Close Command Placeholders
- `{pane_id}`: Primary ID (WEZTERM_PANE, KITTY_WINDOW_ID, etc.)
- `{pid}`: Process ID
- `{process_id}`: hcom's process ID (for nested sessions)
- `{id}`: Fallback to terminal_id if pane_id missing
- Missing placeholders -> close command skipped

### Kitty Special Handling
- Outside kitty: auto-detects socket via `kitten @ ls` on `/tmp/kitty*` sockets
- Injects `--to unix:/path/socket` for remote control
- Inside kitty: uses env var `KITTY_LISTEN_ON`
- Requires: `allow_remote_control yes` in kitty.conf
- Pane ID captured: reads output of `kitten @ launch` via temp file

### WezTerm Special Handling
- Outside wezterm: detects via `wezterm cli list` success
- Inside: uses `WEZTERM_PANE` env var for split
- Tab mode: `wezterm cli spawn -- bash {script}`
- Split mode: requires wezterm running outside for mux

### Custom TOML Presets
Define in `~/.hcom/config.toml`:
```toml
[terminal.custom]
binary = "my-term"
open = "my-term --execute bash {script}"
close = "my-term --close {pane_id}"
pane_id_env = "MY_TERM_PANE"
```

---

## PTY Screen Reading

**Location:** `src/pty/screen.rs` (1017 lines)

### Core Component: ScreenTracker

Uses `vt100::Parser` to parse ANSI escape sequences in real-time. Maintains in-memory screen grid (rows x cols) with per-cell attributes.

### Gate Conditions Before Delivery

| Gate | Method | What it checks | Tool defaults |
|------|--------|---------------|---------------|
| Ready pattern | `is_ready()` | Configured pattern visible on screen | Claude: 5s timeout, Gemini: 60s, Codex: 5s |
| Approval waiting | `is_waiting_approval()` | OSC9 sequence detected | One-way latch, persists until user input |
| Output stability | `is_output_stable(ms)` | No PTY output for N milliseconds | 100-500ms depending on tool |
| Prompt empty | `get_*_input_text()` | No user text in input box | Tool-specific detection |
| User cooldown | `last_user_input` | No keystrokes for 500ms-3s | 500ms default |

### Tool-Specific Prompt Detection

**Claude** (`get_claude_input_text()`, lines 361-417):
- Finds `❯` prompt character with `─` borders above/below
- Uses vt100 cell-level `dim` attribute to distinguish placeholder from user input
- Returns empty string if placeholder (dim text), actual text if user typed
- User activity cooldown: 500ms

**Gemini** (`get_gemini_input_text()`, lines 430-495):
- Three border formats: old `╭` corner, new `▀` border, or dash `─` borders
- Finds ` > ` or ` * ` (YOLO mode) prompt
- Collects multi-line input until bottom border
- Placeholder hidden by ready pattern visibility

**Codex** (`get_codex_input_text()`, lines 505-540):
- Finds `›` (U+203A) prompt character
- Uses dim attribute for placeholder detection
- Falls back to ready pattern if dim check fails

### OSC9 Filtering
- Output buffer monitored for approval notifications before vt100 parsing
- Patterns: `\x1b]9;Approval requested` (tool approval), `\x1b]9;Codex wants to edit` (file edits)
- One-way latch: once set, persists until user input clears it
- Updates DB status to "blocked" for TUI visibility

---

## Text Injection Mechanism

**Location:** `src/pty/inject.rs` (160 lines)

### TCP Injection Server (InjectServer)
- Binds to `127.0.0.1:0` (random port)
- Non-blocking `accept()` on listener
- Maintains vector of active clients

### Injection Flow
1. **Command**: hcom resolves instance name + inject port from DB
2. **TCP Write**: command text sent to port (trailing LF stripped)
3. **Main Loop**: inject client handler reads data
4. **PTY Write**: `write_all(&self.pty_master, text.as_bytes())?`

### Two Message Types
- **Inject** (normal): text written directly to PTY master
- **Query** (magic prefix `\x00`): extraction command (e.g., `\x00SCREEN\n`)
  - Client removed from active pool
  - Response generated in main loop (screen dump)
  - Sent via `QueryClient::respond()`, connection closed

### UTF-8 Handling
- Primary: UTF-8 decode
- Fallback: Latin-1 (preserves all byte values)
- Strips trailing LF (echo/nc adds it), preserves CR for submit

### CLI Interface
```bash
hcom term inject luna "fix the bug" --enter    # Type text + submit
hcom term inject luna "/exit"                   # Type text only
hcom term luna                                  # View screen
```

---

## Main PTY Loop Architecture

**Location:** `src/pty/mod.rs::Proxy::run()` (lines 645-1030)

### Polling Model (epoll-like)
- Poll FDs: PTY master, stdin, inject listener, inject clients
- Poll timeout: 5-10s (debug=5s for periodic dumps, normal=10s)
- Timeout path: deliver on startup delay, debug flag check, lost terminal detection

### Data Flow

**PTY -> stdout** (lines 787-912):
1. Drain loop: read until EAGAIN
2. Short poll retry: 1ms wait for trailing fragment (coalesce frame to prevent flicker)
3. Single write: all coalesced data to stdout
4. Title filter: strips tool's OSC 0/1/2 title sequences
5. Screen update: feed raw chunks to vt100 parser
6. Delivery state update: ready/approval/input_text

**stdin -> PTY** (lines 914-937):
1. Write user input directly to PTY master
2. Update delivery state: last_user_input, clear approval

**Inject clients** (lines 946-971):
1. Read client data (in reverse order to handle removals)
2. Inject: write text to PTY master
3. Query: dump screen via TCP response

**Title OSC Updates** (lines 973-1005):
- Shared Arcs: current_name, current_status (updated by delivery thread)
- Writes only on iterations with NO PTY output (prevents interleaving)
- Guards: pending_utf8 (cross-iteration multi-byte), pending_escape (CSI/OSC/DCS)

### Signal Handling (async-safe)
- **SIGWINCH**: Update screen size, forward to child via ioctl TIOCSWINSZ
- **SIGINT**: Forward to child's process group (Ctrl-C)
- **SIGTERM/SIGHUP**: Break main loop, set EXIT_WAS_KILLED flag
- **SIGPIPE**: Ignored (revoked terminal, closed TCP)

### Ready/Delivery Startup
- Wait for ready pattern OR timeout (tool-dependent):
  - Claude/Codex: 5s timeout (pattern unreliable in accept-edits/narrow mode)
  - Gemini: 60s timeout (pattern always visible)
  - OpenCode: 5s timeout (empty ready_pattern fires immediately)
- Start delivery thread on first output if pattern detected, or on timeout
- Delivery thread bridges PTY loop <-> DB/hook system

---

## Text Filtering and Corruption Prevention

### Title Filter (TitleOscFilter)
- Stateful FSM across read boundaries
- States: Pass -> SawEsc -> SawBracket -> SawDigit(0/1/2) -> InTitle -> (ST terminator)
- Discards title content, passes all other data
- Prevents title sequences from hiding real tool output

### UTF-8 Boundary Handling (`pending_utf8_bytes()`)
- Detects incomplete multi-byte sequence at buffer end
- Returns bytes still needed (0-3)
- Defers title writes until sequence completes or timeout
- Prevents corruption when reads split characters mid-sequence

### Escape Sequence Boundary Handling (`has_pending_escape()`)
- Detects incomplete CSI/OSC/DCS at buffer end
- CSI: waits for final byte (0x40-0x7E)
- OSC/DCS: waits for BEL (0x07) or ST (ESC \)
- Prevents title writes from interleaving mid-escape

### Output Coalescing
- Drain loop collects all available PTY data before single write
- Kernel PTY buffer ~4KB, TUI frames split across reads
- Coalescing prevents flicker from partial frame writes

---

## Pane Lifecycle Management

### Spawn
```
spawn_terminal_process(argv) -> (success: bool, captured_id: String)
```
- Executes terminal command with script path
- Kitty: captures output of `kitten @ launch` via temp file at `~/.hcom/.tmp/terminal_ids/{process_id}`
- WezTerm/tmux: reads env var directly
- Stores in DB: `db.store_launch_context(instance_name, json)` with pane_id, process_id, terminal_id

### Track
DB columns in launch_context JSON: preset_name, pane_id, process_id, kitty_listen_on, terminal_id

### Close on Kill (`kill_process()`)

1. If preset has close template -> `close_terminal_pane()`:
   - Substitute placeholders ({pane_id}, {pid}, {process_id}, {id})
   - Execute: `sh -c "{close_cmd}"`
2. **SIGTERM process group** (negative PID = killpg):
   - Child is session leader via `setsid()`, so PID = process group ID
   - Kills entire subtree (child + all descendants)
3. Handles: no-op if preset missing, ESRCH (already dead), EPERM (permission denied)

### Escalation (drain_and_wait_child)
- 5s timeout for graceful SIGTERM shutdown
- After 5s: escalate to SIGKILL
- After SIGKILL: 2s more for stuck processes
- Drain PTY master during shutdown to prevent deadlock (kernel buffer full blocks child)

---

## File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `src/pty/mod.rs` | 1935 | Main PTY proxy loop, I/O forwarding, signal handling, title OSC management |
| `src/terminal.rs` | 1692 | Terminal spawning, script creation, pane close/kill, preset resolution |
| `src/pty/screen.rs` | 1017 | vt100 screen tracking, ready pattern, input box detection per tool |
| `src/pty/inject.rs` | 160 | TCP injection server, text write to PTY, query responses |
| `src/pty/terminal.rs` | 115 | Raw mode setup, signal handler registration, terminal size queries |
| `src/shared/terminal_presets.rs` | 381 | 24 preset definitions, binary detection, close command templates |
