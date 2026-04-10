# Interactive Mode

Run `athena` to start the terminal UI — the primary observability surface for your agent sessions.

## Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│ ATHENA v0.2.3 | ⠙ working        claude-sonnet | tools:7 | ████░ | ● │  ← Header
├──────────────────────────────────────────────────────────────────────┤
│  09:41:02 tool.pre     claude  Read          src/Header.tsx          │
│  09:41:03 tool.post    claude  Read          2.1kb                   │  ← Event feed
│  09:41:05 perm.req     athena  Write         src/Header.tsx → ...    │
├──────────────────────────────────────────────────────────────────────┤
│  input>                                                              │  ← Input bar
└──────────────────────────────────────────────────────────────────────┘
```

### Header Elements

| Element | Description |
|---------|-------------|
| Version | `ATHENA v0.2.3` |
| State label | `idle` / `working` / `waiting for input` / `error` |
| Model name | e.g., `claude-sonnet` |
| Tool count | Active tools available |
| Context bar | Green → amber → red (context window usage) |
| Socket status | `●` dot — connected/disconnected |

### Event Feed Columns

| Column | Description |
|--------|-------------|
| TIME | `HH:MM:SS` wall clock |
| EVENT | `tool.pre`, `tool.post`, `tool.failure`, `perm.req`, `perm.decision`, `agent.msg`, etc. |
| ACTOR | Source (`claude`, `codex`, `athena`). Duplicate adjacent actors shown as `·` |
| TOOL | Tool name (`Read`, `Write`, `Bash`, MCP tools) |
| DETAILS | Human-readable summary |

### Input Bar

Enter prompts, `/slash-commands`, `:command-mode`, or `/search`.

## Navigation

| Key | Action |
|-----|--------|
| `↑`/`↓` | Move cursor through event feed |
| `PageUp`/`PageDown` | Page scroll |
| `Home`/`End` | Jump to top/tail |
| `Enter` / `Ctrl+→` | Expand/collapse event entry |
| `Tab` | Cycle focus: feed → input → todo |
| `/` | Enter search mode |
| `:` | Enter command mode |
| `Ctrl+T` | Toggle todo panel |
| `Ctrl+/` | Cycle hints bar |
| `Escape` | Interrupt agent |
| `n`/`N` (in search) | Next/previous match |
| `Ctrl+L` (in search) | Clear search |
| `q` or `Esc` (in expanded view) | Close expanded view |

## Command Mode (`:` prefix)

| Command | Action |
|---------|--------|
| `:todo` | Toggle todo panel |
| `:todo add [p0\|p1\|p2] <text>` | Add todo item with priority |
| `:run list` | Show run overlay |
| `:run <needle>` | Filter to matching runs |
| `:tail` | Jump to tail of feed |
| `:jump <needle>` | Jump to first match |
| `:errors` | Toggle errors-only filter |

## Slash Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `/help` | `/h`, `/?` | List all commands |
| `/clear` | `/cls` | Clear history |
| `/quit` | `/q`, `/exit` | Exit Athena |
| `/stats` | `/s` | Session statistics |
| `/context` | `/ctx` | Token breakdown |
| `/sessions` | — | Session picker |
| `/tasks` | `/todo` | Task list |
| `/setup` | — | Re-run setup wizard |
| `/telemetry` | — | Telemetry status |
| `/workflow` | — | Change active workflow |

Plugin skills with `user-invocable: true` also appear as slash commands.

## Themes

| Theme | For | Command |
|-------|-----|---------|
| `dark` | Default. Dark terminal backgrounds. | `--theme=dark` |
| `light` | Light terminal backgrounds. | `--theme=light` |
| `high-contrast` | Accessibility / bright environments. | `--theme=high-contrast` |

## Verbose Mode

```bash
athena-flow --verbose
```

Enables additional detail in feed rows — fuller payloads and context information hidden by default.

## ASCII Mode

```bash
athena-flow --ascii
```

Switches all UI glyphs to ASCII-safe equivalents for limited terminals.
