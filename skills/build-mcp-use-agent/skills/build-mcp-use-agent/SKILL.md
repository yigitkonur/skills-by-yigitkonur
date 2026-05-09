---
name: build-mcp-use-agent
description: Use skill if you are building or auditing TypeScript mcp-use MCPAgent code where an LLM picks and orchestrates MCP tools via run, stream, or streamEvents.
---

# Build MCP Use Agent

Build or audit TypeScript `MCPAgent` code from the `mcp-use` package — the LLM-driven loop where a model chooses, calls, and chains MCP tools across one or more servers.

This SKILL.md is a routing spine. Load-bearing rules and the minimal runnable path live here; deep detail lives in `references/`.

## When to use this skill

Trigger on any of these:

- *Imports `MCPAgent` from `mcp-use` and calls `agent.run({ prompt })`, `agent.stream(...)`, `agent.streamEvents(...)`, or `agent.prettyStreamEvents(...)`.*
- *Wires an LLM (LangChain `ChatModel` or `"provider/model"` shorthand) into an agent loop that must select tools at runtime.*
- *Builds a Next.js / Express / serverless handler whose body is a `MCPAgent` invocation against one or more MCP servers.*
- *Adds streaming, structured output (Zod), memory, server-manager, code mode, observability (Langfuse), or production hardening to an existing `MCPAgent`.*
- *Debugging an agent that loops, stalls, hits `maxSteps`, leaks sessions, or returns wrong-shaped output.*
- *Picks a model/provider for an `MCPAgent` (OpenAI, Anthropic, Google, Groq, custom LangChain adapter) or migrates between them.*

### Do NOT use this skill for

- *Pure deterministic `MCPClient` work — listing tools, manually calling a known tool, reading resources, sessions, React hooks, `mcp-use/browser`, `npx mcp-use client`. Route to `build-mcp-use-client`.*
- *Building the MCP server itself — tools, resources, prompts, auth, transports, MCP Apps widgets, Inspector, deploy. Route to `build-mcp-use-server`.*
- *Raw `@modelcontextprotocol/*` SDK servers (no `mcp-use` wrapper). Route to `build-mcp-server-sdk-v1` or `build-mcp-server-sdk-v2`.*
- *LangChain/LangGraph agent code where MCP is optional or absent. Route to `build-langchain-ts-app`.*

**Rule of thumb:** if an LLM decides which MCP tool to call, this skill. If the app already knows which MCP call to make, `build-mcp-use-client`. If you are writing the server, `build-mcp-use-server`.

## Core rules (load-bearing — read before editing agent code)

| # | Rule | Why |
|---|---|---|
| 1 | Import agent APIs from `mcp-use`. Do not import raw `@modelcontextprotocol/*` primitives for agent code. | The agent loop, tool wiring, and lifecycle live in `mcp-use`. |
| 2 | Prefer object-form calls: `run({ prompt })`, `stream({ prompt })`, `streamEvents({ prompt })`, `prettyStreamEvents({ prompt })`. Plain-string overloads are compatibility paths. | Object form is the documented surface and supports schema, callbacks, tags. |
| 3 | Use a tool-calling chat model — LangChain `ChatModel` instance or supported `"provider/model"` shorthand. | Non-tool-calling models silently fail to invoke MCP tools. |
| 4 | Verified providers: OpenAI, Anthropic, Google, Groq, custom LangChain adapter. Treat OpenRouter / Ollama / local routes as custom adapters unless you re-verified primary docs. | Provider catalogs drift; do not ship from training-cutoff memory. |
| 5 | Verify model IDs and `mcp-use` version before shipping. Run `scripts/check-mcp-use-version.sh` or `npm view mcp-use version engines peerDependencies --json`. Match Node.js to the latest `engines` field. | Version, engines, and peer deps change between minor releases. |
| 6 | Set `maxSteps` deliberately. If the agent loops, lower the cap and narrow the prompt or tool surface before raising it. | Unbounded loops burn tokens and never converge. |
| 7 | Disable memory (`memoryEnabled: false`) for stateless handlers and batch jobs. Keep memory only for real multi-turn sessions. | Memory in stateless paths leaks state across requests. |
| 8 | Restrict risky tools with `disallowedTools`. Never use `toolsUsedNames` as an access filter. | `toolsUsedNames` is a result field, not a permission gate. |
| 9 | Set `observe: false` for high-throughput or cost-sensitive paths when tracing is not required. | Tracing has non-zero overhead. |
| 10 | Treat production runtime as Node.js unless verified. Do not imply edge-runtime support for agents that need Node APIs, stdio MCP servers, child processes, or LangChain provider packages. | Edge runtimes lack the APIs `mcp-use` and most providers depend on. |
| 11 | Keep observability claims precise — traces / logs / events are covered; metrics are production patterns unless implemented. | Overclaiming observability misleads reviewers. |

