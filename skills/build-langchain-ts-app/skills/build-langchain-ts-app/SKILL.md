---
name: build-langchain-ts-app
description: Use skill if you are building TypeScript agents, RAG pipelines, or tool-calling workflows with LangChain.js and LangGraph.
---

# Build LangChain TypeScript App

Build LangChain.js v1 and LangGraph.js applications in TypeScript. Keep the spine small, choose one implementation path before coding, and load the bundled references only for the selected path.

## Trigger boundary

Use this skill for LangChain.js/LangGraph TypeScript implementation: `createAgent` assistants, RAG pipelines, structured output, streaming APIs, raw `StateGraph` workflows, MCP-backed tools, memory/checkpointing, multi-agent systems, and knowledge-domain agents.

Do not use this skill for Python LangChain, LangServe, or simple single-provider chat where the provider SDK alone is enough.

| Adjacent skill | Use instead when |
|---|---|
| `build-copilot-sdk-app` | The app uses `@github/copilot-sdk`, Copilot CLI sessions, Copilot custom tools, or BYOK. |
| `build-mcp-use-agent` | The agent is built with `mcp-use` `MCPAgent`. |
| `build-effect-ts-v3` | The core runtime is Effect / `@effect/*`, even if it calls LLMs. |
| `run-research` | The task is web-evidence research about LangChain versions, pricing, docs, or ecosystem decisions, not code implementation. |

## Preflight

Before coding, inspect the target repo and record:

