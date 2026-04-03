# hcom Tool Integration Layer — Complete Reference

How hcom abstracts across 4 AI tools: Claude Code, Codex, Gemini CLI, and OpenCode.

## Tool Enum and Abstraction

**File:** `src/tool.rs`

```rust
pub enum Tool {
    Claude,
    Gemini,
    Codex,
    OpenCode,
    Adhoc,        // Non-launched, ad-hoc participant
}
```

**Ready patterns per tool:**
- Claude: `"? for shortcuts"`
- Codex: `"›"` (U+203A)
- Gemini: `"Type your message"`
- OpenCode: `"ctrl+p commands"`
- Adhoc: empty (immediate ready)

The launcher also defines `LaunchTool` enum adding `ClaudePty` for the PTY wrapper distinction.

## Per-Tool Argument Handling

### Shared Infrastructure (`src/tools/args_common.rs`)

- **FlagValue enum**: `Single(String)` or `List(Vec<String>)` for repeatable flags
- **SourceType**: `Cli`, `Env`, or `None` (tracks where args originated)
- **Flag utilities**: `extract_flag_name_from_token()`, `looks_like_flag()`, `toggle_flag()`, `set_value_flag()`, `remove_flag_with_value()`
- **Shell escaping**: `shell_quote()` and `shell_split()` for env serialization
- **Levenshtein matching**: `find_close_match()` for typo suggestions

### Claude Args (`src/hooks/claude_args.rs`)

- Optional-value flags: `--resume`, `--debug` (can stand alone OR take a value)
- Value flags: `--model`, `--system-prompt`, `--session-id`
- Background switches: `-p`, `--print` (headless indicators)
- Fork switch: `--fork-session`
- Boolean flags: `--verbose`, `--continue`, `--ide`
- Returns `ClaudeArgsSpec` with parsed tokens, flag values, subcommand detection

### Codex Args (`src/tools/codex_args.rs`)

- **Case-sensitive flags**: `-C` (--cd) vs `-c` (--config) are DIFFERENT
- Subcommands: `exec`, `resume`, `fork`, `review`, `mcp`, `sandbox`, `debug`
- Repeatable flags: `-c`, `--config`, `--enable`, `--disable`, `-i`, `--image`, `--add-dir`
- Sandbox flag grouping: If CLI has ANY sandbox flag, ALL sandbox flags from env are stripped
- Value flags with special handling: `--sandbox workspace-write` syntax
- Returns `CodexArgsSpec` with exec/json detection and positional tracking

### Gemini Args (`src/tools/gemini_args.rs`)

- Optional-value flags: `--resume`, `-r` (with aliases)
- Repeatable flags: `-e`, `--extensions`, `--include-directories`, `--allowed-mcp-server-names`
- Boolean flags: `--debug`, `--sandbox`, `--yolo`, `--list-extensions`
- Session ID detection: Positional args that look like session IDs
- Subcommands: `mcp`, `extensions`, `hooks`, `skills`

### OpenCode Preprocessing (`src/tools/opencode_preprocessing.rs`)

