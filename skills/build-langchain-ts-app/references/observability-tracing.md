# Observability: Tracing & Monitoring Reference

Complete reference for LangSmith tracing setup, callback system, span data model, cost/token tracking, and production monitoring. All APIs verified against langchain@1.2.35, @langchain/core@1.1.34, @langchain/langgraph@1.2.5, langsmith (latest). TypeScript only.

---

## Quick Reference — Imports

```typescript
// LangSmith core
import { Client } from "langsmith";
import { traceable, getCurrentRunTree } from "langsmith/traceable";
import { RunTree } from "langsmith";
import { getLangchainCallbacks } from "langsmith/langchain";
import { waitForAllTracers } from "@langchain/core/tracers";
import { createAnonymizer } from "langsmith/anonymizer";

// LangChain tracers and callbacks
import { LangChainTracer } from "@langchain/core/tracers/tracer_langchain";
import { ConsoleCallbackHandler } from "@langchain/core/tracers/console";
import { StreamingStdOutCallbackHandler } from "@langchain/core/callbacks/streaming_stdout";
import { UsageMetadataCallbackHandler } from "@langchain/core/callbacks/usage";
import { BaseCallbackHandler } from "@langchain/core/callbacks/base";
import { CallbackManager } from "@langchain/core/callbacks/manager";
```

---

## 1. LangSmith Setup and Configuration

### Required Environment Variables

```bash
# Enable automatic tracing — no code changes needed
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY="lsv2_pt_..."       # from smith.langchain.com > Settings > API Keys

# Optional but recommended
export LANGSMITH_PROJECT="my-agent-project"  # defaults to "default"
export LANGSMITH_ENDPOINT="https://api.smith.langchain.com"  # EU: https://eu.api.smith.langchain.com
export LANGSMITH_WORKSPACE_ID="<id>"         # multi-workspace API keys only

# Performance tuning
export LANGCHAIN_CALLBACKS_BACKGROUND=true   # non-serverless: reduces latency (callbacks run async)
# export LANGCHAIN_CALLBACKS_BACKGROUND=false  # serverless: ensures traces flush before response
```

### Full Environment Variable Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `LANGSMITH_TRACING` | Enable LangSmith tracing | `false` |
| `LANGSMITH_API_KEY` | LangSmith API key | — |
| `LANGSMITH_PROJECT` | Default project name | `"default"` |
| `LANGSMITH_ENDPOINT` | LangSmith API endpoint | `https://api.smith.langchain.com` |
| `LANGSMITH_WORKSPACE_ID` | Target workspace (multi-workspace keys) | — |
| `LANGSMITH_OTEL_ENABLED` | Enable OpenTelemetry mode | `false` |
| `LANGSMITH_OTEL_ONLY` | Only send to custom OTEL provider, skip LangSmith | `false` |
| `LANGCHAIN_CALLBACKS_BACKGROUND` | Run callbacks in background thread | `true` |
| `LANGSMITH_LICENSE_KEY` | Production license for self-hosted deployment | — |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP exporter endpoint | — |
| `OTEL_EXPORTER_OTLP_HEADERS` | OTLP authentication headers | — |
| `OTEL_SERVICE_NAME` | Service name in OTEL spans | `"langsmith"` |

### Client Constructor

```typescript
import { Client } from "langsmith";

const client = new Client({
  apiKey: process.env.LANGSMITH_API_KEY,
  apiUrl: "https://api.smith.langchain.com",   // default
  // apiUrl: "https://eu.api.smith.langchain.com",  // EU region
  workspaceId: process.env.LANGSMITH_WORKSPACE_ID,  // multi-workspace
});
```

### LangChainTracer Constructor

```typescript
import { LangChainTracer } from "@langchain/core/tracers/tracer_langchain";
import { Client } from "langsmith";

// Simplest form — uses env vars
const tracer = new LangChainTracer({ projectName: "my-project" });

// With explicit client (custom endpoint, EU, etc.)
const langsmithClient = new Client({ apiKey: "...", apiUrl: "..." });
const tracer = new LangChainTracer({
  client: langsmithClient,
  projectName: "my-project",
});
```

---

## 2. Automatic Tracing

Once `LANGSMITH_TRACING=true` is set, every LangChain/LangGraph operation is traced with zero code changes.

```typescript
import { StateGraph, Annotation } from "@langchain/langgraph";
import { ChatOpenAI } from "@langchain/openai";

// No tracing code here — it is all automatic
const model = new ChatOpenAI({ modelName: "gpt-4.1-mini" });

const StateAnnotation = Annotation.Root({
  messages: Annotation<any[]>({ reducer: (a, b) => [...a, ...b] }),
});

async function callModel(state: typeof StateAnnotation.State) {
  const response = await model.invoke(state.messages);
  return { messages: [response] };
}

const graph = new StateGraph(StateAnnotation)
  .addNode("agent", callModel)
  .addEdge("__start__", "agent")
  .addEdge("agent", "__end__")
  .compile();

// Every invocation automatically generates a full trace in LangSmith
await graph.invoke({ messages: [{ role: "user", content: "Hello" }] });
```

### Selective Tracing (Per Invocation)

```typescript
import { LangChainTracer } from "@langchain/core/tracers/tracer_langchain";

// Only trace this specific invocation
const tracer = new LangChainTracer({ projectName: "email-agent-test" });

await agent.invoke(
  { messages: [{ role: "user", content: "Send a test email" }] },
  { callbacks: [tracer] }
);
```

### Static Config via `.withConfig()`

```typescript
// Configure once, applies to all subsequent invocations
const configuredChain = chain.withConfig({
  tags: ["ts-chain", "production"],
  metadata: { env: "prod", version: "1.0" },
  run_name: "MyProductionChain",
});
```

### Per-Invocation Configuration

