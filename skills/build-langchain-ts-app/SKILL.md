---
name: build-langchain-ts-app
description: "Use if building TypeScript apps with langchain/@langchain — agents, RAG, structured output."
---

# Build LangChain TypeScript App

Build LangChain.js v1 and LangGraph.js applications in TypeScript. Choose one implementation path before coding, keep the spine small, and load only the bundled references the chosen path needs.

## When to use this skill

- *Building a tool-calling assistant with `createAgent` from `langchain` and Zod-typed tools.*
- *Wiring a RAG pipeline with a `Document` loader, splitter, embeddings, vector store, and retriever.*
- *Authoring a raw `StateGraph` from `@langchain/langgraph` with explicit state, routing, fan-out/fan-in, or interrupts.*
- *Adding structured output via `withStructuredOutput`, `responseFormat`, `toolStrategy`, or `providerStrategy`.*
- *Streaming tokens, events, or graph updates back to a UI/API and handling cancellation.*
- *Persisting agent/graph state with checkpointers, stores, or `thread_id`-keyed memory.*
- *Connecting MCP servers as namespaced tools through `@langchain/mcp-adapters`.*
- *Composing supervisor/router/handoff multi-agent or knowledge-domain agents in TypeScript.*

Do **not** use this skill when:

- The codebase is **Python LangChain / LangGraph** — TypeScript-only patterns here will mislead.
- A simple **single-provider chat** call (e.g., `openai.chat.completions.create`) is enough — pull in the provider SDK directly.
- The agent runtime is **`mcp-use` `MCPAgent`** — use `build-mcp-use-agent`.
- The core runtime is **Effect / `@effect/*`** even if it calls LLMs — use `build-effect-ts-v3`.

## Trigger signals (imports and idioms)

Treat these as the strong-positive signals for this skill:

| Signal | Example |
|---|---|
| `langchain` package import | `import { createAgent } from "langchain"` |
| `@langchain/core/*` | `import { tool } from "@langchain/core/tools"` |
| `@langchain/langgraph` | `import { StateGraph, MemorySaver, Annotation } from "@langchain/langgraph"` |
| Provider packages | `@langchain/openai`, `@langchain/anthropic`, `@langchain/google-genai`, `@langchain/azure-openai` |
| Retrieval stack | `@langchain/textsplitters`, `RecursiveCharacterTextSplitter`, `OpenAIEmbeddings`, `InMemoryVectorStore`, `*.asRetriever()` |
| MCP adapters | `import { MultiServerMCPClient } from "@langchain/mcp-adapters"` |
| Structured output / streaming | `model.withStructuredOutput(schema)`, `responseFormat`, `toolStrategy`, `providerStrategy`, `agent.stream(..., { streamMode: "updates" })` |
| Persistence | `MemorySaver`, `checkpointer`, `thread_id`, `store` |
| LangSmith | `langsmith`, `LANGSMITH_API_KEY`, `traceable`, `openevals` |

If none of these appear and the task is plain chat completion, route away from this skill.

## Preflight

Before coding, inspect the target repo and record:

