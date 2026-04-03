# hcom Configuration System — Complete Reference

All configuration keys, TOML structure, environment variable mapping, and per-agent config.

## Configuration Layers

### Layer 1: Runtime Config (`config.rs`, 80 lines)
- Environment variables: `HCOM_DIR`, `HCOM_INSTANCE_NAME`, `HCOM_PROCESS_ID`
- Startup-only, used by router/client
- Global singleton, lazily initialized

### Layer 2: HcomConfig (`config.rs`, 1875 lines)
- TOML file + env vars with validation
- Loading priority: **CLI flag > env var > TOML file > default**
- 20 user-facing settings

## TOML File Structure

Location: `~/.hcom/config.toml`

```toml
[preferences]
timeout = 120
subagent_timeout = 300
terminal = "kitty-split"
tag = "team-alpha"
hints = "Use bun instead of npm"
notes = "Remember: this project uses Python 3.12"

[preferences.args]
claude_args = "--model claude-sonnet-4-20250514 --verbose"
gemini_args = "--model gemini-2.5-flash"
codex_args = "--model o4-mini"
opencode_args = ""

[preferences.prompts]
gemini_system_prompt = "You are a helpful coding assistant"
codex_system_prompt = "You are a Codex coding agent"

[preferences.advanced]
codex_sandbox_mode = "workspace"
auto_approve = true
auto_subscribe = "idle,collision"
name_export = "AGENT_NAME"

[relay]
id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
url = "mqtts://broker.emqx.io:8883"
token = ""
enabled = true
```

## All 20 Configuration Keys

| Key | TOML Path | Env Var | Type | Default | Description |
|-----|-----------|---------|------|---------|-------------|
| `timeout` | preferences.timeout | `HCOM_TIMEOUT` | 1-86400 | 120 | Default wait timeout (seconds) |
| `subagent_timeout` | preferences.subagent_timeout | `HCOM_SUBAGENT_TIMEOUT` | integer | 300 | Subagent keep-alive timeout |
| `terminal` | preferences.terminal | `HCOM_TERMINAL` | string | auto-detect | Terminal preset or custom command with `{script}` |
| `tag` | preferences.tag | `HCOM_TAG` | alphanumeric+hyphen | none | Default tag for launched agents |
| `hints` | preferences.hints | `HCOM_HINTS` | string | none | Hints passed to agents in bootstrap |
| `notes` | preferences.notes | `HCOM_NOTES` | string | none | Notes appended to bootstrap as ## NOTES section |
| `claude_args` | preferences.args.claude_args | `HCOM_CLAUDE_ARGS` | shell-quoted | none | Default args for Claude launches |
| `gemini_args` | preferences.args.gemini_args | `HCOM_GEMINI_ARGS` | shell-quoted | none | Default args for Gemini launches |
| `codex_args` | preferences.args.codex_args | `HCOM_CODEX_ARGS` | shell-quoted | none | Default args for Codex launches |
| `opencode_args` | preferences.args.opencode_args | `HCOM_OPENCODE_ARGS` | shell-quoted | none | Default args for OpenCode launches |
| `codex_sandbox_mode` | preferences.advanced.codex_sandbox_mode | `HCOM_CODEX_SANDBOX_MODE` | enum | workspace | workspace, untrusted, danger-full-access, none |
| `gemini_system_prompt` | preferences.prompts.gemini_system_prompt | `HCOM_GEMINI_SYSTEM_PROMPT` | string | none | System prompt for Gemini agents |
| `codex_system_prompt` | preferences.prompts.codex_system_prompt | `HCOM_CODEX_SYSTEM_PROMPT` | string | none | System prompt for Codex agents |
| `auto_approve` | preferences.advanced.auto_approve | `HCOM_AUTO_APPROVE` | boolean | tool-dependent | Auto-approve hcom commands |
| `auto_subscribe` | preferences.advanced.auto_subscribe | `HCOM_AUTO_SUBSCRIBE` | comma-sep | none | Auto-subscribe preset names |
| `name_export` | preferences.advanced.name_export | `HCOM_NAME_EXPORT` | string | none | Custom env var for instance name |
| `relay` | relay.url | TOML-only | URL | none | Relay broker URL |
| `relay_id` | relay.id | TOML-only | UUID | none | Relay group ID |
| `relay_token` | relay.token | TOML-only | string | none | Relay auth token |
| `relay_enabled` | relay.enabled | TOML-only | boolean | false | Relay enabled/disabled |