## Workflow

1. **Scan the target.** Inspect the actual package or app path. Look for `package.json`, `mcp-use`, imports of `MCPAgent` / `MCPClient`, `agent.run()`, `agent.stream()`, `agent.streamEvents()`, LangChain provider packages, server configs, existing cleanup.
2. **Classify the work.**
   - Existing agent: audit configuration, execution/output, MCP connections, production readiness against the rule table above.
   - New agent in an existing app: infer the smallest useful integration and wire it into the local structure.
   - New standalone agent: use the minimal runnable path below, then add only requested capabilities.
3. **Verify current package facts** (Rule 5) before writing runtime, peer, or setup claims.
4. **Choose construction mode.**
   - *Simplified mode:* `llm: "provider/model"` plus inline `mcpServers`. Best for scripts, demos, compact handlers.
   - *Explicit mode:* LangChain model instance plus `MCPClient`. Best for shared clients, code mode, callbacks, custom providers, lifecycle ownership. For deterministic client work that does not run the agent loop, route to `build-mcp-use-client`.
5. **Build the non-streaming path first.** Get one `run({ prompt })` call working before adding streaming, structured output, memory, observability, or server manager.
6. **Harden deliberately.** Add `maxSteps`, memory policy, tool restrictions, env validation, cleanup, runtime checks, observability — based on the target environment.
7. **Validate honestly.** At minimum run TypeScript / package checks or the relevant script. Claim live MCP+LLM behavior only after running against a real server and key.

## Minimal runnable path

The only inline example in this spine. Expanded variants live in `references/guides/quick-start.md` and `references/examples/agent-recipes.md`.

```typescript
import "dotenv/config";
import { MCPAgent } from "mcp-use";

if (!process.env.OPENAI_API_KEY) {
  throw new Error("OPENAI_API_KEY is required.");
}

const agent = new MCPAgent({
  llm: "openai/gpt-4o",
  llmConfig: { temperature: 0 },
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", process.cwd()],
    },
  },
  maxSteps: 10,
  memoryEnabled: false,
  autoInitialize: true,
});

try {
  const result = await agent.run({
    prompt: "List top-level files and summarize their roles.",
  });
  console.log(result);
} finally {
  await agent.close();
}
```

Before the first call, validate provider env vars and each MCP server `command` or URL. Debug broken prerequisites before changing agent logic.

## Completion contract

- `run()` resolves to the final value (`string` or schema-typed result).
- `stream()` yields `AgentStep` objects; the final value appears only when the generator completes (`done === true` from `.next()`).
- `streamEvents()` yields raw lifecycle events and does **not** return a final value. Consume events such as `on_chain_end` and tool/model events.
- For structured output with `streamEvents()`, the `mcp-use` structured result is `event.data.output` on `on_structured_output`.
- `step.observation` from `stream()` is empty at yield time; use `streamEvents()` for live tool-result payloads.

