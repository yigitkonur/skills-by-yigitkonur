# This skill vs neighbors

When you're not sure which mcp-use skill applies, decide by what the user is **building**, not what they're talking about.

## Decision table

| The user wants to… | Skill |
|---|---|
| Write `server.tool(...)`, `server.resource(...)`, `server.prompt(...)`, `server.uiResource(...)` | **this skill** |
| Add OAuth to a server, configure CORS, choose a session store, deploy a server | **this skill** |
| Build an MCP Apps widget, an interactive React UI that renders inside ChatGPT or another host | **this skill** (`18-mcp-apps/`) |
| Connect a custom app to an existing MCP server: list tools, call tools, subscribe to resources | `build-mcp-use-client` |
| Build an LLM agent that picks among MCP servers and orchestrates calls | `build-mcp-use-agent` |
| Use the raw `@modelcontextprotocol/sdk` directly (no `mcp-use`) | `build-mcp-server-sdk-v1` (single-package SDK) or `build-mcp-server-sdk-v2` (split-package SDK) |

## Fuzzy cases

### "I'm building a widget"

If they mean a React UI that an MCP server hosts and a ChatGPT/MCP Apps client renders → **this skill, cluster 18**.

If they mean a client that *consumes* widgets from a server → that's still client-side rendering work, but the rendering is provided by `mcp-use/react`. The widget runtime is shared. The **server** part (registering the widget, defining its tool, declaring CSP) is this skill. The **client** part (mounting the React tree, providing host context) belongs in either this skill (if the client is a stock host with built-in support) or `build-mcp-use-client` (if they're hand-rolling a host).

### "I'm building both a server and a client"

Start in this skill for the server. Switch to `build-mcp-use-client` once the server is shipped.

### "I'm using `MCPAgent` to call my own server"

Server build → this skill. Agent build → `build-mcp-use-agent`. Both can ship from the same monorepo.

## What this skill does NOT cover

- Writing `MCPClient` code (other than what's needed to test a server).
- Writing `MCPAgent` planner loops.
- Choosing an LLM provider.
- Front-end frameworks for hosting MCP UIs outside of the MCP Apps widget runtime.

## Sibling skill changes

The legacy skill `build-mcp-use-apps-widgets` was merged into this skill. Cluster `18-mcp-apps/` carries everything that was in `build-mcp-use-apps-widgets`. If you find a reference to `build-mcp-use-apps-widgets` in another skill, update it to `build-mcp-use-server` (or to `build-mcp-use-server/skills/build-mcp-use-server/references/18-mcp-apps/` if it pointed at a specific file).

**Canonical doc:** https://manufact.com/docs/typescript/getting-started/welcome