```typescript
const result = await chain.invoke(
  { input: "What is the meaning of life?" },
  {
    tags: ["production", "v1.0"],
    metadata: {
      userId: "user123",
      sessionId: "session456",
      environment: "production",
      requestId: "req-abc-123",
    },
    run_name: "MyCustomRunName",
    run_id: "custom-run-id-001",  // optional deterministic run ID; appears as trace ID in LangSmith
    callbacks: [tracer],
  }
);
```

### Wait for All Traces (Critical for Scripts and Tests)

```typescript
import { waitForAllTracers } from "@langchain/core/tracers";

await model.invoke("Hello");
await waitForAllTracers();  // flush all background trace callbacks before process exits
```

**Always call `waitForAllTracers()` in scripts, tests, and serverless functions.** Without it, traces may be dropped when the process exits before the background flush completes.

---

## 3. Manual Tracing — `traceable` and RunTree

### `traceable` Wrapper

Wraps any async function to create a traced span in LangSmith. The cleanest way to instrument non-LangChain code.

```typescript
import { traceable } from "langsmith/traceable";

const myFunction = traceable(
  async (inputText: string): Promise<string> => {
    return inputText.toUpperCase();
  },
  {
    name: "my_function",        // display name in LangSmith UI (required)
    run_type: "chain",          // classify the span
    tags: ["production"],
    metadata: {
      version: "1.0.0",
      env: "prod",
    },
    tracingEnabled: true,       // override global LANGSMITH_TRACING env var
    project_name: "my-project", // route to specific LangSmith project
  }
);

const result = await myFunction("hello world");
```

### `traceable` Options Reference

| Option | Type | Description |
|--------|------|-------------|
| `name` | `string` | Display name in UI (required) |
| `run_type` | `string` | `"llm"`, `"tool"`, `"chain"`, `"retriever"`, `"embedding"`, `"prompt"`, `"parser"` |
| `tags` | `string[]` | Static tags for this run |
| `metadata` | `Record<string, any>` | Static metadata for this run |
| `tracingEnabled` | `boolean` | Force enable/disable; overrides `LANGSMITH_TRACING` env var |
| `project_name` | `string` | Route trace to a specific LangSmith project |
| `client` | `Client` | Custom LangSmith client instance |

### LLM Run with Custom Token Tracking via `getCurrentRunTree`

```typescript
import { traceable, getCurrentRunTree } from "langsmith/traceable";

const chatModel = traceable(
  async (messages: Array<{ role: string; content: string }>) => {
    const response = { role: "assistant", content: "Sure! What time?" };

    // Attach token usage to the current run
    const run = getCurrentRunTree();
    run.set({
      usage_metadata: {
        input_tokens: 27,
        output_tokens: 13,
        total_tokens: 40,
        input_token_details: { cache_read: 10 },
      },
    });

    return response;
  },
  {
    run_type: "llm",
    metadata: {
      ls_provider: "my_provider",    // enables cost lookup in LangSmith
      ls_model_name: "my_model",
    },
  }
);
```

### Tracing Generator Functions (Streaming)

```typescript
import { traceable } from "langsmith/traceable";
import OpenAI from "openai";

const openai = new OpenAI();

const streamingModel = traceable(
  async function* (messages: any[]) {
    const stream = await openai.chat.completions.create({
      model: "gpt-4.1-mini",
      messages,
      stream: true,
    });
    for await (const chunk of stream) {
      yield chunk.choices[0]?.delta?.content || "";
    }
  },
  { name: "streamingModel", run_type: "llm" }
);
```

### Manual RunTree API

Use `RunTree` when you need fine-grained control over the trace hierarchy, or when operating outside a `traceable` context.

```typescript
import { RunTree, Client } from "langsmith";

const client = new Client({ apiKey: process.env.LANGSMITH_API_KEY });

async function runPipeline() {
  // Create root run
  const pipeline = new RunTree({
    name: "Chat Pipeline",
    run_type: "chain",
    inputs: { subject: "colorful socks" },
    project_name: "my-project",
  });
  await pipeline.post();

  // Create child run
  const llmRun = pipeline.create_child({
    name: "OpenAI Call",
    run_type: "llm",
    inputs: { messages: [{ role: "user", content: "Name a store?" }] },
  });
  await llmRun.post();

  // Complete child run
  const response = { content: "Sock It To Me!" };
  llmRun.end({ output: response });
  await llmRun.patch();

  // Complete root run
  pipeline.end({ answer: response.content });
  await pipeline.patch();
}

try {
  await runPipeline();
} finally {
  await client.flush();  // ensure all traces are submitted
}
```

### RunTree Constructor Options

```typescript
interface RunTreeConfig {
  name: string;              // required
  run_type: string;          // required
  inputs?: Record<string, any>;
  outputs?: Record<string, any>;
  project_name?: string;
  parent_run?: RunTree;
  tags?: string[];
  metadata?: Record<string, any>;
  start_time?: Date;
  client?: Client;
}
```

### Distributed Tracing (Cross-Service)

```typescript
import { getCurrentRunTree } from "langsmith/run_tree";
import { traceable } from "langsmith/traceable";

// Service A: inject trace headers into outbound HTTP request
async function parentService(input: any) {
  const rt = await getCurrentRunTree();
  const headers = rt.toHeaders();
  await fetch("https://service-b/process", {
    method: "POST",
    headers: { ...headers, "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

// Service B: extract trace context from incoming headers
const processInServiceB = traceable(
  async (input: any) => {
    // This span appears as a child of the parent span from Service A
    return await model.invoke(input);
  },
  { name: "ServiceBProcessor" }
);
```

### Fetch Callbacks from `traceable` Context

When mixing `traceable`-wrapped code with LangChain runnables, use `getLangchainCallbacks()` to bridge the trace context:

```typescript
import { getLangchainCallbacks } from "langsmith/langchain";
import { traceable } from "langsmith/traceable";

const main = traceable(
  async (input: { question: string }) => {
    const callbacks = await getLangchainCallbacks();
    return await chain.invoke(input, { callbacks });
  },
  { name: "main" }
);
```

---

## 4. Run (Span) Data Format

