# Inspector Walkthrough

*Read this when you want to manually test an MCP server using the Inspector UI.*

Start your development server and open the Inspector at its default location.

## Quick Start

```bash
npm run dev
# Opens Inspector at http://localhost:3000/mcp/inspector
```

The Inspector auto-connects to the local MCP server. You should see:
- **Dashboard** — all available tools, prompts, and resources
- **Tools tab** — list of registered tools with input forms
- **Prompts tab** — library of prompts
- **Resources tab** — static and templated resources
- **Chat tab** — interactive testing with an LLM

## Connection Settings

Inspector → **Connection Settings** (gear icon):
- **URL**: Pre-filled with `http://localhost:3000/mcp` for auto-connected dev server
- **Transport**: HTTP (default for v2)
- **Connection mode**: Auto (tries direct first; falls back to proxy on CORS fail)

For deployed servers or tunneled endpoints, paste the full MCP URL (including `/mcp` suffix).

## Testing a Tool

1. Go to **Tools** tab
2. Click a tool name
3. Fill the input form (schema-validated in real-time)
4. Click **Call**
5. See result in **Output** panel below
6. If the tool returns a view (MCP App), preview renders inline

## Testing Resources

1. Go to **Resources** tab
2. Click a resource name
3. See content in the inspector
4. For templated resources, enter URI parameters in the form

## Testing Prompts

1. Go to **Prompts** tab
2. Select a prompt
3. View the prompt text and argument structure
4. Use **Chat** tab to test with an LLM

## Authentication Flow

When a server requires OAuth:
1. Connection enters `pending_auth` state
2. Click **Authenticate** button
3. Complete OAuth flow in browser
4. Inspector reconnects automatically
5. Bearer token cached in browser session (encrypted)

## Saving Connections

Inspector → **Add Connection** button (top-left) — saves server URL + auth + headers for reuse across browser sessions.

## Debug Panels

When a tool call returns a view:
- **props**: Structured data the widget receives
- **output**: Raw tool result (text, structured, etc.)
- **metadata**: Timestamps, cache state, host hints
- **state**: Widget state after user interaction

Use these to verify view props match your schema.

## Copy Client Setup

After testing, Inspector offers one-click copy of `mcp-use client` setup — copy the exact command to connect from CLI.