- `package.json`: module type, scripts, framework, existing LangChain packages, and test command.
- Runtime: Node.js 20+ and TypeScript 5+; stop and fix lower versions before debugging LangChain behavior.
- Installed versions: `npm ls langchain @langchain/core @langchain/langgraph @langchain/openai` when dependencies are installed; use `references/start/version-discipline.md` for drift checks.
- Provider environment: `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, Anthropic/Google/Azure keys, LangSmith keys, MCP credentials.
- Work mode: greenfield scaffold vs existing app integration; for existing apps, follow local file layout and test conventions.

## Choose the path

Force the architecture choice before writing code:

- **Tool-calling assistant:** choose `createAgent` when external actions or business functions are needed and graph state/routing is not explicit.
- **2-step RAG:** choose deterministic retrieval plus answer generation when every query requires retrieval and predictable latency matters.
- **Agentic RAG:** expose the retriever as a tool when retrieval is one possible action among several.
- **Raw LangGraph:** use `StateGraph` only when the app needs explicit state, routing, interrupts, fan-out/fan-in, or durable graph execution.

| Path | Expected output shape | First reference to load | Verification |
|---|---|---|---|
| `createAgent` tool-calling assistant | Messages state plus optional `structuredResponse`; tools call real project functions. | `references/agents/agents.md`, then `references/agents/tools.md` | Assert tool call/result behavior, final message, max-step limit, and optional structured response. |
| RAG pipeline | Answer plus retrieved/source `Document[]`, citations, and grounding metadata. | `references/rag/rag.md` | Assert retrieval count, source IDs, answer contract, and no-answer behavior. |
| Raw `StateGraph` | Typed graph state returned from `invoke`/`stream`; state transitions are explicit. | `references/langgraph/langgraph.md` | Assert node outputs, conditional routes, recursion limit, and persisted state when enabled. |
| Structured output | Validated schema object or explicit parse/retry failure path. | `references/agents/structured-output.md` | Assert schema success, invalid-output handling, and provider/tool strategy behavior. |
| Streaming UI/API | Chosen token/event/update contract with cancellation and error events. | `references/agents/streaming.md` | Assert event order, chunk shape, completion signal, and abort behavior. |
| MCP integration | Namespaced MCP tools, lifecycle management, and explicit auth/transport config. | `references/providers/mcp.md` | Assert server connection, tool discovery/filtering, timeout, cleanup, and credential failure behavior. |
| Memory/checkpointing | Stable `thread_id`, selected checkpointer/store, retention rules, and replay expectations. | `references/langgraph/memory-checkpointers.md` | Assert multi-turn continuity, isolation between threads, and persistence across process restart if durable. |
| Multi-agent / knowledge-domain agent | Supervisor/router/handoff state plus domain safety constraints. | `references/agents/multi-agent.md` or `references/agents/knowledge-agents.md` | Assert route selection, handoff messages, domain guardrails, and failure fallback. |

## Implementation contracts

- Match tests to the selected output contract. Do not claim the path works if tests only assert an LLM text substring.
- Keep real side effects behind tools with Zod schemas and deterministic unit tests.
- Use `toolStrategy` as the portable structured-output default; choose `providerStrategy` only when the selected provider is known to support it.
- Token-level streaming and strict validated structured output often need different contracts. Choose raw-token streaming with parse-on-completion, event streaming, or non-streaming structured output deliberately.
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

Use `@latest` only in update commands or exploratory refreshes, not as the documented tested state. When package APIs matter, verify the current package matrix before editing examples and record the research date. See `references/start/version-discipline.md`.

## Reliability guardrails

For RAG, make these decisions before implementation:

| Decision | Local default | Production requirement |
|---|---|---|
| Corpus size/update cadence | Small static fixture | Ingestion and re-indexing plan |
| Embedding model/dimension | `OpenAIEmbeddings`, `text-embedding-3-small` | Stable model, recorded dimension, migration plan |
| Vector store | `InMemoryVectorStore` | Persistent store with backups and filters |
| Metadata filtering | Source ID only | Typed metadata schema and filter tests |
| Retriever type | Similarity retriever | Chosen retriever/reranker based on eval results |
| Grounding contract | Return source documents | Citations, refusal/no-answer policy, regression eval |
| Evaluation metric | Manual smoke test | Retrieval recall, faithfulness, answer relevance |

Before productionizing any path, define max steps or recursion limits, token budget, retry/fallback policy, rate-limit strategy, and failure surface. Route details to `references/middleware/middleware-catalog.md`, `references/middleware/middleware-patterns.md`, `references/ops/observability-tracing.md`, and `references/ops/observability-evaluation.md`.

Use LangSmith/observability for development debugging, production traces, cost/token tracking, RAG evaluation, and user feedback or online evals. Verify current pricing before quoting costs.

## Reference routing

Load only the files needed for the selected path.

| Intent | Read |
|---|---|
| First runnable app, baseline commands, and version drift | `references/start/getting-started.md`, `references/start/common-errors.md`, `references/start/version-discipline.md` |
| Agent orchestration and tool contracts | `references/agents/agents.md`, `references/agents/tools.md` |
| Structured output and streaming | `references/agents/structured-output.md`, `references/agents/streaming.md` |
| Multi-agent and knowledge-domain agents | `references/agents/multi-agent.md`, `references/agents/knowledge-agents.md` |
| Raw LangGraph execution | `references/langgraph/langgraph.md`, `references/langgraph/langgraph-execution.md`, `references/langgraph/human-in-the-loop.md` |
| Memory and persistence | `references/langgraph/memory-checkpointers.md`, `references/langgraph/memory-stores.md` |
| RAG | `references/rag/rag.md` |
| Middleware and guardrails | `references/middleware/middleware-catalog.md`, `references/middleware/middleware-patterns.md` |
| Models, providers, and MCP | `references/providers/models.md`, `references/providers/providers.md`, `references/providers/mcp.md` |
| Local and production deployment | `references/ops/deployment-local.md`, `references/ops/deployment-production.md` |
| Tracing, evaluation, and online feedback | `references/ops/observability-tracing.md`, `references/ops/observability-evaluation.md` |

## Scope boundaries

- Use LangChain.js and LangGraph.js v1 TypeScript APIs only.
- Keep Python-only guidance out of TypeScript implementations.
- Keep legacy v0 imports such as `langchain/chains` only when documenting migrations or anti-patterns.
- Do not rely on in-memory checkpointers, stores, vector stores, or caches for production persistence.
- Do not assume provider feature parity; verify model/tool/structured-output/streaming support before coding against it.
