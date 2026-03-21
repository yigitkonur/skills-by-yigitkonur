# Observability & Debugging Reference

> All patterns verified 2026-03-21
> Packages: langchain@1.2.35, @langchain/core@1.1.34, @langchain/openai@1.3.0, @langchain/langgraph@1.2.5, langsmith
> Model: anthropic/claude-sonnet-4-6 via OpenRouter

---

## 1. LangSmith Setup

### Environment Variables

LangSmith tracing activates automatically when these env vars are set. No code changes required.

```bash
# Required — enables automatic tracing for ALL LangChain calls
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY="lsv2_pt_..."  # from smith.langchain.com > Settings > API Keys

# Optional — organizes traces by project (defaults to "default")
export LANGSMITH_PROJECT="my-project-name"

# Optional — custom endpoint (for self-hosted LangSmith)
export LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
```

**In a Next.js `.env.local`**:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxxxxxxxxxx
LANGSMITH_PROJECT=my-app-production
```

**Critical**: These env vars must be set on the **server side** where LangChain runs. Client-side code (React components) does not and should not have access to `LANGSMITH_API_KEY`.

---

### Automatic Tracing — Zero Code Changes

Once env vars are set, every LangChain operation is automatically traced:

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";

const model = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

const chain = ChatPromptTemplate.fromMessages([
  ["system", "You are a helpful assistant."],
  ["human", "{input}"],
]).pipe(model).pipe(new StringOutputParser());

// This call is AUTOMATICALLY traced in LangSmith — no extra code needed
const result = await chain.invoke({ input: "What is TypeScript?" });
```

**What gets traced automatically**:
- All `.invoke()`, `.stream()`, `.batch()` calls
- Prompt template rendering
- Model calls (including token usage, latency)
- Output parser execution
- Tool calls and results
- Agent step-by-step execution
- LangGraph node transitions

**Trace hierarchy**: LangSmith shows nested traces — a chain trace contains child traces for each step (prompt → model → parser). Agent traces show the full tool-calling loop.

---

## 2. Manual Tracing with traceable()

### Wrapping Custom Functions

**When to use**: You have custom business logic (API calls, database queries, processing) that you want to appear in LangSmith traces alongside LangChain operations.
**Packages**: `langsmith`

```bash
npm install langsmith
```

```typescript
import { traceable } from "langsmith/traceable";

// Wrap any async function to make it traceable
const fetchUserData = traceable(
  async (userId: string): Promise<{ name: string; email: string }> => {
    const response = await fetch(`https://api.example.com/users/${userId}`);
    return response.json();
  },
  {
    name: "fetch_user_data",       // appears in LangSmith UI
    run_type: "retriever",          // "llm" | "chain" | "tool" | "retriever" | "embedding"
    metadata: { service: "user-api" },
  }
);

// Now this function appears in LangSmith traces
const user = await fetchUserData("user-123");
```

### Nesting Traceable Functions

```typescript
import { traceable } from "langsmith/traceable";

const processOrder = traceable(
  async (orderId: string) => {
    // These sub-calls appear as children in the trace
    const order = await fetchOrder(orderId);     // traceable
    const validated = await validateOrder(order); // traceable
    const result = await submitOrder(validated);  // traceable
    return result;
  },
  { name: "process_order", run_type: "chain" }
);

const fetchOrder = traceable(
  async (orderId: string) => {
    return { id: orderId, items: ["item1", "item2"] };
  },
  { name: "fetch_order", run_type: "retriever" }
);

const validateOrder = traceable(
  async (order: any) => {
    return { ...order, validated: true };
  },
  { name: "validate_order", run_type: "tool" }
);

const submitOrder = traceable(
  async (order: any) => {
    return { status: "submitted", orderId: order.id };
  },
  { name: "submit_order", run_type: "tool" }
);
```

**Result in LangSmith**: A parent trace `process_order` with three child traces nested inside.

---

### wrapOpenAI — Tracing Direct OpenAI SDK Calls

**When to use**: You're using the OpenAI SDK directly (not through LangChain) but still want traces in LangSmith.

```typescript
import { wrapOpenAI } from "langsmith/wrappers";
import OpenAI from "openai";

