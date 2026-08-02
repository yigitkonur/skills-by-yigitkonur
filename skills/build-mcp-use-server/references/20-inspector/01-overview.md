# Inspector Overview

*Read this when you want to understand how the Inspector works and how it auto-mounts in mcp-use.*

The Inspector is an interactive developer tool for testing and debugging MCP servers. It lets you connect to a server, call tools with typed inputs, inspect resources and prompts, try chat, preview MCP Apps widgets, and copy client setup commands.

## Two invocation modes

### Auto-mounted in `mcp-use dev`

When you run `npm run dev` in an mcp-use project, the Inspector is pre-built and supplied by `mcp-use`. It mounts automatically at two URLs on your local listener:

| URL | Purpose |
| --- | --- |
| `http://localhost:3000/mcp` | MCP endpoint for the server |
| `http://localhost:3000/mcp/inspector` | Inspector UI |

The default port is 3000; it may vary if that port is in use. No separate dependency or installation is needed — it ships with mcp-use.

Use `mcp-use dev --no-inspector` when you need a headless dev run without the Inspector UI.

### Standalone: `npx @mcp-use/inspector`

Run the Inspector standalone on any port without an mcp-use server:

```bash
npx @mcp-use/inspector
```

This starts the Inspector server on port 8080 (default) and opens it in your browser. The Inspector can then connect to any publicly reachable or local MCP server you provide.

Use `--port <port>` to pick a different port, and `--no-open` to skip opening the browser.

## Core workflow

1. **Connect** — Open the Inspector and add a server by URL (e.g., `http://localhost:3000/mcp`).
2. **Test tools** — Open the Tools tab, select a tool, fill the form, and run it to verify schema and response shape.
3. **Inspect resources and prompts** — Check what the server exposes in the Resources and Prompts tabs.
4. **Debug widgets** — When a tool returns an MCP Apps widget, inspect the widget data, test layout and display modes, and verify CSP (Content Security Policy) before using it in a production host.
5. **Chat** — Use the Chat tab to test how an LLM calls your tools in a conversation.
6. **Copy setup** — Use the Add to Client dropdown to install or copy setup commands for Claude Desktop, Cursor, VS Code, Claude Code, and other clients.

See `references/22-validate/01-inspector-walkthrough.md` for a guided walkthrough.
