---
name: run-athena-flow
description: "Use skill if you are driving the Athena Flow CLI for AI workflow orchestration, plugin development, session management, or CI integration with Claude Code or OpenAI Codex harnesses."
---

# Athena Flow CLI

Athena Flow is a workflow runtime for AI coding agents. It wraps Claude Code and OpenAI Codex, normalizing their event streams into a unified runtime with structured workflows, real-time observability, session persistence, and a plugin system.

## Mental Model

Five concepts, layered:

```
Harness → Runtime → Workflow → Plugin → Hook
```

- **Harness** — The agent runtime Athena wraps (Claude Code or OpenAI Codex)
- **Runtime** — Athena's core: receives events over UDS/JSON-RPC, persists to SQLite, renders UI
- **Workflow** — Reusable session definition: prompt + plugins + loop config + isolation
- **Plugin** — Directory adding skills (slash commands) and MCP servers
- **Hook** — Lifecycle event from the agent runtime (tool use, permissions, session start, etc.)

## Quick Start

```bash
npm install -g @athenaflow/cli
cd /your/project
athena
```

Three binaries installed: `athena`, `athena-flow`, `athena-hook-forwarder`.

Prerequisites: Node.js 20+, git, Claude Code (`claude`) and/or OpenAI Codex (`codex` v0.37.0+) on PATH.

Platform: macOS and Linux. Windows via WSL only (Unix Domain Socket requirement).

→ [references/getting-started/installation.md](references/getting-started/installation.md)
→ [references/getting-started/first-workflow.md](references/getting-started/first-workflow.md)

## Architecture

**Claude Code** — Hook-forwarding over Unix Domain Socket:

```
Claude Code → athena-hook-forwarder (stdin) → UDS NDJSON → Athena runtime
```

**OpenAI Codex** — JSON-RPC app-server protocol:

```
Codex → codex-app-server (JSON-RPC) → Athena runtime
```

Both produce normalized `RuntimeEvent` objects. The UI, plugins, and workflows work identically regardless of harness.

→ [references/getting-started/what-is-athena.md](references/getting-started/what-is-athena.md)
→ [references/concepts/harnesses.md](references/concepts/harnesses.md)

## Core Concepts

| Concept | When to read | Reference |
|---------|-------------|-----------|
| Harnesses | Understanding Claude Code vs Codex integration | [references/concepts/harnesses.md](references/concepts/harnesses.md) |
| Hooks & Permissions | Working with event lifecycle, blocking decisions | [references/concepts/hooks-and-permissions.md](references/concepts/hooks-and-permissions.md) |
| Sessions & Persistence | Managing SQLite sessions, resume, ephemeral | [references/concepts/sessions-and-persistence.md](references/concepts/sessions-and-persistence.md) |
| Runtime Events | Processing the 28 event types in the event stream | [references/concepts/runtime-events.md](references/concepts/runtime-events.md) |
| Isolation Presets | Configuring strict/minimal/permissive tool access | [references/concepts/isolation-presets.md](references/concepts/isolation-presets.md) |

## Workflows

Workflows define the shape of an agent session — prompt template, plugins, loop config, isolation level, model override.

```json
{
  "name": "my-workflow",
  "promptTemplate": "Do the thing.",
  "plugins": ["plugin@owner/repo"],
  "loop": { "enabled": true, "completionMarker": "ATHENA_COMPLETE", "maxIterations": 10 },
  "isolation": "minimal"
}
```

| Topic | Reference |
|-------|-----------|
| Workflow overview | [references/workflows/overview.md](references/workflows/overview.md) |
| Schema reference (all fields) | [references/workflows/schema-reference.md](references/workflows/schema-reference.md) |
| Loop configuration & tracker files | [references/workflows/loop-config.md](references/workflows/loop-config.md) |
| Marketplace install & publish | [references/workflows/marketplace.md](references/workflows/marketplace.md) |

## Plugins

Plugins add slash commands (skills) and MCP servers to sessions.

```
my-plugin/
  .claude-plugin/plugin.json    # manifest (required)
  skills/<name>/SKILL.md        # skill definitions
  .mcp.json                     # MCP server config (optional)
  workflow.json                 # auto-discovered workflow (optional)
```

