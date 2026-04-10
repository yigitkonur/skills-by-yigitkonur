# What is Athena Flow

Athena Flow is a workflow runtime for AI coding agents. It currently supports Claude Code and OpenAI Codex. It observes every tool call, permission decision, and agent action in real time — and gives you the ability to control what happens next.

## The Mental Model

Five concepts, layered:

```
Harness → Runtime → Workflow → Plugin → Hook
```

**Harness** — The agent runtime Athena wraps. Today that's Claude Code and OpenAI Codex. Each harness has its own integration mechanism but Athena normalizes the event stream so workflows and plugins work identically across both.

**Runtime** — Athena's core process. It receives hook events over a Unix Domain Socket, persists them to SQLite, evaluates isolation policies, and renders the terminal UI.

**Workflow** — A reusable session definition: prompt template + plugins + loop config + isolation level. Workflows encode what works so you can repeat it.

**Plugin** — A directory that adds skills (slash commands) and MCP servers to your sessions. Plugins are loaded by workflows or by config.

**Hook** — A lifecycle event fired by the agent runtime (tool use, permission request, session start, etc.). Athena receives and processes the event stream from whichever harness is active.

## How It Connects

**Claude Code** uses hook-forwarding over a Unix Domain Socket:

```
Claude Code → athena-hook-forwarder (stdin) → Unix Domain Socket → Athena runtime
```

**OpenAI Codex** uses a JSON-RPC app-server protocol:

```
Codex → codex-app-server (JSON-RPC) → Athena runtime
```

Both produce the same normalized `RuntimeEvent` stream. Workflows, plugins, and the UI work identically regardless of which harness is active.

## What You Get

- **Live event feed** — every tool call, permission prompt, and result, structured and color-coded
- **Session persistence** — every session saved to SQLite, resumable any time
- **Plugin system** — slash commands and MCP servers loaded from plugin directories
- **Workflow orchestration** — reusable JSON definitions with prompt templates and loop logic
- **Isolation presets** — `strict`, `minimal`, or `permissive` control over agent capabilities

## Ecosystem

- **Package:** `@athenaflow/cli` on npm (MIT license)
- **Runtime:** TypeScript + React/Ink for TUI, better-sqlite3 for persistence
- **Build:** tsup (ESM only), Vitest for testing
- **Repo:** github.com/lespaceman/athena-flow-cli
- **Marketplace:** github.com/lespaceman/athena-workflow-marketplace
- **Browser MCP:** github.com/lespaceman/agent-web-interface
- **MCP Registry:** github.com/lespaceman/athena-mcp-registry
