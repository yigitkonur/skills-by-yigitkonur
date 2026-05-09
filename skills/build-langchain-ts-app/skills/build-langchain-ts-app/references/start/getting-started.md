# Getting Started — First Runnable Paths

Use this file when you need the first working path, not the full LangChain ecosystem.

## Preflight

- Node.js 20+ is required.
- Pick one provider before you install anything else.
- If the repo already has a TypeScript runner, keep using it. Otherwise install `tsx`, `typescript`, and `@types/node` as dev dependencies.
- If the repo already has a `src/` or `lib/` layout, follow it. Otherwise default to `src/agent.ts` and `src/lib/math.ts`.

## Path 1 — createAgent with existing helpers

Use this when you need a small tool-calling agent with 1-5 tools and no custom graph.

### Install

```bash
npm install langchain @langchain/core @langchain/openai @langchain/langgraph zod
npm install -D tsx typescript @types/node
```

### Credentials

Set `OPENAI_API_KEY` before you run the file.

### File layout

If the repo already has helper functions, keep those paths. If not, start with:

- `src/lib/math.ts`
- `src/agent.ts`

### `src/lib/math.ts`

```typescript
export const add = (a: number, b: number) => a + b;
export const subtract = (a: number, b: number) => a - b;
export const multiply = (a: number, b: number) => a * b;
export const divide = (a: number, b: number) => a / b;
```

### `src/agent.ts`

```typescript
import { createAgent } from "langchain";
import { ChatOpenAI } from "@langchain/openai";
import { tool } from "@langchain/core/tools";
import { MemorySaver } from "@langchain/langgraph";
import { z } from "zod";
import { add, subtract, multiply, divide } from "./lib/math.js";

const model = new ChatOpenAI({
  model: "gpt-4.1",
  apiKey: process.env.OPENAI_API_KEY,
});

const addTool = tool(
  ({ a, b }) => String(add(a, b)),
  {
    name: "add_numbers",
    description: "Add two numbers.",
    schema: z.object({
      a: z.number().describe("First number"),
      b: z.number().describe("Second number"),
    }),
  }
);

const subtractTool = tool(
  ({ a, b }) => String(subtract(a, b)),
  {
    name: "subtract_numbers",
    description: "Subtract the second number from the first.",
    schema: z.object({
      a: z.number().describe("First number"),
      b: z.number().describe("Second number"),
    }),
  }
);

const multiplyTool = tool(
  ({ a, b }) => String(multiply(a, b)),
  {
    name: "multiply_numbers",
    description: "Multiply two numbers.",
    schema: z.object({
      a: z.number().describe("First number"),
      b: z.number().describe("Second number"),
    }),
  }
);

const divideTool = tool(
  ({ a, b }) => String(divide(a, b)),
  {
    name: "divide_numbers",
    description: "Divide the first number by the second.",
    schema: z.object({
      a: z.number().describe("Dividend"),
      b: z.number().describe("Divisor"),
    }),
  }
);

const agent = createAgent({
  model,
  tools: [addTool, subtractTool, multiplyTool, divideTool],
  systemPrompt: "Use the arithmetic tools instead of mental math.",
  checkpointer: new MemorySaver(),
});

const result = await agent.invoke(
  { messages: [{ role: "user", content: "What is 15 * 23 + 7?" }] },
  { configurable: { thread_id: "local-demo-1" } }
);

console.log(result.messages.at(-1)?.content);
```

### Run

```bash
OPENAI_API_KEY=your_key_here npx tsx src/agent.ts
```

If the repo already loads env vars from `.env`, keep that mechanism and run the repo's usual command instead.

### Do not change these first

- Keep `thread_id` stable while testing memory.
- Keep one tool per real helper function.
- Keep tool schemas flat and fully described.
- Keep `systemPrompt` simple until the first run works.

### Switch away from this path when

- You need explicit graph nodes, cycles, or `interrupt()`.
- You need to branch or resume execution outside the built-in agent loop.
- You need retrieval, long-context grounding, or document ingestion.

## Path 2 — OpenRouter with direct tool binding

Use this when you need to validate OpenRouter credentials or a simple `bindTools()` workflow before you build a full agent.

### Install

```bash
npm install langchain @langchain/core @langchain/openrouter zod
npm install -D tsx typescript @types/node
```

### Credentials

Set `OPENROUTER_API_KEY` before running.

### Minimal file

```typescript
import { ChatOpenRouter } from "@langchain/openrouter";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const search = tool(
  ({ query }) => `Results for: ${query}`,
  {
    name: "search",
    description: "Search for information.",
    schema: z.object({ query: z.string().describe("Search terms") }),
  }
);

const model = new ChatOpenRouter({
  model: "anthropic/claude-sonnet-4-6",
  apiKey: process.env.OPENROUTER_API_KEY,
});

const modelWithTools = model.bindTools([search]);
const response = await modelWithTools.invoke("Search for TypeScript news");
console.log(response.tool_calls);
```

### Run

```bash
OPENROUTER_API_KEY=your_key_here npx tsx src/openrouter-agent.ts
```

## When to switch to StateGraph

Do not start with StateGraph unless one of these is already true:

- You need explicit nodes and edges instead of one ReAct loop.
- You need `interrupt()` or human approval that resumes later.
- You need custom state beyond messages and simple checkpoint memory.
- You need deterministic routing, parallel graph branches, or reusable subgraphs.

When that happens, return to `SKILL.md` and move to `Pattern C — LangGraph StateGraph`, then load `references/langgraph.md` and `references/human-in-the-loop.md`.

## When to switch to RAG

Do not start with RAG if the working corpus fits comfortably in the model context window.

Switch to RAG when:

- The app must retrieve from documents or knowledge bases at runtime.
- Grounding matters more than general chat quality.
- You need citations, retrieval metrics, or vector-store-backed memory.

When that happens, load `references/rag.md` first and use `Pattern D — RAG chain (LCEL)` as the wiring pattern.
