---
name: build-mcp-use-agent
description: Use skill if you are building TypeScript mcp-use MCPAgent code where an LLM chooses and orchestrates MCP tools.
---

# Build MCP Use Agent

Build or audit TypeScript `MCPAgent` code from `mcp-use`. Keep the spine focused on routing and decisions; load references for signatures, tables, and copyable recipes.

## When to use this skill vs neighbors

- **This skill:** an LLM-driven `MCPAgent` chooses, calls, and orchestrates MCP tools.
- **`build-mcp-use-client`:** deterministic `MCPClient` code lists/calls tools, reads resources, handles sessions, or builds React/client integrations without LLM agent orchestration.
- **`build-mcp-use-server`:** builds the MCP server, tool, resource, prompt, auth, transport, or widget side with `mcp-use/server`.
- **`build-mcp-server-sdk-v1` / `build-mcp-server-sdk-v2`:** builds raw `@modelcontextprotocol/*` SDK servers, not `mcp-use` wrappers.
- **`build-langchain-ts-app`:** builds LangChain/LangGraph agents, RAG, memory, or multi-agent workflows where MCP is optional or secondary.
- **`build-copilot-sdk-app`:** builds GitHub Copilot SDK apps, sessions, CLI-backed JSON-RPC, tools, hooks, or BYOK flows.

Rule of thumb: choose `MCPAgent` when a model must decide which MCP tools to call. Choose raw `MCPClient` when the app already knows the exact MCP operation.

## Workflow

1. **Scan the target.** Inspect the actual package or app path. Look for `package.json`, `mcp-use`, imports of `MCPAgent` / `MCPClient`, `agent.run()`, `agent.stream()`, `agent.streamEvents()`, LangChain provider packages, server configs, and existing cleanup.
2. **Classify the work.**
   - Existing agent: audit configuration, execution/output, MCP connections, and production readiness.
   - New agent in an existing app: infer the smallest useful integration and wire it into the local structure.
   - New standalone agent: use the minimal runnable path below, then add only requested capabilities.
3. **Verify current package facts.** Run `scripts/check-mcp-use-version.sh` or `npm view mcp-use version engines peerDependencies peerDependenciesMeta --json` before writing runtime, peer, or setup claims.
4. **Choose construction mode.**
   - Simplified mode: `llm: "provider/model"` plus inline `mcpServers`; best for scripts, demos, and compact handlers.
   - Explicit mode: LangChain model instance plus `MCPClient`; best for shared clients, code mode, callbacks, custom providers, or lifecycle ownership.
5. **Build the non-streaming path first.** Get one `run({ prompt })` call working before adding streaming, structured output, memory, observability, or server manager.
6. **Harden deliberately.** Set `maxSteps`, memory, tool restrictions, env validation, cleanup, runtime support, and observability based on the target environment.
7. **Validate honestly.** At minimum run TypeScript/package checks or the relevant script. Claim live MCP+LLM behavior only after running against a real server and key.

## Core rules

- Import agent APIs from `mcp-use`; do not import raw MCP SDK primitives for agent code.
- Prefer object-form calls: `run({ prompt })`, `stream({ prompt })`, `streamEvents({ prompt })`, and `prettyStreamEvents({ prompt })`. Plain-string overloads are compatibility paths.
- Use a tool-calling chat model through LangChain or a supported `"provider/model"` shorthand.
- Concrete provider coverage is OpenAI, Anthropic, Google, Groq, and custom LangChain-compatible adapters. Treat OpenRouter, Ollama, and local-model routes as custom adapters unless primary docs were verified during the task.
- Verify model IDs before shipping. Keep model names in config or env; examples are placeholders, not stable provider catalogs.
- Match Node.js to the latest `mcp-use` `engines` field. Do not document Node 18 support for current `mcp-use` unless npm confirms it.
- Set `maxSteps` deliberately. If the agent loops, lower the cap and narrow the prompt or tool surface before raising it.
- Disable memory for stateless handlers and batch jobs. Keep memory only for real multi-turn behavior.
- Restrict risky tools with `disallowedTools`; do not use `toolsUsedNames` as an access filter.
- Use `observe: false` for high-throughput or cost-sensitive paths when tracing is not required.
- Treat production runtime as Node.js unless verified otherwise. Do not imply edge-runtime support for agents that need Node APIs, stdio servers, child processes, or LangChain provider packages.
- Keep observability claims precise: traces/logs/events are covered; metrics are production patterns unless implemented.

## Minimal runnable path

Use this as the only inline example in the spine. Load `references/guides/quick-start.md` and `references/examples/agent-recipes.md` for expanded variants.

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

Before the first call, validate provider env vars and each MCP server command or URL. Debug broken prerequisites before changing agent logic.

## Completion contract

- `run()` resolves to the final value (`string` or schema-typed result).
- `stream()` yields `AgentStep` objects; the final value appears only when the generator completes (`done === true` from `.next()`).
- `streamEvents()` yields raw lifecycle events and does not return a final value. Consume events such as `on_chain_end` and tool/model events.
- For structured output with `streamEvents()`, the mcp-use structured result is `event.data.output` on `on_structured_output`.
- `step.observation` from `stream()` is empty at yield time; use `streamEvents()` for live tool-result payloads.

## Configuration and lifecycle contract

- In simplified mode, configuration lives inline on `MCPAgent` through `mcpServers`; the agent owns the generated client.
- In explicit mode, build an `MCPClient` from inline config or config-file helpers, then pass `client` to `MCPAgent`. Route deeper deterministic client work to `build-mcp-use-client`.
- Set `codeMode` on `MCPClient`, not `MCPAgent`.
- Cleanup policy:
  - simplified mode or agent-owned client: `await agent.close()`
  - explicit shared client owned outside the agent: close the owner once at application shutdown with `client.closeAllSessions()` or `client.close()` when code mode/E2B requires it
  - do not call both cleanup methods for the same ownership scope unless current docs or local runtime prove it is necessary
  - serverless with tracing: `await agent.flush()` before cleanup

## Reference routing

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
| `references/examples/integration-recipes.md` | Next.js/Vercel AI SDK, Express SSE, React frontend, Langfuse, fallback, dynamic servers. |
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
- Frontmatter description starts with `Use skill if you are` and stays within 30 words.
- No stale hard-coded `mcp-use` version claims remain.
- Node runtime guidance matches the latest npm `engines` result.
- Provider/model claims follow the verification policy instead of dated catalogs.
- Cleanup examples follow the ownership policy above.
- Validation passes with `python3 scripts/validate-skills.py`.
