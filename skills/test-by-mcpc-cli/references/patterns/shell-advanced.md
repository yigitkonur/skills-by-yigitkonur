# Shell advanced reference

## Starting the shell

```bash
mcpc @session shell
```

This is the only supported entry point. The `@session` prefix is required — `shell` is a sub-command of an existing named session, not a standalone mode. A direct URL target (e.g., `mcpc https://mcp.apify.com shell`) does not enable notifications (explained below).

---

## How the REPL works internally

The shell is implemented in `src/cli/shell.ts` using Node.js `readline.createInterface`. Key properties of the interface:

- **Prompt string**: `mcpc(@session)>` rendered in cyan via `chalk`.
- **History pre-loaded**: On startup, `loadHistory()` reads `~/.mcpc/shell-history`, splits on newlines, and passes the entries to readline in reverse order (most-recent-first), which is the order readline expects for up-arrow navigation.
- **History size**: `historySize: 1000` is passed to readline, matching the `HISTORY_MAX_COMMANDS` constant.
- **Terminal mode**: `terminal: true` is set explicitly, enabling readline's line-editing features (cursor movement, kill-line, etc.) even when stdin is a TTY.
- **Each command**: The `line` event fires, adds the line to the in-memory history array (deduplicating consecutive identical entries), then calls `executeCommand()`. After the command resolves, `rl.prompt()` is called again — this is a sequential loop, not concurrent.
- **Ctrl+C (`SIGINT`)**: Prints a blank line and re-issues the prompt. Does not exit.
- **Ctrl+D / `close` event**: Sets `ctx.running = false`, prints `Goodbye!`, then the `finally` block in `startShell()` calls `saveHistory()` and closes the notification client.

### Startup sequence

1. Load history from disk.
2. Call `logTarget()` — prints `[Using session: @name]`.
3. Print the welcome banner.
4. Call `setupNotificationListener()` — opens a second IPC connection to the bridge (session targets only).
5. Enter `shellLoop()` — readline takes over.

### Shutdown sequence

1. `exit`/`quit` command or Ctrl+D sets `ctx.running = false`.
2. readline `close` event fires.
3. `finally` block saves history (trimmed to the last 1000 entries) and closes the notification client.

---

## All available commands

### Shell-only built-ins

| Command        | Effect                                      |
|----------------|---------------------------------------------|
| `help`         | Print the command reference table           |
| `exit`         | Terminate the shell cleanly                 |
| `quit`         | Alias for `exit`                            |
| `clear`        | Call `console.clear()` (equivalent to Ctrl+L) |

### MCP commands (short aliases accepted)

| Command                              | Notes                                              |
|--------------------------------------|----------------------------------------------------|
| `tools` / `tools-list`               | List all tools from the server                     |
| `tools-get <name>`                   | Show schema and description for a single tool      |
| `tools-call <name> [key:=value ...]` | Call a tool; supports `--task` and `--detach` flags |
| `resources` / `resources-list`       | List all resources                                 |
| `resources-read <uri>`               | Fetch and print a resource by URI                  |
| `resources-templates-list`           | List URI templates                                 |
| `prompts` / `prompts-list`           | List all prompts                                   |
| `prompts-get <name> [key:=value ...]`| Render a prompt with arguments                     |
| `logging-set-level <level>`          | Set server-side log level (debug…emergency)        |
| `ping`                               | Round-trip latency check                           |
| `tasks-list`                         | List async tasks                                   |
| `tasks-get <taskId>`                 | Get status/result of a task                        |
| `tasks-cancel <taskId>`              | Cancel a running task                              |

All MCP commands run in `outputMode: 'human'` and suppress the `[Using session: …]` prefix (`hideTarget: true`), keeping output compact.

### Command aliases

`tools` and `tools-list` are identical. Same for `resources`/`resources-list` and `prompts`/`prompts-list`. These aliases exist only in the shell dispatcher; the CLI does not have them.

---

## Shell-only features not available in CLI mode

1. **Persistent notification listener** — a live push stream from the server, visible as timestamped lines between prompts. Not available in one-shot CLI mode.
2. **Built-in history navigation** — readline history across the entire session (and persisted across sessions). The CLI has no stateful history.
3. **`clear`** — no equivalent CLI command.
4. **`help` without a subcommand** — in CLI mode, `mcpc --help` is Commander.js-driven; inside the shell `help` shows a curated MCP-focused command table.
5. **Short aliases** (`tools`, `resources`, `prompts`) — accepted only inside the shell dispatcher.
6. **Easter egg** — typing `shell` inside the shell (see below).

---

## Notification listener

When the target starts with `@` (a named session), `setupNotificationListener()` creates a **second, separate IPC connection** to the bridge process:

```
Shell process
├── Command connection  →  bridge socket  →  MCP server (request/response)
└── Notification connection  →  bridge socket  →  MCP server (push stream)
```

The notification client registers a handler on the `'notification'` event. Notifications arrive asynchronously and are printed between prompts — they do not interrupt a running command but may interleave with output if a command is slow.

If the session target does not start with `@` (e.g., a raw URL), `setupNotificationListener()` returns immediately without error. The shell still works for commands.

If creating the notification client throws, the error is silently swallowed. The shell continues without notifications rather than failing.

### Notification types and colors

| `notification.method`       | Color  | Message format                                      |
|-----------------------------|--------|-----------------------------------------------------|
| `tools/list_changed`        | yellow | `[HH:MM:SS] Server tools list changed`             |
| `resources/list_changed`    | yellow | `[HH:MM:SS] Server resources list changed`         |
| `prompts/list_changed`      | yellow | `[HH:MM:SS] Server prompts list changed`           |
| `resources/updated`         | yellow | `[HH:MM:SS] Resource updated`                      |
| `progress`                  | cyan   | `[HH:MM:SS] Progress: <JSON params>`               |
| `logging/message`           | gray   | `[HH:MM:SS] Server log: <JSON params>`             |
| _(anything else)_           | dim    | `[HH:MM:SS] Notification: <method>`                |

