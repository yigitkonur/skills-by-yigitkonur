# Research Summary — build-mcp-sdk

## Research goal

Build a new skill for the official `@modelcontextprotocol/sdk` TypeScript SDK covering server construction with tools, resources, prompts, transports, auth, and deployment.

## Search keywords used

- `model context protocol typescript sdk mcp server client official`
- `modelcontextprotocol typescript-sdk official sdk build mcp tools resources prompts transport`
- `mcp server builder typescript zod schema tool definition handler`

## Downloaded corpus (7 skills)

| Source | Owner/Repo | Status |
|---|---|---|
| mcp-integration | anthropics/claude-code | Downloaded, 7 files |
| mcp-builder | tazomatalax/context-engineering | Downloaded, 10 files |
| mcp-sdk-typescript-bootstrapper | a5c-ai/babysitter | Downloaded, 2 files |
| create-mcp-app | sammcj/agentic-coding | Downloaded, 1 file |
| mcp-developer | trotsky1997/my-claude-agent-skills | Downloaded, 4 files |
| mcp-builder | direktly/agent-skills | Downloaded, 4 files |
| mcp-builder | vudovn/antigravity-kit | Downloaded, 1 file |

## Shortlisted candidates

| Source | Focus | Verdict |
|---|---|---|
| tazomatalax/mcp-builder | Full MCP dev (Python+TS), 4-phase workflow, evaluation harness | **Inherit:** phased workflow, tool annotations, Zod patterns. **Avoid:** 969-line TS reference (bloated) |
| a5c-ai/mcp-sdk-typescript-bootstrapper | TypeScript SDK scaffolding, Zod-first | **Inherit:** Zod dual-use, modular registration. **Avoid:** incomplete utility scaffolding |
| anthropics/claude-code/mcp-integration | Plugin config (.mcp.json), server type matrix | **Inherit:** selection matrix format, security DO/DON'T. **Avoid:** config-only scope |
| trotsky1997/mcp-developer | Python templates, comprehensive error handling | **Inherit:** error handling patterns, quick reference format. **Avoid:** Python-only, old API |

## Key finding

No existing skill deeply covers the official `@modelcontextprotocol/sdk` v1.x TypeScript SDK with current APIs (`registerTool`, `registerResource`, `registerPrompt`, `StreamableHTTPServerTransport`). All downloaded skills either:
- Use the `mcp-use` wrapper library
- Focus on Python/FastMCP
- Use deprecated SDK APIs (`tool()`, `Server` class, `SSEServerTransport`)
- Are configuration-focused rather than code-building

## Primary source

Official MCP TypeScript SDK v1.29.0 (released 2026-03-30):
- GitHub: https://github.com/modelcontextprotocol/typescript-sdk
- npm: @modelcontextprotocol/sdk
- Protocol version: 2025-11-25

## Synthesis strategy

1. Use the official SDK source code as the ground truth for all API signatures
2. Inherit the behavioral flow pattern from `build-mcp-use-server` (detect → branch → build → validate)
3. Inherit phased workflow concept from tazomatalax for reference file organization
4. Inherit error handling patterns from trotsky1997 and production patterns from tazomatalax
5. Original contribution: comprehensive coverage of `registerTool`/`registerResource`/`registerPrompt` APIs, `StreamableHTTPServerTransport`, and current OAuth middleware — none of which are documented in any downloaded skill
