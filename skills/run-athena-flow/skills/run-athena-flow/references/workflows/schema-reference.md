# Workflow Schema Reference

Workflows are `workflow.json` files stored in the local registry at `~/.config/athena/workflows/<name>/workflow.json`.

## Full Example

```json
{
  "name": "e2e-test-builder",
  "version": "1.0.0",
  "description": "Automatically discover and generate end-to-end tests.",
  "plugins": [
    "e2e-test-builder@lespaceman/athena-workflow-marketplace",
    "site-knowledge@lespaceman/athena-workflow-marketplace"
  ],
  "promptTemplate": "Add comprehensive Playwright E2E tests for this codebase. Begin by analyzing existing test conventions, then identify untested user flows, implement tests for each, and run them to confirm they pass.",
  "systemPromptFile": "./system-prompt.md",
  "loop": {
    "enabled": true,
    "completionMarker": "ATHENA_COMPLETE",
    "maxIterations": 10,
    "blockedMarker": "ATHENA_BLOCKED",
    "trackerPath": ".athena-tracker.json",
    "continuePrompt": "Continue from where you left off. Tracker: {trackerPath}"
  },
  "isolation": "minimal",
  "model": "claude-opus-4-5",
  "env": {
    "PLAYWRIGHT_BROWSERS_PATH": "0"
  }
}
```

## Field Reference

### `name` — `string` (required)

Unique workflow identifier. Used in `--workflow` flags and config.

### `version` — `string` (recommended)

Semver version. Shown in the header and marketplace listings.

### `description` — `string` (optional)

Human-readable description for marketplace listings.

### `plugins` — `string[]` (optional)

Plugin references auto-loaded on activation. Local paths or marketplace refs (`name@owner/repo`). Merged with config/CLI plugins.

Versioned format also supported:

```json
{
  "plugins": [
    { "ref": "my-plugin@org/repo", "version": "1.2.0" }
  ]
}
```

### `promptTemplate` — `string` (required)

Initial prompt injected as the user message to start the session. Supports `{input}` placeholder for dynamic substitution.

### `systemPromptFile` — `string` (optional)

Relative path (from workflow directory) to a markdown system prompt file.

### `loop` — `object` (optional)

Iterative execution configuration. Omit for single-run workflows.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enabled` | boolean | Yes | Whether looping is active |
| `completionMarker` | string | Yes | String the agent outputs to signal completion |
| `maxIterations` | number | Yes | Maximum iterations before stopping |
| `blockedMarker` | string | No | String the agent outputs when blocked |
| `trackerPath` | string | No | Relative path to a tracker file |
| `continuePrompt` | string | No | Prompt for iterations 2+. Supports `{trackerPath}` interpolation |

The loop runs until `completionMarker` is output, `blockedMarker` is output, or `maxIterations` is reached.

### `isolation` — `"strict" | "minimal" | "permissive"` (optional)

Session isolation preset. Upgrades the user's setting if the workflow needs more access (with a warning in the UI).

### `model` — `string` (optional)

Model override. Accepts short aliases (`"sonnet"`, `"opus"`) or full model IDs (`"claude-opus-4-5"`).

### `env` — `object` (optional)

Environment variables injected into the agent process.

```json
{
  "env": {
    "NODE_ENV": "test",
    "PLAYWRIGHT_BROWSERS_PATH": "0"
  }
}
```

### `examplePrompts` — `string[]` (optional)

Example prompts shown in the workflow picker or help output.