The timestamp is `new Date().toLocaleTimeString()` — locale-dependent, typically `HH:MM:SS AM/PM` or `HH:MM:SS` depending on system locale.

Note: all list-change notifications share the same yellow color. There is no green or blue in the current implementation — only yellow, cyan, gray, and dim.

---

## History management

- **File**: `~/.mcpc/shell-history` (plain text, one command per line).
- **Max entries**: 1000 (`HISTORY_MAX_COMMANDS`). On save, `history.slice(-1000)` is written.
- **Deduplication**: Consecutive identical commands are not added (`addToHistory` checks the last entry).
- **Empty lines**: Skipped — not added to history and not saved.
- **Load errors**: Silently ignored; the shell starts with an empty history.
- **Save errors**: Silently ignored; existing history is not corrupted.
- **The `~/.mcpc/` directory** is created with `mkdir({ recursive: true })` before each save, so the file is safe to delete manually.

To clear history manually:

```bash
rm ~/.mcpc/shell-history
```

To inspect it:

```bash
cat ~/.mcpc/shell-history
```

---

## Quote-aware argument parsing (`shell-parser.ts`)

`parseShellCommand(line)` splits a raw input line into `{ command, args }`. The algorithm is a single-pass character scanner:

1. Tracks whether the parser is inside a quoted region (`inQuote`, `quoteChar`).
2. Opening `"` or `'` when not already inside a quote sets `inQuote = true`.
3. The matching closing quote clears `inQuote`. The quotes themselves are **consumed** (stripped from the token).
4. Spaces outside quotes flush the current token into `parts`.
5. Any other character is appended to `current`.
6. After the loop, any remaining `current` is pushed.

Consequences:

- `tools-call search query:="hello world"` → args `["query:=hello world"]` (space preserved inside quotes).
- `tools-call search query:='it'"'"'s fine'` — shell-style quote-splicing is NOT supported; the parser handles a single quote context at a time.
- Quotes are not nested: `"foo 'bar'"` treats the single quotes as literal characters inside the double-quoted region.
- No backslash escaping: `\"` inside a double-quoted string does not escape the quote — it ends the quoted region.
- The first token is always the command; everything after is `args`.

This parser is intentionally minimal. For complex JSON arguments with internal spaces, use single or double quotes:

```
tools-call search config:='{"key":"hello world"}'
```

---

## Easter egg

Typing `shell` inside the shell triggers a random message from a pool of eight responses, displayed in yellow:

```
🐚 Shell-ception! You're already in a shell.
🪆 It's shells all the way down...
🎭 Ha, nice try!
🔄 Yo dawg, I heard you like shells...
🌀 Recursion limit reached. Just kidding.
🐢 A shell inside a shell? How very turtles-all-the-way-down of you.
🎪 Welcome to shell² — same great shell, same great location!
🪞 *shell stares back at you*
```

The message is selected with `Math.floor(Math.random() * 8)`, so distribution is uniform but not deterministic. The shell does not actually recurse.

---

## Productivity tips

### Readline keyboard shortcuts

Because the shell uses `readline` in terminal mode, all standard readline (Emacs-mode) shortcuts work:

| Shortcut       | Action                              |
|----------------|-------------------------------------|
| `Ctrl+A`       | Move cursor to beginning of line    |
| `Ctrl+E`       | Move cursor to end of line          |
| `Ctrl+U`       | Kill from cursor to start of line   |
| `Ctrl+K`       | Kill from cursor to end of line     |
| `Ctrl+W`       | Kill previous word                  |
| `Ctrl+Y`       | Yank (paste) killed text            |
| `Ctrl+R`       | Reverse incremental history search  |
| `Up` / `Down`  | Navigate history                    |
| `Ctrl+L`       | Clear screen (same as `clear`)      |
| `Ctrl+C`       | Cancel current line, re-prompt      |
| `Ctrl+D`       | EOF — exit the shell                |

`Ctrl+R` is particularly useful for long `tools-call` invocations with embedded JSON.

### tmux integration

Run the shell in a named tmux window to keep it live across disconnections:

```bash
tmux new-window -n mcpc-shell "mcpc @session shell"
```

To send a command from another pane without switching:

```bash
tmux send-keys -t mcpc-shell "tools-list" Enter
```

Notifications appear in the tmux window passively, so you can monitor server events without polling.

### Watching notifications passively

Leave the shell open in a background terminal (or tmux pane) connected to a session. When the MCP server pushes `tools/list_changed` or `resources/updated`, the timestamped notification line appears automatically. This is the only way to observe push notifications without writing custom code.

---

## Scripting the shell

The shell is not designed for unattended scripting — it uses readline in terminal mode, which behaves differently when stdin is not a TTY. For scripting, use the one-shot CLI form:

```bash
# Preferred: direct CLI commands (no shell needed)
mcpc @session tools-list --json
mcpc @session tools-call my-tool key:=value
```

If you want to drive multiple commands sequentially in a script, chain them:

```bash
mcpc @session tools-list --json | jq '.[] | .name' | while read -r tool; do
  mcpc @session tools-get "$tool" --json
done
```

Piping into the shell process itself is unreliable because readline detects non-TTY stdin and may behave unexpectedly. Use the CLI commands directly in scripts.

For stdin-based tool argument passing (supported in CLI mode):

```bash
echo '{"query":"hello","limit":10}' | mcpc @session tools-call search
```

This bypasses the shell entirely and is the correct approach for automated workflows.
