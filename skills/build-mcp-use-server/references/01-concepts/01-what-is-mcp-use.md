# What is mcp-use

`mcp-use` is a TypeScript framework for building MCP (Model Context Protocol) servers, clients, and agents. It sits on top of `@modelcontextprotocol/sdk` and provides:

- A declarative server API (`MCPServer`, `server.tool`, `server.resource`, `server.prompt`, `server.uiResource`).
- Built-in transports (stdio, Streamable HTTP, serverless handlers) with sensible defaults.
- Session management with pluggable stores (memory, filesystem, Redis).
- OAuth 2.1 with DCR-direct support for 7 providers plus a proxy escape hatch.
- React hooks and components for MCP Apps widgets (`useWidget`, `useCallTool`, `McpUseProvider`).
- A CLI (`@mcp-use/cli`) with HMR, type generation, deploy, and org management.
- An Inspector for live testing, RPC logging, CSP debugging.

## What this skill covers

The **server-side** half of mcp-use plus everything you need to ship MCP Apps widgets that render in ChatGPT and other MCP-compatible hosts:

- writing tools with Zod schemas
- exposing resources and prompts
- registering MCP Apps widgets
- choosing transports
- running OAuth
- managing sessions
- emitting notifications
- debugging with the Inspector
- deploying

The client SDK and `MCPAgent` orchestration live in sibling skills (see `07-this-skill-vs-build-mcp-use-client.md`).

## What mcp-use is not

- It is **not** a fork of `@modelcontextprotocol/sdk` — it imports and extends the official SDK.
- It is **not** an LLM provider — tools call out to your own logic, your own APIs, your own database.
- It is **not** a UI framework — but it does ship a React widget runtime (MCP Apps) for hosts that render widgets in-conversation.

## Read next

- `02-server-vs-client-vs-agent.md` — how the three sides relate.
- `03-transports-overview.md` — how clients reach servers.
- `06-mcp-apps-vs-widgets-terminology.md` — the vocabulary you'll need before reading `18-mcp-apps/`.

**Canonical doc:** https://manufact.com/docs/typescript/getting-started/welcome
