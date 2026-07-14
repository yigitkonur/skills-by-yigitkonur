# Server vs Client vs Agent

`mcp-use` ships three distinct halves of the MCP architecture. Knowing which half you're working on tells you which skill to use.

## Server

You write a server when you have **capabilities to expose** — a database, an API wrapper, a file system, a render pipeline, anything an LLM-driven host might invoke.

- API: `import { MCPServer } from "mcp-use/server"`
- Primitives: tools, resources, prompts, MCP Apps widgets
- Transports: stdio (Claude Desktop, Cursor), Streamable HTTP (web hosts), serverless handlers
- This skill covers everything server-side.

## Client

You write a client when you have an app that **needs to call out** to MCP servers — a custom IDE plugin, a backoffice tool, a script.

- API: `import { MCPClient } from "mcp-use/client"`
- Primitives: connect/disconnect, list tools/resources/prompts, invoke them, subscribe to notifications
- Use cases: anything other than a stock MCP host (Claude Desktop, ChatGPT, Cursor) consuming MCP servers programmatically.
- Skill: **`build-mcp-use-client`** (separate skill; this skill does not cover client SDK usage).

## Agent

You write an agent when you have an LLM that should **orchestrate multiple MCP servers** — picking tools, chaining calls, planning multi-step actions.

- API: `import { MCPAgent } from "mcp-use/agent"`
- Primitives: LLM provider, tool selection, planner loop, observability
- Use cases: AI assistants that use MCP servers as a tool layer.
- Skill: **`build-mcp-use-agent`** (separate skill).

## Routing decisions

| User goal | Skill |
|---|---|
| "Build an MCP server / extend my mcp-use server / add a widget" | this skill |
| "Connect my app to an MCP server / list and call tools programmatically" | `build-mcp-use-client` |
| "Build an LLM agent that uses MCP servers as tools" | `build-mcp-use-agent` |
| "Build a server with raw `@modelcontextprotocol/sdk` (no `mcp-use`)" | `build-mcp-server-sdk-v1` or `build-mcp-server-sdk-v2` |

## Mixed cases

If the user is building both halves (e.g. an `mcp-use` server *and* a custom client that calls it), start with this skill for the server half and route to the appropriate sibling for the client half. Don't try to teach the other halves from inside this skill.

## Read next

- `07-this-skill-vs-build-mcp-use-client.md` — disambiguation when the line is fuzzy.

**Canonical doc:** https://manufact.com/docs/typescript/getting-started/welcome
