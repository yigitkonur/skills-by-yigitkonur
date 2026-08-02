# This Skill vs build-mcp-use-client

*Read this when you're building both a server and a client, or you're unsure which skill applies.*

## Clear-cut boundaries

| Goal | Skill |
|------|-------|
| Write tools, resources, prompts with `server.tool(...)`, `server.resource(...)`, `server.prompt(...)` | **this skill** |
| Configure OAuth, CORS, basePath, host validation | **this skill** |
| Deploy to Node, Next.js, Vercel, Cloudflare, Deno, Cloud Run, Railway | **this skill** |
| Build MCP Apps views (React components) that render tool results | **this skill** (`18-mcp-apps/`) |
| Connect an app to a server: list/call tools, read resources, subscribe | `build-mcp-use-client` |
| Build an LLM agent that plans and orchestrates multiple servers | `build-mcp-use-agent` |
| Use raw `@modelcontextprotocol/sdk` directly (no framework) | `build-mcp-server-sdk-v2` |

## Fuzzy boundaries

### "I'm building a view"

If it's a React component at `views/<name>/view.tsx` that your server hosts and ChatGPT renders → **this skill, `18-mcp-apps/`**.

If it's a standalone React app that *consumes* widgets from a remote MCP server → probably `build-mcp-use-client`, but check if your app is also an MCP server (both roles).

### "I'm building both a server and a client"

Start in **this skill** for the server side. Once the server ships, route to **`build-mcp-use-client`** for client-side work (connection, tool calling, state management on the client).

They're independent skills because the server and client are independent codebases.

### "I have a Next.js app that acts as a server AND calls another server"

- **Server logic** (tool registration, OAuth setup) → this skill + `19-nextjs-drop-in/`
- **Client logic** (calling downstream MCP servers) → `build-mcp-use-client` (or copy code examples into same monorepo)

Both can coexist in one Next.js app.

## This skill does NOT cover

- `@mcp-use/client` SDK usage (other than test clients in examples)
- LLM agent orchestration or multi-server planning
- Custom host development (embedding MCP in an Electron app, for example)
- Raw SDK usage (use `build-mcp-server-sdk-v2` instead)

## Cross-reference conventions

When this skill references `build-mcp-use-client`, it uses the canonical sister name. When the client skill references this skill, it uses `build-mcp-use-server`.