**Note:** Relay fields (`relay`, `relay_id`, `relay_token`, `relay_enabled`) are **TOML-only** -- no env var override.

## Validation Rules

| Key | Validation |
|-----|-----------|
| `timeout` | Must be 1-86400 (seconds) |
| `tag` | Alphanumeric + hyphens only |
| `terminal` | Known preset name OR custom command containing `{script}` |
| `codex_sandbox_mode` | One of: workspace, untrusted, danger-full-access, none |
| `*_args` | Validated with `shell_words::split()` (must be valid shell quoting) |
| `auto_subscribe` | Comma-separated list of known preset names |

## Per-Instance Overrides

```bash
hcom config -i luna tag "reviewer"              # Set tag for specific instance
hcom config -i luna timeout 300                 # Override timeout for luna
hcom config -i self subagent_timeout 600        # "self" = current instance
```

Per-instance overrides stored in the `instances` table columns (not TOML).

## Environment Variable Mapping

The `FIELD_TO_ENV` map converts field names to `HCOM_*` env vars:
- `timeout` -> `HCOM_TIMEOUT`
- `terminal` -> `HCOM_TERMINAL`
- `tag` -> `HCOM_TAG`
- etc.

The `TOML_KEY_MAP` converts field names to dotted TOML paths:
- `timeout` -> `preferences.timeout`
- `claude_args` -> `preferences.args.claude_args`
- `codex_sandbox_mode` -> `preferences.advanced.codex_sandbox_mode`

## Config Commands

```bash
hcom config                          # List all settings
hcom config timeout                  # Get specific key
hcom config timeout 300              # Set specific key
hcom config --edit                   # Open TOML in $EDITOR
hcom config --reset                  # Factory reset (delete config.toml)
hcom config --json                   # Export as JSON
hcom config --setup                  # Terminal setup wizard
hcom config -i luna tag "reviewer"   # Per-instance override
```

## Codex Sandbox Modes

| Mode | Flags | Description |
|------|-------|-------------|
| `workspace` | `--full-auto` + network config | Default. Full auto-approval within workspace. |
| `untrusted` | `--sandbox workspace-write` | Sandbox with write approval on untrusted commands |
| `danger-full-access` | `--dangerously-bypass-approvals-and-sandbox` | No sandbox, no approvals |
| `none` | (raw) | No hcom flags added, skips `--add-dir ~/.hcom` |

## Terminal Setup

Interactive wizard via `hcom config --setup`:
1. Detects current terminal environment
2. Lists available presets with binary availability check
3. Tests chosen preset with a script launch
4. Saves to config if successful

Custom terminal command:
```bash
hcom config terminal "my-term --execute bash {script}"
```
The `{script}` placeholder is replaced with the path to the launch script at runtime.

## Identity Export

Custom env var names for instance identification:
- `HCOM_PROCESS_ID_EXPORT`: Custom var name for process ID
- `HCOM_NAME_EXPORT`: Custom var name for instance name
- Falls back to `config.name_export` field

Example:
```bash
hcom config name_export "AGENT_NAME"
# Now launched agents have AGENT_NAME=luna in their environment
```

## File Reference

| File | Lines | Purpose |
|------|-------|---------|
| `src/config.rs` | 1875 | HcomConfig struct, loading, validation, field maps |
| `src/commands/config.rs` | 1715 | `hcom config` command, editor, wizard, JSON export |
