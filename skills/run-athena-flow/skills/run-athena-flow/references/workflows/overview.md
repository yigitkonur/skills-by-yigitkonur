# Workflows Overview

A workflow defines the shape of an agent session — what the agent should do, with which prompt, using which plugins, under which isolation level, and whether to loop.

## What a Workflow Bundles

| Component | Purpose |
|-----------|---------|
| `promptTemplate` | Initial prompt injected into the session |
| `systemPromptFile` | Markdown file used as the system prompt |
| `plugins[]` | Plugin references auto-loaded on activation |
| `loop` | Iterative execution config (completion markers, max iterations) |
| `isolation` | Permission preset for the session |
| `model` | Model override |
| `env` | Environment variables for the agent process |

## Activating a Workflow

Install first (see Marketplace), then activate:

```bash
athena-flow --workflow=e2e-test-builder
```

Or set it in your project config:

```json
{
  "workflow": "e2e-test-builder"
}
```

When a workflow activates, it:

1. Auto-loads its declared `plugins[]`
2. Applies its `isolation` preset (upgrading from yours if needed, with a warning)
3. Injects `promptTemplate` and `systemPromptFile`
4. Runs loop logic if `loop.enabled`

## Plugin Bundles

Workflows declare plugin dependencies in `plugins[]`:

```json
{
  "plugins": [
    "e2e-test-builder@lespaceman/athena-workflow-marketplace",
    "site-knowledge@lespaceman/athena-workflow-marketplace"
  ]
}
```

These are resolved exactly like `--plugin` flags. Duplicates with config/CLI plugins are deduplicated.

### Plugin Load Order

1. Workflow `plugins[]`
2. Global config `plugins[]`
3. Project config `plugins[]`
4. `--plugin` CLI flags

Later entries win on name conflicts.

## Workflow Discovery

If a loaded plugin directory contains a `workflow.json` at its root, Athena auto-discovers it. If exactly one workflow is discovered and no `--workflow` flag is set, it activates automatically. Multiple discovered workflows require an explicit `--workflow` selection.

## Workflow Storage

Installed workflows live at:

```
~/.config/athena/workflows/<name>/workflow.json
```

A `source.json` file alongside it tracks provenance (marketplace source, install time).

## Built-in Workflow

Athena includes a built-in "default" workflow for general long-horizon tasks. It uses a tracker file system where the agent creates and maintains a `task-tracker.md` with checkboxes, status updates, and completion markers.