Every operation in a trace is stored as a "run" (equivalent to an OpenTelemetry span).

### Run Type Values

| `run_type` | Description |
|------------|-------------|
| `llm` | LLM or chat model call |
| `chain` | A chain or graph node execution |
| `tool` | Tool / function call |
| `retriever` | Document retrieval |
| `embedding` | Embedding generation |
| `prompt` | Prompt template rendering |
| `parser` | Output parser |

### Complete Run Schema

```typescript
interface Run {
  id: string;                        // UUID — unique run identifier
  name: string;                      // display name
  run_type: string;                  // see table above
  inputs: Record<string, any>;       // inputs provided to the run
  outputs?: Record<string, any>;     // outputs generated
  start_time: string;                // ISO-8601
  end_time?: string;                 // ISO-8601
  status: "pending" | "success" | "error";
  error?: string;                    // error message if failed
  trace_id: string;                  // UUID of root run (equals id for root)
  parent_run_id?: string;            // UUID of parent run
  parent_run_ids: string[];          // all ancestor run IDs
  child_run_ids: string[];           // all child run IDs
  direct_child_run_ids: string[];    // direct children only
  dotted_order: string;              // hierarchical sort key
  tags: string[];
  extra: Record<string, any>;
  events: any[];                     // streaming events
  feedback_stats: Record<string, { n: number; avg: number | null }>;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_cost: number;
  prompt_cost: number;
  completion_cost: number;
  first_token_time?: string;         // time to first token (streaming)
  session_id: string;                // project/session ID
  in_dataset: boolean;
  share_token?: string;
  reference_example_id?: string;     // for evaluation runs
  app_path: string;                  // LangSmith UI path
}
```

### `dotted_order` Explained

Format: `<start_time>Z<uuid>.<child_start_time>Z<child_uuid>...`

- First segment UUID = `trace_id`
- Last segment UUID = this run's `id`
- Provides a sortable hierarchical key for the full trace tree
- Enables efficient querying of all runs within a trace without a recursive DB lookup

Example: `20240429T004912090000Zabc123.20240429T004913000000Zdef456`

### Run Tree Visualization

The LangSmith UI renders the `dotted_order` hierarchy as a visual tree. To construct a run tree programmatically:

```typescript
import { Client } from "langsmith";

const client = new Client();

// Fetch all runs in a trace
for await (const run of client.listRuns({
  project_name: "my-project",
  filter: `eq(trace_id, "trace-uuid-here")`,
})) {
  // Build tree from parent_run_id / child_run_ids
  const indent = run.parent_run_ids.length;
  console.log(" ".repeat(indent * 2) + `[${run.run_type}] ${run.name}`);
}
```

---

## 5. Callback System — 19 Callback Types Cataloged

### BaseCallbackHandler — Complete Method Table

**Package:** `@langchain/core/callbacks/base`

| # | Method | Event Trigger | Key Parameters |
|---|--------|--------------|----------------|
| 1 | `handleLLMStart` | LLM/ChatModel run starts | `llm`, `prompts[]`, `runId`, `parentRunId?`, `tags?`, `metadata?`, `runName?` |
| 2 | `handleLLMEnd` | LLM/ChatModel run completes | `output: LLMResult`, `runId`, `parentRunId?`, `tags?`, `metadata?` |
| 3 | `handleLLMError` | LLM/ChatModel throws | `error: Error`, `runId`, `parentRunId?`, `tags?`, `metadata?` |
| 4 | `handleLLMNewToken` | Streaming token received | `token: string`, `chunk: LLMChunk`, `runId`, `parentRunId?`, `tags?` |
| 5 | `handleChainStart` | Chain run starts | `chain`, `inputs`, `runId`, `parentRunId?`, `tags?`, `metadata?`, `runName?` |
| 6 | `handleChainEnd` | Chain run completes | `output: ChainValues`, `runId`, `parentRunId?`, `tags?`, `metadata?` |
| 7 | `handleChainError` | Chain run throws | `error: Error`, `runId`, `parentRunId?`, `tags?`, `metadata?` |
| 8 | `handleToolStart` | Tool run starts | `tool`, `input: string`, `runId`, `parentRunId?`, `tags?`, `metadata?`, `runName?` |
| 9 | `handleToolEnd` | Tool run completes | `output: ToolResult`, `runId`, `parentRunId?`, `tags?`, `metadata?` |
| 10 | `handleToolError` | Tool run throws | `error: Error`, `runId`, `parentRunId?`, `tags?`, `metadata?` |
| 11 | `handleToolEvent` | Streaming async-gen tool chunk | `chunk`, `runId`, `parentRunId?`, `tags?` |
| 12 | `handleAgentAction` | Agent selects an action | `action: AgentAction`, `runId`, `parentRunId?`, `tags?`, `metadata?` |
| 13 | `handleAgentEnd` | Agent execution finishes | `finish: AgentFinish`, `runId`, `parentRunId?`, `tags?`, `metadata?` |
| 14 | `handleRetrieverStart` | Retriever run starts | `retriever`, `query: string`, `runId`, `parentRunId?`, `tags?`, `metadata?`, `runName?` |
| 15 | `handleRetrieverEnd` | Retriever run completes | `documents: Document[]`, `runId`, `parentRunId?`, `tags?`, `metadata?` |
| 16 | `handleRetrieverError` | Retriever run throws | `error: Error`, `runId`, `parentRunId?`, `tags?`, `metadata?` |
| 17 | `handleText` | Generic text event | `text: string`, `runId?`, `parentRunId?`, `tags?` |
| 18 | `onRunCreate` | Run object created | `run: Run`, `runId?` |
| 19 | `persistRun` | Run data persistence (internal) | `run: Run`, `runId?` |

> `onRunUpdate` is also present on some handler variants but is not part of the public `BaseCallbackHandler` contract.