const openai = wrapOpenAI(new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
}));

// Now direct OpenAI calls are traced in LangSmith
const completion = await openai.chat.completions.create({
  model: "gpt-4o",
  messages: [{ role: "user", content: "Hello" }],
});
```

**Note**: This is useful for hybrid codebases that mix LangChain and direct OpenAI SDK calls.

---

## 3. LangSmith Evaluation

### Basic Evaluation Pattern

**When to use**: You want to systematically test your LangChain application against a dataset of examples.
**Packages**: `langsmith`

```typescript
import { Client } from "langsmith";
import { evaluate } from "langsmith/evaluation";

const client = new Client();

// Step 1: Create a dataset
const dataset = await client.createDataset("qa-test-set", {
  description: "Question-answer test cases",
});

// Step 2: Add examples to the dataset
await client.createExamples({
  inputs: [
    { question: "What is TypeScript?" },
    { question: "What is React?" },
    { question: "What is Node.js?" },
  ],
  outputs: [
    { answer: "A typed superset of JavaScript" },
    { answer: "A JavaScript library for building user interfaces" },
    { answer: "A JavaScript runtime built on Chrome's V8 engine" },
  ],
  datasetId: dataset.id,
});

// Step 3: Define your target function (the thing you're testing)
async function myChain(input: { question: string }): Promise<{ answer: string }> {
  const result = await chain.invoke({ input: input.question });
  return { answer: result };
}

// Step 4: Define evaluators
function correctnessEvaluator({
  input,
  prediction,
  reference,
}: {
  input: { question: string };
  prediction: { answer: string };
  reference: { answer: string };
}): { key: string; score: number } {
  const isCorrect = prediction.answer
    .toLowerCase()
    .includes(reference.answer.toLowerCase());
  return { key: "correctness", score: isCorrect ? 1 : 0 };
}

// Step 5: Run evaluation
const results = await evaluate(myChain, {
  data: "qa-test-set",
  evaluators: [correctnessEvaluator],
  experimentPrefix: "qa-v1",
});

console.log("Evaluation results:", results);
// Results viewable in LangSmith UI under Datasets & Experiments
```

---

## 4. Langfuse Alternative

### Setup

[Langfuse](https://langfuse.com) is an open-source alternative to LangSmith for LLM observability.

```bash
npm install langfuse-langchain
```

```typescript
import { CallbackHandler } from "langfuse-langchain";

const langfuseHandler = new CallbackHandler({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
  secretKey: process.env.LANGFUSE_SECRET_KEY!,
  baseUrl: "https://cloud.langfuse.com", // or self-hosted URL
});

// Pass as callback to any LangChain call
const result = await chain.invoke(
  { input: "What is TypeScript?" },
  { callbacks: [langfuseHandler] }
);
```

### With createAgent

```typescript
import { createAgent } from "langchain";
import { CallbackHandler } from "langfuse-langchain";

const langfuseHandler = new CallbackHandler({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
  secretKey: process.env.LANGFUSE_SECRET_KEY!,
  baseUrl: "https://cloud.langfuse.com",
});

const agent = createAgent({
  model,
  tools: [searchTool],
  prompt: "You are a helpful assistant.",
});

const result = await agent.invoke(
  { messages: [{ role: "user", content: "Search for TypeScript news" }] },
  { callbacks: [langfuseHandler] }
);
```

**Langfuse vs LangSmith**:
- LangSmith: First-party, deepest integration, automatic tracing via env vars
- Langfuse: Open-source, self-hostable, requires explicit callback handler
- Both provide: trace visualization, cost tracking, latency analysis, evaluation

**Reference**: [Langfuse LangChain.js Integration Guide](https://langfuse.com/guides/cookbook/js_integration_langchain)

---

## 5. Debugging Patterns

### Verbose Mode

Enable detailed logging for all LangChain operations:

```typescript
import { ChatOpenAI } from "@langchain/openai";

// Option A: Per-model verbose
const model = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  verbose: true, // logs prompts and responses to console
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

