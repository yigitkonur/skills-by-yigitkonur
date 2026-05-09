# Companion Toolchain Decision Tree

Pick the smallest companion route that can finish the job. This file decides which skill or non-MCP path should take over after `optimize-agentic-mcp` has established the audit finding or architecture sketch.

## Decision Tree

```
START: What needs to happen after the MCP audit or architecture sketch?
|
+-- Implement a TypeScript server using mcp-use conventions?
|   +-- YES --> build-mcp-use-server
|       Use for tools, schemas, responses, auth, sessions, transports,
|       MCP Apps widgets, ChatGPT Apps, Inspector, and deploy mechanics.
|
+-- Enforce TypeScript layer boundaries in an mcp-use server?
|   +-- YES --> apply-clean-mcp-architecture
|       Use for folder layout, dependency direction, composition root,
|       TypeScript quality, and layer-boundary refactors.
|
+-- Implement or maintain raw official SDK v1?
|   +-- YES --> build-mcp-server-sdk-v1
|       Use for @modelcontextprotocol/sdk v1.x, single-package imports,
|       Zod v3/raw-shape patterns, stdio, Streamable HTTP, OAuth, and v1 APIs.
|
+-- Implement or maintain raw official SDK v2?
|   +-- YES --> build-mcp-server-sdk-v2
|       Use only after checking current npm/docs state and confirming the user
|       accepts alpha/pre-release risk when v2 is still alpha.
|
+-- Need live verification against a running server?
|   +-- YES --> test-by-mcpc-cli
|       Use for repeatable stdio/Streamable HTTP smoke checks, JSON scripting,
|       schema inspection, grep, and post-fix verification.
|
+-- Is the real problem CLI agent-readiness?
|   +-- YES --> optimize-agentic-cli
|       Use when stdout/stderr, JSON contracts, exit codes, non-interactive
|       flags, or repairable CLI workflows are the core surface.
|
+-- Does an existing CLI or SDK already solve the workflow?
|   +-- YES --> no MCP / use existing CLI
|       Prefer CLI when shell composition, files, pipes, local trust, or an
|       already mature command contract dominates the work.
|
+-- Is the missing value static workflow knowledge rather than a runtime tool?
|   +-- YES --> use an agent skill
|       Prefer a skill when the agent needs procedure, standards, prompts, or
|       domain context, not authenticated runtime access.
|
+-- Otherwise
    +-- Keep `optimize-agentic-mcp` in control
        Continue the audit/architecture pass until the route is clear.
```

## Positive Routing Rules

| Route | Pick when | Do not use for |
|---|---|---|
| `build-mcp-use-server` | `mcp-use/server` imports, HTTP-first TypeScript servers, widgets/apps, OAuth helpers | General agent-readiness audits |
| `build-mcp-server-sdk-v1` | `@modelcontextprotocol/sdk` v1 single-package servers | v2 split-package imports |
| `build-mcp-server-sdk-v2` | `@modelcontextprotocol/server` v2 split-package servers where alpha risk is accepted | Production-default raw SDK work when v2 is still alpha |
| `test-by-mcpc-cli` | Running stdio/Streamable HTTP smoke checks and JSON-scripted validation | Static design review without a running server |
| `apply-clean-mcp-architecture` | TypeScript `mcp-use` layer-boundary or quality issues | Raw SDK servers without `mcp-use` |
| `optimize-agentic-cli` | CLI command contracts and machine-readable execution surfaces | MCP protocol, schema, auth, or transport design |
| No MCP / existing CLI | Mature CLI/SDK already exposes the workflow cleanly | Multi-user auth, approval, or typed tool discovery needs |
| Agent skill | Runtime access is unnecessary; the agent needs workflow knowledge | Live external state, auth, or per-call data access |

## Output Line

When you choose a companion route, include one line in the audit or architecture output:

`Companion route: <skill-or-path> because <reason>; validation: <test-by-mcpc-cli | MCP Inspector | unit/integration test | manual check>.`
