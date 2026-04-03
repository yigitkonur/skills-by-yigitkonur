---
name: build-langchain-ts-app
description: Use skill if you are building TypeScript agents, RAG pipelines, or tool-calling workflows with LangChain.js and LangGraph.
---

# Build LangChain TypeScript App

Build with LangChain.js v1 and LangGraph in TypeScript. Prefer the smallest working pattern (`createAgent`) first, then add complexity only when required.

## Trigger boundary

Use this skill when work involves LangChain.js/LangGraph TypeScript design or implementation:

- Tool-calling agents
- RAG pipelines
- Streaming and structured output
- LangGraph stateful workflows
- MCP integration
- Memory/checkpointer design
- Multi-agent orchestration

Do not use this skill for:

- Python LangChain code
- Simple single-provider chatbot work where provider SDK alone is enough

## Non-negotiable rules

1. **TypeScript-only, LangChain v1 APIs only.**
2. **Start simple:** `createAgent` before `StateGraph`.
3. **Use real project functions as tools**; never use eval-style shortcuts.
4. **Choose model/provider explicitly** before adding middleware, memory, or RAG.
5. **Keep code incremental**: get one path working end-to-end, then extend.

## Fast decision tree

```
What are you building?
├── Basic tool-calling assistant (1-5 tools, low state)
│   └─► createAgent path (references/getting-started.md, references/agents.md)
├── Stateful loops, interrupts, custom routing
│   └─► LangGraph StateGraph path (references/langgraph.md, references/langgraph-execution.md)
├── Retrieval over documents
│   └─► RAG path (references/rag.md)
├── Strict JSON output contract
│   └─► Structured output path (references/structured-output.md)
├── UI token/event streaming
│   └─► Streaming path (references/streaming.md)
├── Multi-agent coordinator/swarm
│   └─► Multi-agent path (references/multi-agent.md)
└── External tools via MCP
    └─► MCP path (references/mcp.md)
```

## Baseline setup

```bash
npm install langchain @langchain/core @langchain/langgraph zod
npm install @langchain/openai
# Optional:
npm install @langchain/openrouter @langchain/mcp-adapters
```

Required runtime: **Node.js 20+** and TypeScript 5+.

Provider keys:

- OpenAI: `OPENAI_API_KEY`
- OpenRouter: `OPENROUTER_API_KEY`

For exact startup scaffolding (file layout + first run command), read `references/getting-started.md`.

## Minimal implementation workflow

1. **Pick provider/model**
   - Use `references/models.md` and `references/providers.md` for feature and compatibility checks.
2. **Pick agent architecture**
   - Start with `createAgent`; move to LangGraph only if you need state graphs/interrupts.
3. **Define tools and schemas**
   - Tool contracts must be explicit and testable (`references/tools.md`).
4. **Add reliability layers**
   - Middleware, retries, fallbacks, guardrails (`references/middleware-catalog.md`, `references/middleware-patterns.md`).
5. **Add memory/streaming/structured output as needed**
   - Use dedicated references instead of ad-hoc patterns.
6. **Instrument and test**
   - Add tracing/evaluation early (`references/observability-tracing.md`, `references/observability-evaluation.md`).

## Default path (recommended): createAgent

Use this as the initial architecture for most tasks:

- `createAgent` for orchestration
- Zod schemas for tool input contracts
- checkpointer only when thread persistence is required
- `toolStrategy` for structured output portability

Deep dive: `references/agents.md`.

## Escalation path: StateGraph

Switch to StateGraph only if one or more are true:

- You need explicit graph nodes/edges and branching
- You need interrupt/resume with human approval
- You need durable/replayable execution semantics
- You need complex multi-step state transitions

Deep dives: `references/langgraph.md`, `references/langgraph-execution.md`, `references/human-in-the-loop.md`.

## Common anti-patterns

Reject these and route to fixes:

- Legacy v0 imports (`langchain/chains`, deprecated APIs)
- `providerStrategy` with OpenRouter multi-model paths
- In-memory persistence choices for production
- Deeply nested tool schemas without clear constraints
- Streaming assumptions that conflict with structured output behavior

Canonical fixes: `references/common-errors.md`, `references/structured-output.md`, `references/streaming.md`.

## Reference routing

## Reference routing