// Option B: Global verbose (affects ALL LangChain runnables)
import { setVerbose } from "@langchain/core/globals";
setVerbose(true);
```

**What verbose mode shows**: Full prompt text sent to model, full response text, tool call details, timing information.

### Custom Callbacks for Debugging

```typescript
import { BaseCallbackHandler } from "@langchain/core/callbacks/base";

class DebugCallbackHandler extends BaseCallbackHandler {
  name = "debug_handler";

  async handleLLMStart(
    llm: any,
    prompts: string[],
    runId: string
  ): Promise<void> {
    console.log(`🤖 LLM Start [${runId}]`);
    console.log(`   Prompts: ${prompts.length} message(s)`);
  }

  async handleLLMEnd(output: any, runId: string): Promise<void> {
    const tokenUsage = output.llmOutput?.tokenUsage;
    console.log(`🤖 LLM End [${runId}]`);
    if (tokenUsage) {
      console.log(`   Tokens: ${tokenUsage.promptTokens} in, ${tokenUsage.completionTokens} out`);
    }
  }

  async handleLLMError(error: Error, runId: string): Promise<void> {
    console.error(`❌ LLM Error [${runId}]: ${error.message}`);
  }

  async handleToolStart(
    tool: any,
    input: string,
    runId: string
  ): Promise<void> {
    console.log(`🔧 Tool Start: ${tool.name} [${runId}]`);
    console.log(`   Input: ${input}`);
  }

  async handleToolEnd(output: string, runId: string): Promise<void> {
    console.log(`🔧 Tool End [${runId}]: ${output.substring(0, 100)}...`);
  }

  async handleToolError(error: Error, runId: string): Promise<void> {
    console.error(`❌ Tool Error [${runId}]: ${error.message}`);
  }
}

// Use in any LangChain call
const handler = new DebugCallbackHandler();
const result = await chain.invoke(
  { input: "hello" },
  { callbacks: [handler] }
);
```

---

## 6. Production Observability

### What to Monitor

| Metric | Why | How to Get It |
|--------|-----|---------------|
| **Latency (p50, p95, p99)** | User experience, SLA compliance | LangSmith trace duration |
| **Token usage per request** | Cost control, budget alerts | `AIMessage.usage_metadata` |
| **Error rate** | Reliability, model availability | LangSmith error traces + custom logging |
| **Tool success rate** | Tool reliability, schema issues | Count tool errors vs successes in traces |
| **Cost per request** | Budget management | Token usage × model pricing |
| **Time to first token (TTFT)** | Perceived responsiveness | First `on_chat_model_stream` event timestamp |
| **Agent loop iterations** | Runaway agents, efficiency | Count `model_request` node invocations in traces |
| **Cache hit rate** | Cost optimization effectiveness | Custom cache middleware metrics |

### Token Usage from AIMessage

```typescript
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  model: "anthropic/claude-sonnet-4-6",
  configuration: {
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_API_KEY!,
  },
});

const response = await model.invoke("Explain TypeScript in one sentence.");

// Token usage is on the response message
const usage = response.usage_metadata;
if (usage) {
  console.log(`Input tokens:  ${usage.input_tokens}`);
  console.log(`Output tokens: ${usage.output_tokens}`);
  console.log(`Total tokens:  ${usage.total_tokens}`);
}

// For agent responses, get the last AIMessage
const agentResult = await agent.invoke({
  messages: [{ role: "user", content: "Search for news" }],
});
const lastMessage = agentResult.messages[agentResult.messages.length - 1];
if (lastMessage.usage_metadata) {
  console.log("Final response tokens:", lastMessage.usage_metadata);
}
```

### Cost Tracking Helper

```typescript
// Pricing per 1M tokens (example rates — adjust for your models)
const PRICING: Record<string, { input: number; output: number }> = {
  "anthropic/claude-sonnet-4-6": { input: 3.0, output: 15.0 },
  "openai/gpt-4o": { input: 2.5, output: 10.0 },
  "openai/gpt-4o-mini": { input: 0.15, output: 0.6 },
};