### BaseCallbackHandler Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `name` | `string` | `""` | Handler identifier; used for deduplication |
| `awaitHandlers` | `boolean` | `false` | `true` = await each handler; `false` = run in parallel |
| `ignoreLLM` | `boolean` | `false` | Skip all LLM-related callbacks (1–4) |
| `ignoreChain` | `boolean` | `false` | Skip all chain-related callbacks (5–7) |
| `ignoreRetriever` | `boolean` | `false` | Skip all retriever-related callbacks (14–16) |
| `ignoreAgent` | `boolean` | `false` | Skip agent-related callbacks (12–13) |
| `ignoreCustomEvent` | `boolean` | `false` | Skip custom event callbacks |
| `raiseError` | `boolean` | `false` | `true` = throw exceptions; `false` = log and continue |

---

## 6. Built-in Callback Handlers

### ConsoleCallbackHandler

```typescript
import { ConsoleCallbackHandler } from "@langchain/core/tracers/console";
import { ChatAnthropic } from "@langchain/anthropic";

const llm = new ChatAnthropic({
  temperature: 0,
  callbacks: [new ConsoleCallbackHandler()],
});
```

- Logs every lifecycle event to stdout with formatting
- `name = "console_callback_handler"`
- Auto-attached when `verbose: true` is set on a Runnable or globally
- **Known issue:** `runMap` and `runTreeMap` grow indefinitely in long-running processes — create a fresh instance per request or clear periodically

### UsageMetadataCallbackHandler

```typescript
import { UsageMetadataCallbackHandler } from "@langchain/core/callbacks/usage";
import { ChatOpenAI } from "@langchain/openai";

const tracker = new UsageMetadataCallbackHandler();
const model = new ChatOpenAI({ model: "gpt-4o-mini" });
await model.invoke("Hello", { callbacks: [tracker] });

console.log(tracker.usageMetadata);
// { input_tokens: 12, output_tokens: 45, total_tokens: 57 }
```

Tracks `AIMessage.usage_metadata` across all LLM calls in a run. Works out of the box with OpenAI-compatible providers.

### StreamingStdOutCallbackHandler

```typescript
import { StreamingStdOutCallbackHandler } from "@langchain/core/callbacks/streaming_stdout";
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  streaming: true,
  callbacks: [new StreamingStdOutCallbackHandler()],
});
```

Writes each streaming token to `stdout` as it arrives. Only implements `handleLLMNewToken`.

### LangChainTracer

```typescript
import { LangChainTracer } from "@langchain/core/tracers/langchain";

// Automatically active when LANGSMITH_TRACING=true + LANGSMITH_API_KEY are set
// Can also be passed explicitly for selective tracing
const tracer = new LangChainTracer({ projectName: "my-project" });
await chain.invoke(input, { callbacks: [tracer] });
```

---

## 7. Custom Callback Handlers

### Minimal Custom Handler

```typescript
import { BaseCallbackHandler } from "@langchain/core/callbacks/base";
import { LLMResult } from "@langchain/core/outputs";
import { ChatOpenAI } from "@langchain/openai";

class MyLoggingHandler extends BaseCallbackHandler {
  name = "my_logging_handler";

  async handleLLMStart(
    llm: { name: string },
    prompts: string[],
    runId: string
  ) {
    console.log(`[${new Date().toISOString()}] LLM ${llm.name} started (${runId})`);
    console.log("Prompt:", prompts[0].substring(0, 100) + "...");
  }

  async handleLLMEnd(output: LLMResult, runId: string) {
    console.log("LLM completed:", output.generations[0][0].text);
  }

  async handleLLMError(err: Error, runId: string) {
    console.error("LLM error:", err.message);
  }
}

const model = new ChatOpenAI({ callbacks: [new MyLoggingHandler()] });
```

### Full Signature for Common Methods

```typescript
import { BaseCallbackHandler, LLMResult } from "@langchain/core/callbacks/base";
import { AgentAction, AgentFinish } from "@langchain/core/agents";
import { LLMChunk } from "@langchain/core/outputs";

class MyHandler extends BaseCallbackHandler {
  name = "my_handler";

  async handleLLMStart(
    llm: { name: string },
    prompts: string[],
    runId: string,
    parentRunId?: string,
    tags?: string[],
    metadata?: Record<string, unknown>,
    runName?: string
  ): Promise<void> {
    console.log(`LLM started: ${llm.name}, runId: ${runId}`);
    if (metadata) console.log("Metadata:", metadata);
  }

  async handleLLMEnd(
    output: LLMResult,
    runId: string,
    parentRunId?: string,
    tags?: string[],
    metadata?: Record<string, unknown>
  ): Promise<void> {
    // Access token usage
    const usage = output.llmOutput?.usage_metadata;
    if (usage) {
      console.log(`Tokens: prompt=${usage.prompt_tokens} completion=${usage.completion_tokens}`);
    }
  }

  async handleLLMNewToken(
    token: string,
    chunk: LLMChunk,
    runId: string
  ): Promise<void> {
    process.stdout.write(token);
  }

  async handleChainStart(
    chain: { name: string },
    inputs: Record<string, unknown>,
    runId: string,
    parentRunId?: string
  ): Promise<void> {
    // NOTE: chain may be null in LangChain v0.3+; always null-check
    const chainName = chain?.name ?? "unknown";
    console.log(`Chain started: ${chainName}`);
  }

  async handleToolStart(
    tool: { name: string },
    input: string,
    runId: string
  ): Promise<void> {
    console.log(`Tool started: ${tool.name}, input: ${input}`);
  }

  async handleAgentAction(action: AgentAction, runId: string): Promise<void> {
    console.log(`Agent action: ${action.tool} with input: ${action.toolInput}`);
  }

  async handleAgentEnd(finish: AgentFinish, runId: string): Promise<void> {
    console.log("Agent finished:", finish.returnValues);
  }
}
```

### Custom Handler for LangGraph `createReactAgent`