## Configuration and lifecycle contract

- *Simplified mode:* configuration lives inline on `MCPAgent` via `mcpServers`; the agent owns the generated client.
- *Explicit mode:* build an `MCPClient` from inline config or config-file helpers, then pass `client` to `MCPAgent`.
- `codeMode` lives on `MCPClient`, not `MCPAgent`.
- **Cleanup policy:**
  - Simplified mode or agent-owned client → `await agent.close()`.
  - Explicit, shared client owned outside the agent → close the owner once at app shutdown via `client.closeAllSessions()` or `client.close()` (the latter when code mode / E2B requires it).
  - Do not call both cleanup paths for the same ownership scope unless current docs or local runtime prove it is necessary.
  - Serverless with tracing → `await agent.flush()` before cleanup.

## Reference routing

Load only what the current task needs.

| Reference | Load when |
|---|---|
| `references/guides/quick-start.md` | First runnable agent, setup, chat loop, HTTP handlers, cleanup basics. |
| `references/guides/agent-configuration.md` | Constructor options, explicit vs simplified mode, config-file boundary, tool restrictions, prompt controls. |
| `references/guides/llm-integration.md` | Provider setup, model drift policy, shorthand strings, custom adapters, provider switching. |
| `references/guides/streaming.md` | `stream()`, `streamEvents()`, `prettyStreamEvents()`, generator completion, event handling. |
| `references/guides/structured-output.md` | Zod schemas, typed returns, structured-output events, validation retries. |
| `references/guides/memory-management.md` | `memoryEnabled`, `externalHistory`, token budgets, stateless handlers, history cleanup. |
| `references/guides/server-manager.md` | `useServerManager`, dynamic server activation, multi-server management tools. |
| `references/guides/observability.md` | Langfuse auto-init, callbacks, tags, metadata, trace flushing, raw events. |
| `references/guides/advanced-patterns.md` | Code mode, advanced provider/config examples, combined patterns. |
| `references/patterns/production-patterns.md` | Shutdown, retries, rate limits, timeouts, health metrics, deployment hardening. |
| `references/patterns/anti-patterns.md` | Review checklist for lifecycle, memory, mode mixing, provider drift, tool access, observability. |
| `references/examples/agent-recipes.md` | Copyable CLI, filesystem, browser, multi-server, structured output, streaming, code-mode recipes. |
| `references/examples/integration-recipes.md` | Next.js / Vercel AI SDK, Express SSE, React frontend, Langfuse, fallback, dynamic servers. |
| `references/troubleshooting/common-errors.md` | Known errors, stuck agents, Node/runtime checks, server spawn failures, streaming mistakes. |

## Scripts

Scripts live in `scripts/` beside this skill. Use `--help` first when the task is unclear.

| Script | Purpose | Mutates? | Doc |
|---|---|---:|---|
| `scripts/check-mcp-use-version.sh` | Print installed/latest `mcp-use`, engines, peer deps, and optional peer metadata without env values. | No | `scripts/check-mcp-use-version.md` |
| `scripts/scaffold-agent.sh` | Scaffold a minimal TypeScript `MCPAgent` project in an explicit target directory. Requires `--force` before overwriting. | Yes | `scripts/scaffold-agent.md` |
| `scripts/diagnose-agent-stuck.sh` | Inspect Node version, package versions, provider env presence, config flags, cleanup, server reachability, and output-mode mistakes. | No | `scripts/diagnose-agent-stuck.md` |

## Final checks

- `SKILL.md` stays lean and routes every reference file.
- Frontmatter description starts with `Use skill if you are` and is 30 words or fewer.
- No stale hard-coded `mcp-use` version claims remain.
- Node runtime guidance matches the latest npm `engines` result.
- Provider/model claims follow the verification policy instead of dated catalogs.
- Cleanup examples follow the ownership policy above.
- Validation passes with `python3 scripts/validate-skills.py`.
