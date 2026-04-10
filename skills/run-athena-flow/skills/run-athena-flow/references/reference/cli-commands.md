# CLI Command Reference

## Commands

### `athena-flow` / `athena`

Start the Athena runtime with the terminal UI.

```bash
athena-flow [options]
```

### `athena-flow setup`

Re-run the setup wizard (theme, harness, workflow).

```bash
athena-flow setup
```

### `athena-flow sessions`

Interactive session picker.

```bash
athena-flow sessions
```

### `athena-flow resume`

Resume a previous session.

```bash
athena-flow resume              # most recent
athena-flow resume <session-id> # specific session
```

### `athena-flow exec`

Non-interactive mode for CI and scripts.

```bash
athena-flow exec "<prompt>" [options]
```

### `athena workflow install`

Install a workflow from a marketplace.

```bash
athena workflow install <ref> --name <local-name>
```

### `athena workflow list`

List installed workflows.

```bash
athena workflow list
```

### `athena workflow search`

Search marketplace for workflows.

```bash
athena workflow search <query>
```

### `athena workflow remove`

Remove an installed workflow.

```bash
athena workflow remove <name>
```

### `athena workflow upgrade`

Upgrade a workflow to the latest version.

```bash
athena workflow upgrade <name>
```

### `athena workflow use`

Set a workflow as the active default.

```bash
athena workflow use <name>
```

### `athena marketplace add`

Add a marketplace source.

```bash
athena marketplace add <owner/repo>
```

### `athena marketplace remove`

Remove a marketplace source.

```bash
athena marketplace remove <owner/repo>
```

### `athena marketplace list`

List configured marketplace sources.

```bash
athena marketplace list
```

### `athena telemetry`

Manage telemetry settings.

```bash
athena telemetry enable
athena telemetry disable
athena telemetry status
```

## General Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--project-dir=<path>` | Project directory | cwd |
| `--plugin=<path>` | Load plugin directory (repeatable) | — |
| `--isolation=<preset>` | `strict` / `minimal` / `permissive` | `strict` |
| `--theme=<theme>` | `dark` / `light` / `high-contrast` | `dark` |
| `--workflow=<name>` | Activate installed workflow | — |
| `--verbose` | Extra detail in event feed | off |
| `--ascii` | ASCII-safe glyphs | off |

## Exec Mode Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--json` | JSONL events to stdout | off |
| `--output-last-message=<path>` | Write final message to file | — |
| `--ephemeral` | No session persistence | off |
| `--on-permission=<policy>` | `allow` / `deny` / `fail` | `fail` |
| `--on-question=<policy>` | `empty` / `fail` | `fail` |
| `--timeout-ms=<ms>` | Hard timeout | — |
| `--continue[=<id>]` | Resume session | — |

## Exit Codes (exec mode)

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Permission request with `fail` policy |
| 3 | Question with `fail` policy |
| 4 | Timeout exceeded |
| 5 | Agent error |
| 6 | Session not found |
| 7 | Hook registration failure |

## In-Session Slash Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `/help` | `/h`, `/?` | List commands |
| `/clear` | `/cls` | Clear history |
| `/quit` | `/q`, `/exit` | Exit |
| `/stats` | `/s` | Session statistics |
| `/context` | `/ctx` | Token breakdown |
| `/sessions` | — | Session picker |
| `/tasks` | `/todo` | Task list |
| `/setup` | — | Re-run wizard |
| `/telemetry` | — | Telemetry status |
| `/workflow` | — | Change workflow |

Plugin skills with `user-invocable: true` also appear as slash commands.

## Isolation Presets

| Preset | MCP Servers | Allowed Tools |
|--------|-------------|---------------|
| `strict` | Blocked | `Read`, `Edit`, `Glob`, `Grep`, `Bash`, `Write` |
| `minimal` | Project servers | Above + `WebSearch`, `WebFetch`, `Task`, `Agent`, `Skill`, `mcp__*` |
| `permissive` | Project servers | Above + `NotebookEdit` |