- `package.json`: module type, scripts, framework, existing LangChain packages, and test command.
- Runtime: Node.js 20+ and TypeScript 5+; stop and fix lower versions before debugging LangChain behavior.
- Installed versions: `npm ls langchain @langchain/core @langchain/langgraph @langchain/openai` when dependencies are installed; for drift checks use [references/start/version-discipline.md](references/start/version-discipline.md).
- Version script: run `scripts/check-langchain-versions.sh` for a read-only package report; docs live in `scripts/check-langchain-versions.sh.md`.
- Provider environment: `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, Anthropic/Google/Azure keys, LangSmith keys, MCP credentials.
- Work mode: greenfield scaffold vs existing app integration; for existing apps, follow local file layout and test conventions.
- Greenfield utility: use `scripts/scaffold-createagent-app.sh` only for a minimal `createAgent` app; docs live in `scripts/scaffold-createagent-app.sh.md`.

For first-runnable apps and recovery from common failures, consult [references/start/getting-started.md](references/start/getting-started.md) and [references/start/common-errors.md](references/start/common-errors.md).

## Choose the path (load-bearing)

Force the architecture choice before writing code:

- **Tool-calling assistant:** choose `createAgent` when external actions or business functions are needed and graph state/routing is not explicit.
- **2-step RAG:** choose deterministic retrieval plus answer generation when every query requires retrieval and predictable latency matters.
- **Agentic RAG:** expose the retriever as a tool when retrieval is one possible action among several.
- **Raw LangGraph:** use `StateGraph` only when the app needs explicit state, routing, interrupts, fan-out/fan-in, or durable graph execution.

| Path | Output shape | First reference | Verification |
|---|---|---|---|
| `createAgent` tool-calling assistant | Messages state plus optional `structuredResponse`; tools call real project functions. | [references/agents/agents.md](references/agents/agents.md), then [references/agents/tools.md](references/agents/tools.md) | Assert tool call/result behavior, final message, max-step limit, optional structured response. |
| RAG pipeline | Answer plus retrieved/source `Document[]`, citations, grounding metadata. | [references/rag/rag.md](references/rag/rag.md) | Assert retrieval count, source IDs, answer contract, no-answer behavior. |
| Raw `StateGraph` | Typed graph state returned from `invoke`/`stream`; transitions are explicit. | [references/langgraph/langgraph.md](references/langgraph/langgraph.md), then [references/langgraph/langgraph-execution.md](references/langgraph/langgraph-execution.md) | Assert node outputs, conditional routes, recursion limit, persisted state when enabled. |
| Structured output | Validated schema object or explicit parse/retry failure path. | [references/agents/structured-output.md](references/agents/structured-output.md) | Assert schema success, invalid-output handling, provider/tool strategy behavior. |
| Streaming UI/API | Chosen token/event/update contract with cancellation and error events. | [references/agents/streaming.md](references/agents/streaming.md) | Assert event order, chunk shape, completion signal, abort behavior. |
| Human-in-the-loop | Interrupted graph paused on review/edit/approve nodes. | [references/langgraph/human-in-the-loop.md](references/langgraph/human-in-the-loop.md) | Assert interrupt payload, resume path, replay behavior. |
| MCP integration | Namespaced MCP tools, lifecycle management, explicit auth/transport config. | [references/providers/mcp.md](references/providers/mcp.md) | Assert server connection, tool discovery/filtering, timeout, cleanup, credential failure. |
| Memory / persistence | Stable `thread_id`, selected checkpointer/store, retention rules, replay. | [references/langgraph/memory-checkpointers.md](references/langgraph/memory-checkpointers.md) plus [references/langgraph/memory-stores.md](references/langgraph/memory-stores.md) | Assert multi-turn continuity, isolation between threads, persistence across restart if durable. |
| Multi-agent / knowledge-domain | Supervisor/router/handoff state plus domain safety constraints. | [references/agents/multi-agent.md](references/agents/multi-agent.md) or [references/agents/knowledge-agents.md](references/agents/knowledge-agents.md) | Assert route selection, handoff messages, domain guardrails, failure fallback. |

## Implementation contracts

- Match tests to the selected output contract. Do not claim the path works if tests only assert an LLM text substring.
- Keep real side effects behind tools with Zod schemas and deterministic unit tests.
- Use `toolStrategy` as the portable structured-output default; choose `providerStrategy` only when the selected provider is known to support it.
- Token-level streaming and strictly validated structured output often need different contracts. Choose raw-token streaming with parse-on-completion, event streaming, or non-streaming structured output deliberately.
- Start with one path end-to-end, then layer memory, streaming, middleware, or observability.

## Version and package discipline

Use path-specific package subsets and pin compatible versions in real apps:

| Path | Baseline packages |
|---|---|
| `createAgent` | `langchain @langchain/core zod` plus a provider package such as `@langchain/openai` |
| RAG | `langchain @langchain/core @langchain/openai @langchain/textsplitters zod` plus the chosen vector-store package |
| Raw LangGraph | `@langchain/langgraph @langchain/core zod` plus provider/checkpointer packages as needed |
| MCP | `langchain @langchain/core @langchain/mcp-adapters @modelcontextprotocol/sdk zod` |
| LangSmith eval/tracing | `langsmith` plus `openevals` only when evaluation workflows need it |

Use `@latest` only in update commands or exploratory refreshes, not as the documented tested state. When package APIs matter, verify the current package matrix before editing examples and record the research date. See [references/start/version-discipline.md](references/start/version-discipline.md).

For existing apps, run `scripts/check-langchain-versions.sh` before diagnosing API drift or changing package pins. The paired docs are `scripts/check-langchain-versions.sh.md`.

For greenfield `createAgent` demos, run `scripts/scaffold-createagent-app.sh` to generate the smallest pinned TypeScript app. The paired docs are `scripts/scaffold-createagent-app.sh.md`.

## RAG reliability defaults

For RAG, make these decisions before implementation:

| Decision | Local default | Production requirement |
|---|---|---|
| Corpus size / update cadence | Small static fixture | Ingestion and re-indexing plan |
| Embedding model / dimension | `OpenAIEmbeddings`, `text-embedding-3-small` | Stable model, recorded dimension, migration plan |
| Vector store | `InMemoryVectorStore` | Persistent store with backups and filters |
| Metadata filtering | Source ID only | Typed metadata schema and filter tests |
| Retriever type | Similarity retriever | Chosen retriever/reranker based on eval results |
| Grounding contract | Return source documents | Citations, refusal/no-answer policy, regression eval |
| Evaluation metric | Manual smoke test | Retrieval recall, faithfulness, answer relevance |

## Production guardrails

Before productionizing any path, define max steps or recursion limits, token budget, retry/fallback policy, rate-limit strategy, and failure surface. Route details to [references/middleware/middleware-catalog.md](references/middleware/middleware-catalog.md), [references/middleware/middleware-patterns.md](references/middleware/middleware-patterns.md), [references/ops/observability-tracing.md](references/ops/observability-tracing.md), and [references/ops/observability-evaluation.md](references/ops/observability-evaluation.md).

For deployment shape and platform constraints (Node version, edge runtimes, container/cloud targets), read [references/ops/deployment-local.md](references/ops/deployment-local.md) and [references/ops/deployment-production.md](references/ops/deployment-production.md).

For provider/model selection, capability differences, and key wiring, read [references/providers/models.md](references/providers/models.md) and [references/providers/providers.md](references/providers/providers.md).

Use LangSmith/observability for development debugging, production traces, cost/token tracking, RAG evaluation, and user feedback or online evals. Verify current pricing before quoting costs.

## Reference routing

Load only the files needed for the selected path.

| Intent | Read |
|---|---|
| First runnable app, baseline commands, version drift | [references/start/getting-started.md](references/start/getting-started.md), [references/start/common-errors.md](references/start/common-errors.md), [references/start/version-discipline.md](references/start/version-discipline.md) |
| Agent orchestration and tool contracts | [references/agents/agents.md](references/agents/agents.md), [references/agents/tools.md](references/agents/tools.md) |
| Structured output and streaming | [references/agents/structured-output.md](references/agents/structured-output.md), [references/agents/streaming.md](references/agents/streaming.md) |
| Multi-agent and knowledge-domain agents | [references/agents/multi-agent.md](references/agents/multi-agent.md), [references/agents/knowledge-agents.md](references/agents/knowledge-agents.md) |
| Raw LangGraph execution | [references/langgraph/langgraph.md](references/langgraph/langgraph.md), [references/langgraph/langgraph-execution.md](references/langgraph/langgraph-execution.md), [references/langgraph/human-in-the-loop.md](references/langgraph/human-in-the-loop.md) |
| Memory and persistence | [references/langgraph/memory-checkpointers.md](references/langgraph/memory-checkpointers.md), [references/langgraph/memory-stores.md](references/langgraph/memory-stores.md) |
| RAG | [references/rag/rag.md](references/rag/rag.md) |
| Middleware and guardrails | [references/middleware/middleware-catalog.md](references/middleware/middleware-catalog.md), [references/middleware/middleware-patterns.md](references/middleware/middleware-patterns.md) |
| Models, providers, and MCP | [references/providers/models.md](references/providers/models.md), [references/providers/providers.md](references/providers/providers.md), [references/providers/mcp.md](references/providers/mcp.md) |
| Local and production deployment | [references/ops/deployment-local.md](references/ops/deployment-local.md), [references/ops/deployment-production.md](references/ops/deployment-production.md) |
| Tracing, evaluation, and online feedback | [references/ops/observability-tracing.md](references/ops/observability-tracing.md), [references/ops/observability-evaluation.md](references/ops/observability-evaluation.md) |
| Deterministic utilities | `scripts/check-langchain-versions.sh.md`, `scripts/scaffold-createagent-app.sh.md` |

## Scope boundaries

- Use LangChain.js and LangGraph.js v1 TypeScript APIs only.
- Keep Python-only guidance out of TypeScript implementations.
- Keep legacy v0 imports such as `langchain/chains` only when documenting migrations or anti-patterns.
- Do not rely on in-memory checkpointers, stores, vector stores, or caches for production persistence.
- Do not assume provider feature parity; verify model/tool/structured-output/streaming support before coding against it.