```typescript
import { BaseCallbackHandler } from "@langchain/core/callbacks/base";
import { LLMResult } from "@langchain/core/outputs";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { ChatOpenAI } from "@langchain/openai";

class AgentObserver extends BaseCallbackHandler {
  name = "agent_observer";

  async handleLLMStart(llm: any, prompts: string[], runId: string) {
    console.log("FULL LLM INPUT:", JSON.stringify(prompts, null, 2));
  }

  async handleLLMEnd(output: LLMResult, runId: string) {
    console.log("LLM OUTPUT:", JSON.stringify(output, null, 2));
  }
}

const llm = new ChatOpenAI({ model: "gpt-4.1-mini" });
const agent = createReactAgent({ llm, tools: [] });

// CORRECT: pass callbacks via invoke config to see full tool definitions
const response = await agent.invoke(
  { messages: [{ role: "user", content: "What is 2+2?" }] },
  { callbacks: [new AgentObserver()] }  // NOT in createReactAgent constructor
);
```

### Callback Propagation — Three Attachment Points

```typescript
// 1. Constructor callbacks — always-on, propagates to all descendants
const chain = new SomeChain({ callbacks: [handler] });

// 2. Invoke-time callbacks — only for this call, propagates to all descendants
const result = await chain.invoke(input, { callbacks: [handler] });

// 3. Non-inheritable callbacks — only this runnable, NOT propagated to children
const result = await chain.invoke(input, {
  callbacks: [{ handler, inheritable: false }],
});
```

When both constructor and invoke-time callbacks are present, they are **merged** (both fire). To replace constructor callbacks:

```typescript
import { CallbackManager } from "@langchain/core/callbacks/manager";

const result = await chain.invoke(input, {
  callbacks: new CallbackManager([newHandler]), // replaces constructor callbacks
});
```

### Structured Observability Handler (Production Pattern)

```typescript
import { BaseCallbackHandler } from "@langchain/core/callbacks/base";
import { LLMResult } from "@langchain/core/outputs";

class ObservabilityHandler extends BaseCallbackHandler {
  name = "observability";
  private metrics = new Map<string, number>();
  private errors: Error[] = [];

  async handleLLMStart(llm: any, prompts: string[], runId: string, parentRunId?: string, tags?: string[]) {
    this.metrics.set(`run:${runId}:start`, Date.now());
  }

  async handleLLMEnd(output: LLMResult, runId: string, parentRunId?: string, tags?: string[], metadata?: Record<string, unknown>) {
    const startTime = this.metrics.get(`run:${runId}:start`) ?? Date.now();
    const latency = Date.now() - startTime;

    console.log(JSON.stringify({
      event: "llm_complete",
      runId,
      parentRunId,
      tags,
      latencyMs: latency,
      tokens: output.llmOutput?.usage_metadata,
    }));

    this.metrics.delete(`run:${runId}:start`);
  }

  async handleLLMError(error: Error, runId: string, parentRunId?: string, tags?: string[]) {
    this.errors.push(error);
    console.error(JSON.stringify({ event: "llm_error", runId, error: error.message, tags }));
  }
}
```

---

## 8. Metadata, Tags, and Correlation IDs

### Recommended Metadata Keys

| Key | Purpose |
|-----|---------|
| `userId` | Track per-user behavior and costs |
| `sessionId` | Group related interactions |
| `correlationId` | Link traces to request IDs in other systems |
| `tenantId` | Multi-tenant isolation |
| `environment` | `"production"` / `"staging"` / `"development"` |
| `version` | Agent/prompt version for regression tracking |
| `ls_provider` | Used by LangSmith for automatic cost lookup |
| `ls_model_name` | Used by LangSmith for model-specific cost tracking |

### Static Metadata at Trace Level

```typescript
import { LangChainTracer } from "@langchain/core/tracers/tracer_langchain";

const tracer = new LangChainTracer({ projectName: "email-agent-test" });

await agent.invoke(
  { messages: [{ role: "user", content: "Send email to alice@example.com" }] },
  {
    callbacks: [tracer],
    tags: ["production", "email-assistant", "v1.0"],
    metadata: {
      userId: "user123",
      sessionId: "session456",
      environment: "production",
      correlationId: "req-abc-123",
      tenantId: "tenant-foo",
    },
  }
);
```

### Dynamic Metadata Inside a Run

```typescript
import { getCurrentRunTree } from "langsmith/run_trees";
import { traceable } from "langsmith/traceable";

const myFunction = traceable(
  async (input: string) => {
    const rt = getCurrentRunTree();
    rt.metadata["request_size"] = input.length;
    rt.metadata["processed_at"] = new Date().toISOString();
    rt.tags.push("dynamic-tag");
    return input.toUpperCase();
  },
  { name: "myFunction" }
);
```

### Predefined Trace ID (Correlate with External Systems)

```typescript
import { v4 as uuidv4 } from "uuid";
import { LangChainTracer } from "@langchain/core/tracers/tracer_langchain";

const customRunId = uuidv4();
await chain.invoke(input, {
  runId: customRunId,  // LangSmith uses this as the trace ID
  callbacks: [new LangChainTracer()],
});
```

### Conditional Tracing and Project Routing

```typescript
import { traceable } from "langsmith/traceable";
import { LangChainTracer } from "@langchain/core/tracers/tracer_langchain";
import { Client } from "langsmith";

// Disable tracing for specific calls (highest-priority override)
const processText = traceable(
  (inputText: string) => inputText.toUpperCase(),
  { name: "process_text", tracingEnabled: false }
);

// Multi-tenant routing per project
function getTracerForTenant(tenantId: string): LangChainTracer {
  return new LangChainTracer({ projectName: `tenant-${tenantId}` });
}

// Multi-workspace routing
async function handleRequest(tenantId: string, input: any) {
  const tenantClient = new Client({
    apiKey: process.env.LANGSMITH_API_KEY,
    workspaceId: tenantWorkspaceMap[tenantId],
  });
  const tracer = new LangChainTracer({
    client: tenantClient,
    projectName: `tenant-${tenantId}`,
  });
  return await agent.invoke(input, {
    callbacks: [tracer],
    metadata: { tenantId, environment: "production" },
  });
}
```