| Document | What it contains | Load when |
|----------|-----------------|-----------|
| `references/getting-started.md` | First runnable paths with exact package subsets, env vars, file names, and run commands | Starting a new LangChain TS app or unblocking the first working run |
| `references/agents.md` | createAgent full parameter reference, 9 overloads, model config, structured output, streaming modes, ReAct lifecycle | Building an agent with createAgent |
| `references/models.md` | 15+ provider configs, 14 content block types, fakeModel API, model selection guide | Choosing or configuring chat models |
| `references/providers.md` | 24+ providers, feature matrix, initChatModel universal interface, provider-specific setup | Setting up providers or comparing capabilities |
| `references/tools.md` | tool() factory, schema design, 35+ built-in tools, type hierarchy, error handling, 9 known issues | Designing or debugging tools |
| `references/structured-output.md` | withStructuredOutput, providerStrategy vs toolStrategy, parser catalog, provider-specific bugs | Extracting structured data from models |
| `references/streaming.md` | 8 LangGraph stream modes, 17 event types, streamEvents v2, Vercel AI SDK, Next.js, Express | Streaming responses to UI |
| `references/memory-checkpointers.md` | MemorySaver, PostgresSaver, RedisSaver, trimMessages, summarization, thread management | Thread-scoped conversation memory |
| `references/memory-stores.md` | BaseStore API, InMemoryStore, PostgresStore, caching, GDPR compliance, legacy migration | Long-term memory, caching, compliance |
| `references/middleware-catalog.md` | All 14 built-in middleware with signatures, 6 hook types, execution order | Using built-in middleware |
| `references/middleware-patterns.md` | createMiddleware API, guardrails, PII filtering, runtime context, composition rules | Custom middleware and guardrails |
| `references/mcp.md` | MultiServerMCPClient, stdio/SSE/HTTP transports, OAuth, tool discovery, lifecycle management | Integrating MCP servers |
| `references/human-in-the-loop.md` | interrupt() API, Command resume, RBAC, async approval, useStream UI, tool confirmation | Adding human approval to workflows |
| `references/multi-agent.md` | 4 architecture patterns, handoffs, routing strategies, SubAgent interface, τ-bench benchmarks | Coordinating multiple agents |
| `references/rag.md` | Document loaders, text splitters, embeddings (13+ providers), vector stores (17), retriever types, RAGAS metrics | Building RAG pipelines |
| `references/langgraph.md` | StateGraph, 4 channel types, Graph vs Functional API, Command/Send, subgraphs, conditional routing | Building custom graphs |
| `references/langgraph-execution.md` | Checkpointer architecture, thread management, state serialization, parallel execution, time travel | LangGraph persistence and execution |
| `references/knowledge-agents.md` | SQL agent safety, voice pipelines, multi-KB routing, query validation | Building knowledge-domain agents |
| `references/deployment-local.md` | LangGraph Studio, CLI commands, langgraph.json schema, local dev server, Agent Chat UI | Local development and Studio |
| `references/deployment-production.md` | Docker, Cloud, self-hosted servers, Generative UI, CI/CD, pricing, scaling | Production deployment |
| `references/observability-tracing.md` | LangSmith setup, 19 callback types, tracing, cost tracking, dashboards, alerts | Tracing and monitoring |
| `references/observability-evaluation.md` | LangSmith evaluation, datasets, LLM-as-judge, OpenTelemetry, third-party tools, pricing | Testing and evaluation |
| `references/common-errors.md` | Error catalog by category, antipatterns, v0→v1 migration, provider-specific gotchas | Debugging errors or reviewing code |

## Guardrails

- Do not use Python-only guidance in a TypeScript implementation.
- Do not add complexity before a minimal path runs successfully.
- Do not use outdated v0 APIs.
- Do not assume provider feature parity; verify with `references/providers.md`.
- Do not rely on in-memory persistence components in production workflows.
- Do not ship without tracing/error visibility.

## Scope boundaries

This skill covers LangChain.js and LangGraph.js in TypeScript only. It does not cover:
- Python LangChain (different APIs and patterns)
- LangServe (Python-only)
- Embeddings via OpenRouter (use OpenAI directly)
- Database-specific setup beyond connection patterns (PostgresSaver, SqliteSaver need separate install)
