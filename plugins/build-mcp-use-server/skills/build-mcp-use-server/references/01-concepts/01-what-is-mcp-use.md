# What is mcp-use

*Read this when you need to understand what mcp-use v2 provides as a framework over the raw MCP SDK.*

`mcp-use` v2 is a TypeScript framework for building MCP (Model Context Protocol) servers. It wraps the official `@modelcontextprotocol/sdk` (v2.0.0) with a declarative API and production-ready integrations:

- **Declarative server API** — `MCPServer` constructor, `server.tool()`, `server.resource()`, `server.prompt()` with definition-first signatures
- **Transports** — Streamable HTTP only (Web-standard Fetch API), optimized for edge and Node.js runtimes
- **OAuth 2.1** — Six providers (Clerk, Auth0, WorkOS, Supabase, Keycloak, Better Auth) + custom provider factory
- **Stateless request model** — Fresh MCP context per request; request-state codec for multi-round elicitation
- **MCP Apps** — React components and hooks in `mcp-use/react` for building tool views in ChatGPT and other hosts
- **CLI** — `mcp-use@beta` v4.x with dev, build, deploy, type generation (generates `mcp-env.d.ts`)
- **Inspector** — Live MCP testing, RPC logging, CSP debugging (automounts at `/mcp/inspector` during dev)

## What this skill covers

The **server-side** half of mcp-use: writing tools, resources, prompts, MCP Apps views, OAuth, handling requests, and deploying. It includes everything needed to ship an MCP server from local dev to production endpoints.

The **client SDK** and agent orchestration live in `build-mcp-use-client` (sister skill).

## What mcp-use is not

- **Not a fork of the SDK** — it imports the official MCP SDK as a dependency
- **Not an LLM** — tools call out to your own logic, APIs, databases
- **Not a UI framework** — MCP Apps is a runtime for hosts that render views (ChatGPT, Claude Desktop)

## Key v2 changes from v1

- **No sessions by default** — stateless per-request; application manages state
- **No stdio** — Streamable HTTP only
- **No server-side sampling** — model generates; server provides deterministic tools
- **OAuth Proxy removed** — use external authorization servers
- **No response helpers (deprecated)** — return raw MCP envelopes

## Read next

- `02-server-vs-client-vs-agent.md` — boundaries and which skill covers what
- `03-transports-overview.md` — HTTP endpoint structure
- `04-stateless-model-and-request-state.md` — how requests flow without session affinity
- `06-mcp-apps-and-views-terminology.md` — vocabulary for Views cluster