**`tracingEnabled` Priority (Highest to Lowest):**

1. `tracingEnabled` field in `traceable()` options
2. Global `LANGSMITH_TRACING` environment variable

---

## 9. Data Privacy — Anonymizers

Mask sensitive data before it reaches LangSmith storage:

```typescript
import { createAnonymizer } from "langsmith/anonymizer";
import { Client } from "langsmith";
import { LangChainTracer } from "@langchain/core/tracers/tracer_langchain";
import { StateGraph, Annotation } from "@langchain/langgraph";

const anonymizer = createAnonymizer([
  { pattern: /\b\d{3}-?\d{2}-?\d{4}\b/, replace: "<ssn>" },
  { pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/, replace: "<email>" },
  { pattern: /\b4[0-9]{12}(?:[0-9]{3})?\b/, replace: "<credit_card>" },
]);

const langsmithClient = new Client({ anonymizer });
const tracer = new LangChainTracer({ client: langsmithClient });

export const graph = new StateGraph(StateAnnotation)
  .addNode("agent", callModel)
  .addEdge("__start__", "agent")
  .compile()
  .withConfig({ callbacks: [tracer] });
```

Use cases: GDPR (remove PII before cloud storage), HIPAA (mask healthcare identifiers), zero-retention clients.

---

## 10. Cost and Token Tracking

### Automatic Cost Tracking

LangSmith automatically computes costs when token counts are present and `ls_provider` / `ls_model_name` metadata matches a model entry in your LangSmith workspace.

```typescript
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  modelName: "gpt-4.1-mini",
  metadata: {
    ls_provider: "openai",
    ls_model_name: "gpt-4.1-mini",
  },
});
```

### Usage Metadata Schema

```typescript
interface UsageMetadata {
  input_tokens?: number;
  output_tokens?: number;
  total_tokens?: number;
  input_token_details?: Record<string, number>;   // e.g., { cache_read: 10 }
  output_token_details?: Record<string, number>;  // e.g., { reasoning: 500 }
  input_cost?: number;
  output_cost?: number;
  total_cost?: number;
  input_cost_details?: Record<string, number>;
  output_cost_details?: Record<string, number>;
}
```

### Manually Attaching Usage Metadata

```typescript
import { traceable, getCurrentRunTree } from "langsmith/traceable";
import OpenAI from "openai";

const openai = new OpenAI();

const myLLMCall = traceable(
  async (messages: any[]) => {
    const response = await openai.chat.completions.create({
      model: "gpt-4.1-mini",
      messages,
    });

    const run = getCurrentRunTree();
    run.set({
      usage_metadata: {
        input_tokens: response.usage?.prompt_tokens,
        output_tokens: response.usage?.completion_tokens,
        total_tokens: response.usage?.total_tokens,
      },
    });

    return response;
  },
  { run_type: "llm" }
);
```

### Token Counting Callback (Production Pattern)

Works with any model, including those without native `usage_metadata`:

```typescript
import { BaseCallbackHandler, LLMResult } from "@langchain/core/callbacks/base";
// npm install @dqbd/tiktoken
import { get_encoding } from "@dqbd/tiktoken";

const enc = get_encoding("cl100k_base"); // GPT-4/GPT-4o family

const MODEL_PRICING: Record<string, { prompt: number; completion: number }> = {
  "gpt-4o-mini":  { prompt: 0.15  / 1_000_000, completion: 0.60  / 1_000_000 },
  "gpt-4o":       { prompt: 2.50  / 1_000_000, completion: 10.00 / 1_000_000 },
  "gpt-4.1-mini": { prompt: 0.40  / 1_000_000, completion: 1.60  / 1_000_000 },
};

class TokenCostCallbackHandler extends BaseCallbackHandler {
  name = "token_cost_tracker";
  promptTokens = 0;
  completionTokens = 0;
  promptCost = 0;
  completionCost = 0;
  totalCost = 0;

  async handleLLMStart(_llm: { name: string }, prompts: string[]) {
    for (const prompt of prompts) {
      this.promptTokens += enc.encode(prompt).length;
    }
  }

  async handleLLMNewToken(_token: string) {
    this.completionTokens += 1;
  }

  async handleLLMEnd(output: LLMResult) {
    // Prefer usage_metadata if available (more accurate)
    if (output.llmOutput?.usage_metadata) {
      const usage = output.llmOutput.usage_metadata;
      this.promptTokens = usage.prompt_tokens ?? this.promptTokens;
      this.completionTokens = usage.completion_tokens ?? this.completionTokens;
    }

    const modelName = (output.llmOutput?.model_name ?? "gpt-4o-mini") as string;
    const pricing = MODEL_PRICING[modelName] ?? MODEL_PRICING["gpt-4o-mini"];

    this.promptCost = this.promptTokens * pricing.prompt;
    this.completionCost = this.completionTokens * pricing.completion;
    this.totalCost = this.promptCost + this.completionCost;
  }

  getSummary() {
    return {
      promptTokens: this.promptTokens,
      completionTokens: this.completionTokens,
      totalTokens: this.promptTokens + this.completionTokens,
      promptCost: `$${this.promptCost.toFixed(6)}`,
      completionCost: `$${this.completionCost.toFixed(6)}`,
      totalCost: `$${this.totalCost.toFixed(6)}`,
    };
  }

  reset() {
    this.promptTokens = 0;
    this.completionTokens = 0;
    this.promptCost = this.completionCost = this.totalCost = 0;
  }
}

// Usage
const tracker = new TokenCostCallbackHandler();
const model = new ChatOpenAI({ model: "gpt-4o-mini" });
await model.invoke("Explain quantum computing", { callbacks: [tracker] });
console.log(tracker.getSummary());
```

### Model Pricing Map (LangSmith UI)

Configure under LangSmith UI → Settings → Models:

