# `mcp-use client` + `mcp-use skills`

Two sibling surfaces: `client` is an interactive debugging harness for any MCP server you can reach; `skills` installs the `build-mcp-use-*` family of Claude/Cursor/Codex skills into your project.

---

## `mcp-use client`

### Verbatim `--help`

```
Usage: mcp-use client [options] [command]

Interactive MCP client for terminal usage

Commands:
  connect [options] <url>         Connect to an MCP server
  disconnect [options] [session]  Disconnect from a session
  sessions                        Manage CLI sessions
  tools                           Interact with MCP tools
  resources                       Interact with MCP resources
  prompts                         Interact with MCP prompts
  interactive [options]           Start interactive REPL mode
```

### Subcommand map

| Subcommand | Shape | Purpose |
|---|---|---|
| `connect <url>` | `connect [options] <url>` | Open a session to any MCP-compliant endpoint. URL can be `http(s)://host/mcp`, a Streamable HTTP endpoint, or a tunnel URL. |
| `disconnect [session]` | `disconnect [options] [session]` | Close one session id, or all sessions if omitted. |
| `sessions` | parent of `list`/`current`/`switch` style verbs | Manage persisted CLI sessions (state in `.mcp-use/sessions.json` — see `config-files/20-env-and-sessions.md`). |
| `tools` | parent: `list` / `call` | List tools on the active session and call them with JSON args. |
| `resources` | parent: `list` / `read` | Enumerate + read MCP resources. |
| `prompts` | parent: `list` / `get` | Enumerate + hydrate MCP prompts. |
| `interactive` | REPL | Open a shell that wraps all of the above with tab-completion. |

### REPL basics (`mcp-use client interactive`)

- Prompt shows the active session alias and tool count, e.g. `acme-prod [23]> `.
- Core REPL verbs (mirror the non-interactive subcommands):
  - `connect <url>` — open and switch to a new session
  - `use <session>` — switch active session
  - `tools` — list tools on the active session
  - `call <tool> <json-args>` — invoke a tool with literal JSON payload
  - `resources` / `read <uri>`
  - `prompts` / `get <name> <json-args>`
  - `disconnect` / `exit`
- History persists across REPL runs as part of `.mcp-use/sessions.json`.
- Tab-completes tool names from the current session's tool list.

### Typical flow

```bash
# 1. Connect to a local dev server
mcp-use client connect http://localhost:3000/mcp

# 2. List tools
mcp-use client tools list

# 3. Call a tool — args is the POSITIONAL 2nd argument (JSON string), not a flag
mcp-use client tools call search-users '{"q":"acme"}'

# 4. Read a resource
mcp-use client resources read ui://widget/chart

# 5. Disconnect
mcp-use client disconnect
```

Or via REPL:

```bash
mcp-use client interactive
> connect https://my-server.mcp-use.com/mcp
> tools
> call search-users {"q":"acme"}
> exit
```

### Gotchas

- Session state is **user-global**, not project-local. The CLI persists REPL sessions to `~/.mcp-use/cli-sessions.json` (verified in `cli/src/utils/session-storage.ts`: `SESSION_FILE_PATH = join(homedir(), ".mcp-use", "cli-sessions.json")`). This is a different file from the server-side `FileSystemSessionStore` artifact at `<cwd>/.mcp-use/sessions.json` documented in `config-files/20-env-and-sessions.md` — they are different stores owned by different code paths.
- `connect` against a server requiring OAuth will route through the browser auth flow before the session is usable.
- The REPL does not auto-reconnect when a server drops; re-run `connect` after network hiccups.

---

## `mcp-use skills`

### Verbatim `--help`

```
Usage: mcp-use skills [options] [command]

Commands:
  add [options]      Install mcp-use skills for AI agents (Cursor, Claude Code, Codex)
  install [options]  Alias for 'add'
```

### `add` / `install`

```
Usage: mcp-use skills install [options]

Options:
  -p, --path <path>  Path to project directory
```

- Installs the mcp-use skill bundle (the `build-mcp-use-*` family) into the target project.
- Detects the target agent from file markers in the project root and installs to the agent's skills dir. Verified mapping from `cli/src/commands/skills.ts`:
  - `cursor` → installs to `.cursor/skills/`
  - `claude-code` → installs to `.claude/skills/`
  - `codex` → installs to `.agent/skills/` (note: marker file is `.codex/` but install target is `.agent/skills/`)
- Defaults to `cwd` when `-p` is omitted.
- Live log line confirms: `"Downloading from github.com/mcp-use/mcp-use → .cursor/skills, .claude/skills, .agent/skills"`.

### Use cases

1. **Install into the current project (all detected agents)**
   ```bash
   mcp-use skills add
   ```
2. **Install into a specific project path**
   ```bash
   mcp-use skills install -p ~/projects/my-mcp-server
   ```
3. **Re-run to refresh — idempotent; overwrites updated skill files**
   ```bash
   mcp-use skills add
   ```

### Gotchas

- `install` is a literal alias for `add`. No behaviour difference; pick whichever verb your team uses.
- If no supported agent directory is detected, the command prompts you to pick one to scaffold.
- Skill installs do **not** touch `.mcp-use/`; they land under the agent-specific directory (`.claude/skills/...`, `.cursor/rules/...`, etc.).