function calculateCost(
  model: string,
  inputTokens: number,
  outputTokens: number
): number {
  const price = PRICING[model];
  if (!price) return 0;
  return (
    (inputTokens / 1_000_000) * price.input +
    (outputTokens / 1_000_000) * price.output
  );
}

// Usage
const usage = response.usage_metadata;
if (usage) {
  const cost = calculateCost(
    "anthropic/claude-sonnet-4-6",
    usage.input_tokens,
    usage.output_tokens
  );
  console.log(`Estimated cost: $${cost.toFixed(6)}`);
}
```

---

## 7. Common Debugging Workflow

### The Reproduce → Trace → Identify → Fix Loop

```
1. REPRODUCE
   │  Get the exact input that caused the issue
   │  Replay it locally with LANGSMITH_TRACING=true
   │
2. TRACE
   │  Open the trace in LangSmith UI
   │  Walk through each step: prompt → model → tool → model → response
   │  Look for: unexpected inputs, wrong tool calls, error messages
   │
3. IDENTIFY
   │  Common root causes:
   │  ├── Bad prompt → model misunderstands intent
   │  ├── Missing tool description → model picks wrong tool
   │  ├── Tool error → unhandled exception in tool function
   │  ├── Token limit → context too long, response truncated
   │  ├── Rate limit → 429 from provider
   │  └── Schema mismatch → structured output parsing fails
   │
4. FIX
   │  Apply fix, replay the same input, verify trace looks correct
   │  Add the case to your LangSmith evaluation dataset
```

### Quick Debugging Checklist

```typescript
// 1. Enable tracing
process.env.LANGSMITH_TRACING = "true";

// 2. Enable verbose logging
import { setVerbose } from "@langchain/core/globals";
setVerbose(true);

// 3. Wrap the problematic call with try/catch
try {
  const result = await agent.invoke({
    messages: [{ role: "user", content: problematicInput }],
  });
  console.log("Result:", JSON.stringify(result, null, 2));
} catch (error) {
  console.error("Error type:", error.constructor.name);
  console.error("Message:", error.message);
  // For API errors, check the response body
  if (error.response) {
    console.error("Status:", error.response.status);
    console.error("Body:", await error.response.text());
  }
}

// 4. Check token usage (was context too long?)
const response = await model.invoke(messages);
console.log("Token usage:", response.usage_metadata);

// 5. Test the tool in isolation
const toolResult = await myTool.invoke({ query: "test input" });
console.log("Tool output:", toolResult);
```

### Debugging Agent Loops

When an agent seems to loop or make incorrect tool calls:

```typescript
const stream = await agent.stream(
  { messages: [{ role: "user", content: problematicInput }] },
  { streamMode: "updates" }
);

let stepCount = 0;
for await (const chunk of stream) {
  stepCount++;
  for (const [node, data] of Object.entries(chunk)) {
    console.log(`\n--- Step ${stepCount}: Node "${node}" ---`);
    for (const msg of data.messages) {
      console.log(`  Type: ${msg.constructor.name}`);
      if (msg.tool_calls?.length) {
        console.log(`  Tool calls: ${JSON.stringify(msg.tool_calls, null, 2)}`);
      }
      console.log(`  Content: ${String(msg.content).substring(0, 200)}`);
    }
  }

  // Safety: abort if too many steps
  if (stepCount > 10) {
    console.error("⚠️ Agent exceeded 10 steps — possible infinite loop");
    break;
  }
}
```

---

## Import Reference

```typescript
// LangSmith manual tracing
import { traceable } from "langsmith/traceable";
import { wrapOpenAI } from "langsmith/wrappers";
import { Client } from "langsmith";
import { evaluate } from "langsmith/evaluation";

// Langfuse alternative
import { CallbackHandler } from "langfuse-langchain";

// Custom callbacks
import { BaseCallbackHandler } from "@langchain/core/callbacks/base";

// Verbose mode
import { setVerbose } from "@langchain/core/globals";

// Core LangChain
import { ChatOpenAI } from "@langchain/openai";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { createAgent } from "langchain";
```