| Field | Description |
|-------|-------------|
| `Model Name` | Display name |
| `Input Price` | Cost per 1M input tokens (USD) |
| `Output Price` | Cost per 1M output tokens (USD) |
| `Input/Output Price Breakdown` | Per-type pricing (e.g., `cache_read`) |
| `Match Pattern` | Regex matching `ls_model_name` in metadata |
| `Provider` | Matches `ls_provider` in metadata |
| `Model Activation Date` | When this pricing entry is valid from |

---

## 11. Dashboards and Monitoring

### Prebuilt Dashboard Sections

| Section | Metrics |
|---------|---------|
| **Traces** | Trace count, latency, error rates |
| **LLM Calls** | LLM call count and latency (runs with type `"llm"`) |
| **Cost & Tokens** | Total & per-trace token counts and costs, broken down by token type |
| **Tools** | Run counts, error rates, latency for tool runs (top 5 by name) |
| **Run Types** | Run counts, error rates, latency by run type (top 5) |
| **Feedback Scores** | Aggregate stats for top 5 feedback types |

### Custom Dashboard Charts

Configure via:
1. Select one or more tracing projects
2. Apply chart filters to narrow runs
3. Pick Y-axis metric (latency, token usage, cost, error rate, feedback score)
4. Split via "Group by" (top 5 elements) or manual data series filters
5. Choose chart type (line or bar)
6. Save, clone, or delete

**Important:** Metadata does NOT propagate automatically from parent runs to child runs. To group dashboard data by a custom metadata key (e.g., `userId`), attach that key to both the root run AND each LLM child run.

### Production Monitoring Checklist

- Trace count trends — detect traffic anomalies
- Error rates — alert when error rate exceeds threshold (e.g., >5%)
- P50/P95 latency — track SLA compliance
- Token usage trends — cost forecasting
- Tool call distribution — identify most-used / failing tools
- Feedback score trends — detect quality degradation

---

## 12. Alerts

LangSmith Alerts (available on Plus/Enterprise) send real-time notifications when thresholds are breached.

### Supported Alert Metrics

| Metric | Description |
|--------|-------------|
| **Error Count** | Absolute count of errors in window |
| **Error Rate** | Percentage of errored runs |
| **Average Latency** | Mean response time |
| **Average Feedback Score** | Mean of user/evaluator scores |

### Alert Configuration

- **Filters**: narrow to specific run subsets (by model, tool call, run type, tags, metadata)
- **Aggregation windows**: 5 minutes or 15 minutes
- **Threshold**: numeric value (e.g., error rate > 5%, latency > 2s, feedback < 0.7)

### Notification Integrations

- **PagerDuty** — for on-call routing
- **Custom webhook** — for Slack, Teams, or any HTTP endpoint

### Setup

1. Go to LangSmith UI → Monitoring → Alerts
2. Click **New Alert**
3. Select metric, set filters and threshold
4. Configure notification channel (PagerDuty service key or webhook URL)
5. Save

Docs: `https://docs.smith.langchain.com/observability/how_to_guides/alerts`

### Roadmap (future)

- Run-count alerts
- LLM token-usage alerts
- Change alerts (relative threshold, e.g., latency spike ≥25%)
- Custom time-window definitions

---

## 13. Trace Filtering and Export

### Filter Query Language — Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equals | `eq(run_type, "llm")` |
| `neq` | Not equals | `neq(error, null)` |
| `gt` | Greater than | `gt(latency, "5s")` |
| `gte` | Greater than or equal | `gte(total_tokens, 1000)` |
| `lt` | Less than | `lt(start_time, "2024-01-01T00:00:00Z")` |
| `lte` | Less than or equal | `lte(total_cost, 0.01)` |
| `has` | Tag or metadata key presence | `has(tags, "production")` |
| `search` | Full-text substring search | `search("classification")` |
| `and` | Logical AND | `and(eq(run_type, "llm"), gt(latency, "2s"))` |

### Query Runs via TypeScript SDK

```typescript
import { Client } from "langsmith";

const client = new Client();

// LLM runs in last 24 hours
const llmRuns = await client.listRuns({
  project_name: "my-project",
  start_time: new Date(Date.now() - 86400000),
  run_type: "llm",
});

// Root runs only
const rootRuns = await client.listRuns({
  project_name: "my-project",
  is_root: true,
});

// Complex filter: errors or low-correctness runs
for await (const run of client.listRuns({
  project_name: "my-project",
  filter: `and(
    gt(start_time, "2023-07-15T12:34:56Z"),
    or(neq(error, null), and(eq(feedback_key, "Correctness"), eq(feedback_score, 0.0)))
  )`,
})) {
  console.log(run.id, run.name, run.run_type);
}

// Runs with specific tag (e.g., git commit hash)
const taggedRuns = await client.listRuns({
  project_name: "my-project",
  filter: 'has(tags, "2aa1cf4")',
});

// Tree filter: root had good feedback AND had a specific tool call
const runs = await client.listRuns({
  project_name: "my-project",
  filter: 'eq(name, "RetrieveDocs")',
  trace_filter: 'and(eq(feedback_key, "user_score"), eq(feedback_score, 1))',
  tree_filter: 'eq(name, "ExpandQuery")',
});

// Read single run
const run = await client.readRun("a36092d2-...");
console.log(run.inputs, run.outputs);
```

### Rate Limits for `listRuns`

| Query Type | Limit | Window |
|------------|-------|--------|
| Short window (≤7 days) | 10 req | 10s |
| Large window (>7 days) | 3 req | 10s |
| Full-text search, short | 3 req | 10s |
| Full-text search, large | 1 req | 10s |
| Select `child_run_ids`, short | 3 req | 10s |
| Select `child_run_ids`, large | 1 req | 10s |

### Bulk Export (Plus/Enterprise)

Export trace data to S3-compatible storage in Parquet format:

