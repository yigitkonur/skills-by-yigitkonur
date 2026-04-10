# Configuration

Athena uses JSON config files. CLI flags always take final precedence.

## Config Files

| Scope | Path |
|-------|------|
| Global | `~/.config/athena/config.json` |
| Project | `{projectDir}/.athena/config.json` |

Both are optional. Without them, Athena uses defaults.

## Merge Order

```
Global config → Project config → CLI flags
```

Later sources win. CLI flags have the highest precedence.

## Full Config Schema

```json
{
  "plugins": ["/path/to/plugin", "name@owner/repo"],
  "additionalDirectories": ["/path/to/allow"],
  "workflow": "e2e-test-builder",
  "theme": "dark",
  "model": "sonnet",
  "harness": "claude-code",
  "telemetry": { "enabled": true },
  "setupComplete": true,
  "deviceId": "uuid-v4",
  "workflowMarketplaceSources": ["lespaceman/athena-workflow-marketplace"],
  "workflowSelections": {}
}
```

## Config Fields

### `plugins` — `string[]`

Plugin references. Paths or marketplace refs (`name@owner/repo`).

```json
{
  "plugins": [
    "./plugins/custom-commands",
    "e2e-test-builder@lespaceman/athena-workflow-marketplace"
  ]
}
```

### `additionalDirectories` — `string[]`

Filesystem paths the agent is granted access to. Passed as `--add-dir` flags to Claude Code.

```json
{
  "additionalDirectories": ["/data/fixtures", "/home/user/shared-schemas"]
}
```

### `workflow` — `string`

Workflow name to activate. Must be installed first.

### `theme` — `"dark" | "light" | "high-contrast"`

Terminal UI theme. Default: `dark`.

### `model` — `string`

Model alias (`"sonnet"`, `"opus"`) or full model ID (`"claude-opus-4-5"`).

### `harness` — `"claude-code" | "openai-codex" | "opencode"`

Agent harness. Default: `claude-code`. Both `claude-code` and `openai-codex` are production-ready.

### `telemetry` — `object`

Telemetry settings. Anonymous opt-out via PostHog.

```json
{ "telemetry": { "enabled": false } }
```

Or disable via CLI: `athena telemetry disable`
Or via env: `ATHENA_TELEMETRY_DISABLED=1`

### `workflowMarketplaceSources` — `string[]`

List of marketplace repos to search for workflows.

### `setupComplete` — `boolean`

Whether the setup wizard has been completed.

## All CLI Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--project-dir=<path>` | Project directory | Current directory |
| `--plugin=<path>` | Load a plugin (repeatable) | — |
| `--isolation=<preset>` | `strict`, `minimal`, or `permissive` | `strict` |
| `--theme=<theme>` | `dark`, `light`, or `high-contrast` | `dark` |
| `--workflow=<name>` | Activate a workflow | — |
| `--verbose` | Extra detail in the event feed | off |
| `--ascii` | ASCII-safe glyphs | off |
| `--json` | JSONL output (exec mode) | off |
| `--output-last-message=<path>` | Save final message (exec mode) | — |
| `--ephemeral` | Skip session persistence (exec mode) | off |
| `--on-permission=<policy>` | `allow`, `deny`, `fail` (exec mode) | `fail` |
| `--on-question=<policy>` | `empty`, `fail` (exec mode) | `fail` |
| `--timeout-ms=<ms>` | Hard timeout (exec mode) | — |
| `--continue[=<id>]` | Resume session (exec mode) | — |

## Editing

Config files are plain JSON. Changes take effect on next startup — no hot-reload.

To update interactively:

```bash
athena-flow setup
```

## Debug Logging

```bash
ATHENA_DEBUG=1 athena-flow
```

Enables verbose debug output from hook registration and the socket server.