- Minimal argument parsing (relies on OpenCode's native CLI)
- Sets `OPENCODE_PERMISSION` env: `{"bash":{"hcom *":"allow"}}` (auto-approve hcom)
- Sets `HCOM_NAME` env for plugin diagnostics

## Per-Tool Launch Mechanics

**Entry point:** `src/launcher.rs::launch()`

### Claude (2 launch modes)

**Non-PTY Mode (`LaunchTool::Claude`):**
- Direct invocation: `claude <args>`
- Supports background/headless via `-p` (print) flag
- For background: creates log file at `~/.hcom/.tmp/logs/background_<timestamp>_<rand>.log`
- Tracks log files and PID for orphan detection
- Command built by `build_claude_command()` with shell-quoted args

**PTY Mode (`LaunchTool::ClaudePty`):**
- Wraps `hcom pty claude [args...]` in bash script
- Script path: `~/.hcom/.tmp/launch/<tool>_<instance>_<pid>_<rand>.sh`
- Sets `HCOM_PTY_MODE=1` in env
- Terminal preset selection via `terminal::launch_terminal()`
- Used when not in background mode and on Unix

### Codex

- Always PTY-based: `hcom pty codex [args...]`
- **Preprocessing pipeline:**
  1. Inject sandbox flags based on `HCOM_CODEX_SANDBOX_MODE`
  2. Ensure `--add-dir ~/.hcom` for DB writes
  3. Add bootstrap text via `-c developer_instructions=<bootstrap>`
- Bootstrap: `bootstrap::get_bootstrap()` content injected at launch time
- Sandbox mode mapping:
  - `"workspace"`: `--full-auto` + network access config
  - `"untrusted"`: `--sandbox workspace-write` + approval on untrusted
  - `"danger-full-access"`: `--dangerously-bypass-approvals-and-sandbox`
  - `"none"`: Raw codex (skips --add-dir)

### Gemini

- Always PTY-based: `hcom pty gemini [args...]`
- System prompt written to `~/.hcom/system-prompts/gemini.md`
- Env var set: `GEMINI_SYSTEM_MD=<path>`
- Terminal launch with effective run-here detection

### OpenCode

- Always PTY-based: `hcom pty opencode [args...]`
- Preprocessing: `preprocess_opencode_env()` sets:
  - `OPENCODE_PERMISSION`: `{"bash":{"hcom *":"allow"}}` (auto-approve)
  - `HCOM_NAME`: instance name for plugin diagnostics
- Plugin binding executed via TypeScript plugin (`src/opencode_plugin/hcom.ts`)

## Session Binding Differences

### Identity Environment Variables

Every launched instance receives:
```
HCOM_PROCESS_ID=<uuid>          # Unique process identifier
HCOM_LAUNCHED=1                  # Mark as hcom-launched
HCOM_LAUNCHED_BY=<launcher>      # Who launched this
HCOM_LAUNCH_BATCH_ID=<batch_id>  # Batch coordination
HCOM_LAUNCH_EVENT_ID=<event_id>  # Last event at launch time
HCOM_DIR=~/.hcom                 # Data directory
HCOM_TAG=<tag>                   # Optional tag
```

### Per-Tool Binding

| Tool | When binding happens | How |
|------|---------------------|-----|
| Claude | SessionStart hook (immediate) | session_id from hook payload |
| Codex | First agent-turn-complete (5-10s) | session_id from codex-notify event |
| Gemini | BeforeAgent hook (immediate) | session_id derived from hook |
| OpenCode | Plugin binding ceremony (2-3s) | TCP: `hcom opencode-start --session-id <sid>` |

### Transcript Path Derivation

| Tool | How transcript is found |
|------|------------------------|
| Claude | Hook payload provides transcript path directly |
| Codex | Glob search: `$CODEX_HOME/sessions/rollout-*-{thread-id}.jsonl` |
| Gemini | Search `~/.gemini/chats/` for `rollout-{session_id}.json` |
| OpenCode | OpenCode's SQLite database path passed as transcript |

## Resume and Fork Mechanics

### Resume (`src/commands/resume.rs`)

1. Load stopped instance snapshot from DB (last life event)
2. Extract: session_id, tool, launch_args, tag
3. Merge original args with new CLI args (new args override)
4. Tool-specific resume arg builders:
   - Claude: `--resume <session-id>`
   - Codex: `resume` subcommand (positional)
   - Gemini: `-r <session-id>` or `--resume <session-id>`
   - OpenCode: `--fork` flag

### Fork (`src/commands/fork.rs`)

- Wrapper around resume with `fork=true`
- Launches with `--fork-session` (Claude) or tool-specific fork syntax
- Uses current working directory (not snapshot directory)
- Sets `HCOM_IS_FORK=1` in env for Claude

### Argument Merging Strategy

1. Load original launch args from instance snapshot
2. Parse new CLI args with tool-specific parser
3. Merge with smart precedence:
   - New args override env args
   - Non-repeatable flags: new value wins
   - Repeatable flags: combine both
   - Subcommands: new subcommand wins
   - Positionals: new positionals win

## OpenCode Plugin Architecture

**File:** `src/opencode_plugin/hcom.ts`

TypeScript plugin acting as dual-purpose adapter:

### Binding Ceremony

1. Detect `session.created` or `permission.asked` event
2. Call `hcom opencode-start --session-id <sid>` to establish identity
3. Start TCP notify server on localhost (ephemeral port)
4. Register port: `--notify-port <port>`
5. Plugin state: instance name, session ID, bootstrap text

### Message Delivery

- Lazy loading: checks `HCOM_LAUNCHED` env before hooking
- TCP notify: instant wake when hcom sends messages
- HTTP fetch: periodic reconciliation (5s fallback)
- Deferred ACK: messages marked pending until confirmed delivered

### Status Tracking

- Reports to hcom: `hcom opencode-status --status <listening|active|blocked>`
- Blocks on approval: `permission.asked` -> `--context approval` -> `--detail <permission>`
- Grace period: 5s reconciliation timer

## Hook Installation Validation

### Strict Gate Pattern (`ensure_hooks_installed()`)

Before any launch, verify hooks are ready:
- Claude: Verify hooks installed -> auto-install -> fail if cannot install
- Gemini: Check version >= required -> verify hooks -> auto-install
- Codex: Verify hooks -> auto-install
- OpenCode: Verify plugin installed -> auto-install

Uninstalled or old-version tools: launch refused with error message.

## Tool Marker Clearing

Prevents parent tool identity leakage to child tools:

Cleared before launch:
- `CLAUDECODE`, `GEMINI_CLI`, `CODEX_SANDBOX`, `OPENCODE`
- All `HCOM_IDENTITY_VARS` (prevents inherited process IDs)
- Tool-specific session markers

## Summary: Tool Integration Comparison

| Aspect | Claude | Codex | Gemini | OpenCode |
|--------|--------|-------|--------|----------|
| Launch mode | PTY or non-PTY | Always PTY | Always PTY | Always PTY |
| Bootstrap | Hook injection | -c developer_instructions | System prompt file | Plugin binding |
| Session binding | Immediate | 5-10s delayed | Immediate | 2-3s via TCP |
| Message delivery | Hook output | PTY injection | Hook output | Plugin endpoint |
| Args parser | claude_args.rs | codex_args.rs | gemini_args.rs | Minimal |
| Sandbox | N/A | 4 modes | Optional | N/A |
| Resume | --resume sid | resume subcommand | -r sid | --fork |
| Background | -p flag | PTY only | PTY only | PTY only |
| Subagent support | Yes (Task) | No | No | No |

## File Reference

| File | Purpose |
|------|---------|
| `src/tool.rs` | Tool enum, ready patterns, FromStr |
| `src/launcher.rs` | Central launch(), tool dispatch, env setup |
| `src/tools/args_common.rs` | Shared arg parsing utilities |
| `src/hooks/claude_args.rs` | Claude argument parser |
| `src/tools/codex_args.rs` | Codex argument parser |
| `src/tools/gemini_args.rs` | Gemini argument parser |
| `src/tools/opencode_preprocessing.rs` | OpenCode env preprocessing |
| `src/commands/resume.rs` | Resume mechanics |
| `src/commands/fork.rs` | Fork mechanics |
| `src/opencode_plugin/hcom.ts` | OpenCode TypeScript plugin |