```typescript
// 1. Create destination
const destResponse = await fetch("https://api.smith.langchain.com/api/v1/bulk-exports/destinations", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": process.env.LANGSMITH_API_KEY!,
    "X-Tenant-Id": process.env.LANGSMITH_WORKSPACE_ID!,
  },
  body: JSON.stringify({
    destination_type: "s3",
    display_name: "my-analytics-bucket",
    config: {
      bucket_name: "my-trace-exports",
      prefix: "langgraph-traces/",
      region: "us-east-1",
    },
    credentials: {
      access_key_id: process.env.AWS_ACCESS_KEY_ID,
      secret_access_key: process.env.AWS_SECRET_ACCESS_KEY,
    },
  }),
});

// 2. Create one-time export job
const exportResponse = await fetch("https://api.smith.langchain.com/api/v1/bulk-exports", {
  method: "POST",
  headers: { "Content-Type": "application/json", "X-API-Key": process.env.LANGSMITH_API_KEY! },
  body: JSON.stringify({
    bulk_export_destination_id: "dest-id",
    session_id: "project-uuid",
    start_time: "2024-01-01T00:00:00Z",
    end_time: "2024-01-31T23:59:59Z",
    format_version: "v2_beta",
    filter: 'eq(run_type, "llm")',   // optional
    export_fields: ["id", "name", "run_type", "total_tokens", "total_cost"],
  }),
});

// 3. Monitor export status
const statusResponse = await fetch(
  `https://api.smith.langchain.com/api/v1/bulk-exports/${exportId}`,
  { headers: { "X-API-Key": process.env.LANGSMITH_API_KEY! } }
);
const { status } = await statusResponse.json();
// status: "CREATED" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED" | "TIMEDOUT"
```

Exported Parquet partition structure:
```
s3://bucket/prefix/export_id=<id>/tenant_id=<tid>/session_id=<sid>/runs/year=<Y>/month=<M>/day=<D>/
```

Timeout: 72 hours per export job.

---

## 14. Webhook Automation

LangSmith can POST trace data to your webhook endpoint when automation rules trigger.

### Webhook Payload Structure

```json
{
  "rule_id": "rule-uuid",
  "start_time": "2024-01-01T00:00:00Z",
  "end_time": "2024-01-01T00:05:00Z",
  "runs": [
    {
      "id": "run-uuid",
      "trace_id": "trace-uuid",
      "status": "success",
      "is_root": true,
      "run_type": "chain",
      "name": "my-agent",
      "total_tokens": 1234,
      "total_cost": 0.00123,
      "inputs": {},
      "outputs": {},
      "inputs_s3_urls": {},
      "outputs_s3_urls": {},
      "feedback_stats": {
        "user_score": { "n": 2, "avg": 0.5 },
        "correctness": { "n": 1, "avg": 1.0 }
      },
      "app_path": "/traces/trace-uuid"
    }
  ]
}
```

### Webhook Handler (TypeScript/Hono)

```typescript
import { Hono } from "hono";
import { Client } from "langsmith";

const app = new Hono();
const langsmith = new Client();

app.post("/langsmith-webhook", async (c) => {
  // Validate secret appended to webhook URL
  const secret = c.req.query("secret");
  if (secret !== process.env.LANGSMITH_WEBHOOK_SECRET) {
    return c.json({ error: "Unauthorized" }, 401);
  }

  const data = await c.req.json();

  for (const run of data.runs) {
    // Auto-add low-scoring traces to a fine-tuning dataset
    const feedback = run.feedback_stats?.user_score;
    if (feedback && feedback.avg < 0.5) {
      await langsmith.createExample(
        { question: run.inputs?.messages?.[0]?.content },
        { answer: run.outputs?.messages?.at(-1)?.content },
        { datasetName: "low-score-examples" }
      );
    }
  }

  return c.json({ status: "ok" });
});
```

### Webhook Delivery Policy

| Condition | Action |
|-----------|--------|
| Connection failure | Retry up to 2 times, then fail |
| Response time > 5s | Mark as failed (no retry) |
| 5xx status, < 5s response | Retry up to 2 times with exponential backoff |
| 4xx status | Mark as failed (no retry) |

Append secret to URL: `https://api.example.com/langsmith-webhook?secret=your-secret-token`

---

## Known Pitfalls

| Pitfall | Affected Components | Fix |
|---------|--------------------|----|
| Traces dropped in serverless | Scripts, Lambda, Vercel | Set `LANGCHAIN_CALLBACKS_BACKGROUND=false`; call `waitForAllTracers()` before exit |
| `handleChainStart` receives `chain=null` (v0.3+) | All custom chain handlers | Always null-check: `chain?.name ?? "unknown"` |
| `ConsoleCallbackHandler` memory accumulation | Long-running servers | Create fresh handler per request; clear `runMap` periodically |
| Duplicate callback firing | Constructor + invoke-time handlers | Use unique `name` property; avoid attaching same handler in both places |
| `awaitHandlers=false` race conditions | Handlers with side effects | Set `awaitHandlers = true` when handler must complete before chain continues |
| `run_id` collisions with deterministic IDs | Multi-tenant, parallel runs | Use `uuidv4()` per request; never reuse `run_id` across concurrent requests |
| `on_chain_start serialized=None` warning | v0.3+ migration | Null-check all uses of `serialized.id` and `serialized.name` |
| Streaming token count inaccuracy | `handleLLMNewToken` counters | Use `usage_metadata` when available; tiktoken for estimation only |
| `handleLLMNewToken` + tiktoken underestimates prompt tokens | Chat models | Use `format_prompt` + tiktoken for chat messages |
| `usage_metadata` unreliable during streaming | Non-OpenAI providers | Wrap the provider client directly for token counts |
| LangGraph `createReactAgent` callbacks missing | LangGraph prebuilt agent | Pass callbacks in `invoke` config, NOT in `createReactAgent` constructor |
| Metadata not propagated to child runs | Dashboard group-by queries | Explicitly attach metadata to both root run AND each LLM child run |
| API key in `LANGSMITH_API_KEY` hardcoded in code | Production deployments | Always load from environment secrets; never commit to git |
| EU data residency missed | Regulated environments | Use `https://eu.api.smith.langchain.com` endpoint explicitly |