| Topic | Reference |
|-------|-----------|
| Plugin system overview | [references/plugins/overview.md](references/plugins/overview.md) |
| Writing a plugin step-by-step | [references/plugins/writing-a-plugin.md](references/plugins/writing-a-plugin.md) |
| SKILL.md frontmatter fields | [references/plugins/skill-frontmatter.md](references/plugins/skill-frontmatter.md) |
| MCP server config & merging | [references/plugins/mcp-servers.md](references/plugins/mcp-servers.md) |
| agent-web-interface browser MCP | [references/plugins/agent-web-interface.md](references/plugins/agent-web-interface.md) |

## Usage Modes

| Mode | Command | Reference |
|------|---------|-----------|
| Interactive (TUI) | `athena` | [references/usage/interactive-mode.md](references/usage/interactive-mode.md) |
| CI / Headless | `athena-flow exec "<prompt>"` | [references/usage/ci-and-exec-mode.md](references/usage/ci-and-exec-mode.md) |
| Session management | `athena-flow sessions` / `resume` | [references/usage/session-management.md](references/usage/session-management.md) |
| Configuration | `~/.config/athena/config.json` | [references/usage/configuration.md](references/usage/configuration.md) |

## Recipes

| Recipe | Reference |
|--------|-----------|
| E2E Testing with Playwright | [references/recipes/e2e-testing.md](references/recipes/e2e-testing.md) |
| Custom Workflow from Scratch | [references/recipes/custom-workflow.md](references/recipes/custom-workflow.md) |
| Multi-Harness (Claude Code + Codex) | [references/recipes/multi-harness.md](references/recipes/multi-harness.md) |

## CLI Quick Reference

```bash
athena                                    # Interactive session
athena-flow setup                         # Re-run setup wizard
athena-flow sessions                      # Browse sessions
athena-flow resume [<session-id>]         # Resume session
athena-flow exec "<prompt>" [flags]       # Headless CI mode
athena workflow install <ref> --name <n>  # Install workflow
athena workflow list                      # List installed workflows
```

→ Full CLI reference: [references/reference/cli-commands.md](references/reference/cli-commands.md)
→ Hook event reference: [references/reference/hook-event-reference.md](references/reference/hook-event-reference.md)
→ Troubleshooting: [references/reference/troubleshooting.md](references/reference/troubleshooting.md)

## Common Patterns

### Install and run a marketplace workflow

```bash
athena workflow install e2e-test-builder@lespaceman/athena-workflow-marketplace --name e2e-test-builder
athena-flow --workflow=e2e-test-builder
```

### Run in CI with GitHub Actions

```yaml
- run: |
    npx @athenaflow/cli exec "run all tests" \
      --json --on-permission=deny --on-question=empty \
      --timeout-ms=300000 --ephemeral
```

### Resume a previous session

```bash
athena-flow resume                # most recent
athena-flow resume <session-id>   # specific session
```

### Load a local plugin

```bash
athena-flow --plugin=./my-plugin
```

### Switch harness to Codex

```json
{ "harness": "openai-codex" }
```

### Change isolation level

```bash
athena-flow --isolation=permissive
```

## Source Code Architecture

For contributing or deep debugging of the TypeScript codebase:

| Topic | Reference |
|-------|-----------|
| Source directory layout | [references/architecture/source-layout.md](references/architecture/source-layout.md) |
| Harness adapter internals | [references/architecture/harness-adapters.md](references/architecture/harness-adapters.md) |
| Feed system & observability | [references/architecture/feed-system.md](references/architecture/feed-system.md) |
| Workflow engine internals | [references/architecture/workflow-engine.md](references/architecture/workflow-engine.md) |

## Key Facts

- **Package:** `@athenaflow/cli` on npm (MIT license)
- **Runtime:** TypeScript + React/Ink for TUI, better-sqlite3 for persistence
- **Harnesses:** Claude Code (production), OpenAI Codex (production), opencode (planned)
- **Repo:** [github.com/lespaceman/athena-flow-cli](https://github.com/lespaceman/athena-flow-cli)
- **Marketplace:** [github.com/lespaceman/athena-workflow-marketplace](https://github.com/lespaceman/athena-workflow-marketplace)
- **Browser MCP:** [github.com/lespaceman/agent-web-interface](https://github.com/lespaceman/agent-web-interface)
