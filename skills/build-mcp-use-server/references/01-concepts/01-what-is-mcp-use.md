# What is mcp-use

*Read this when you need to understand what mcp-use v2 provides as a framework over the raw MCP SDK.*

`mcp-use` v2 is a TypeScript framework for building MCP (Model Context Protocol) servers. The `mcp-use` npm package (root import, `beta` dist-tag `2.0.0-beta.66`) wraps the official MCP SDK — not a single `@modelcontextprotocol/sdk` package, but the split v2 SDK packages `@modelcontextprotocol/{client,core,server}` (each pinned to `2.0.0`) plus `@modelcontextprotocol/ext-apps` — with a declarative API and production-ready integrations:

- **Declarative server API** — `MCPServer` constructor, `server.tool()`, `server.resource()`, `server.prompt()` with definition-first signatures
- **Transports** — Streamable HTTP only (Web-standard Fetch API), optimized for edge and Node.js runtimes
- **OAuth 2.1** — Six providers (Clerk, Auth0, WorkOS, Supabase, Keycloak, Better Auth) + custom provider factory
- **Stateless request model** — Fresh MCP context per request; request-state codec for multi-round `input_required` flows (form/URL elicitation)
- **MCP Apps** — React components and hooks in `mcp-use/react` for building tool views in ChatGPT and other hosts
- **CLI** — `@mcp-use/cli` (currently `4.0.0-beta.15`, installed transitively by `mcp-use`) with `dev`, `build`, `start`, `deploy`, `typecheck`, `generate-types` (writes `.mcp-use/tool-registry.d.ts`), and a `client` subcommand
- **Inspector** — Live MCP testing UI (`@mcp-use/inspector`), automounts at `/mcp/inspector` during `mcp-use dev`

## What this skill covers

The **server-side** half of mcp-use: writing tools, resources, prompts, MCP Apps views, OAuth, handling requests, and deploying. It includes everything needed to ship an MCP server from local dev to production endpoints.

The **client SDK** and agent orchestration live in `build-mcp-use-client` (sister skill).

## What mcp-use is not

- **Not a fork of the SDK** — it imports the official MCP SDK as a dependency
- **Not an LLM** — tools call out to your own logic, APIs, databases
- **Not a UI framework** — MCP Apps is a runtime for hosts that render views (ChatGPT, Claude Desktop)

## Key v2 changes from v1

- **No sessions by default** — stateless per-request; no shipped session store; application manages state
- **No stdio** — Streamable HTTP only; SSE transport is not served
- **No server-side sampling or roots** — `ctx.sample()` does not exist; model generates, server provides deterministic tools
- **OAuth Proxy removed** — no server-side proxy factory; use external authorization servers directly
- **Response helpers deprecated, not removed** — `mcp-use` still exports them from the root for migration, but prefer raw `CallToolResult`/`ReadResourceResult`/`GetPromptResult` envelopes

## Read next

- `02-server-vs-client-vs-agent.md` — boundaries and which skill covers what
- `03-transports-overview.md` — HTTP endpoint structure
- `04-stateless-model-and-request-state.md` — how requests flow without session affinity
- `05-mcp-spec-version-history.md` — protocol revision vs SDK version vs framework version, kept separate
- `06-mcp-apps-and-views-terminology.md` — vocabulary for Views cluster
