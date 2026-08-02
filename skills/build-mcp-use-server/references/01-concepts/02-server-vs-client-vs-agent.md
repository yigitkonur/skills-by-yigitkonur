# Server vs Client vs Agent

*Read this when you need to understand the scope boundaries of the three build-mcp-use-* skills.*

## Three domains

| Domain | Package | Skill | You build |
|--------|---------|-------|-----------|
| **Server** | `mcp-use` | `build-mcp-use-server` | MCP endpoints: tools, resources, prompts, OAuth |
| **Client** | `@mcp-use/client` | `build-mcp-use-client` | MCP connections: call tools, read resources, list prompts |
| **Agent** | `@mcp-use/agent` | `build-mcp-use-agent` | Multi-step workflows: planning, tool-calling loops, reasoning |

## Server (this skill)

**What:** MCPServer instance listening at an HTTP endpoint; serves tools, resources, prompts; handles OAuth; may render views in ChatGPT.

**Scope:**
- `MCPServer` constructor and configuration
- Tool registration with Zod schemas
- Resource and prompt registration
- OAuth provider setup
- MCP Apps views
- Transport selection (Node.js, Next.js, Cloudflare, Vercel, etc.)
- Deployment to cloud platforms

**Not included:**
- How to *use* a server from a client application (see `build-mcp-use-client`)
- Multi-server orchestration or aggregation (see `build-mcp-use-agent`)

## Client (sister skill)

**What:** Code that calls a remote MCP server: initializes a session, lists tools, calls tools, reads resources.

**Scope:**
- `@mcp-use/client` for connecting to servers
- Calling tools and handling responses
- Subscriptions and notifications
- Error handling and retry logic

**Not included:**
- How to *build* a server (this skill)
- Agent-level orchestration across multiple servers

## Agent (sister skill)

**What:** High-level automation that reasons, plans, and calls tools across one or more MCP servers.

**Scope:**
- `@mcp-use/agent` for multi-step workflows
- LLM-driven planning and tool selection
- Context management across rounds
- Fallback and error recovery

**Not included:**
- How to build individual servers
- How to connect to individual servers (that's client scope)

## Cross-domain interactions

A single application can be all three:
- **Server** is a tool provider (this skill)
- **Client** connects to a downstream server
- **Agent** orchestrates the flow

Example: Your server calls another MCP server's tools via a client SDK, coordinated by agent logic.
