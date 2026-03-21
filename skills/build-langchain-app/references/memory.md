# Memory Patterns — Conversation & Long-Term State

> Verified against langchain@1.2.35, @langchain/core@1.1.34, @langchain/langgraph@1.2.5 — March 2026
> All code TypeScript. Import paths exact.

---

## Three-Layer Memory Model

LangChain/LangGraph memory is organized into three layers. Pick the shallowest layer that satisfies your persistence requirement.

```
┌──────────────────────────────────────────────────────────┐
│ Layer 3: Semantic Recall (RAG over past conversations)   │
│   → Vector store of past interactions                    │
│   → "What did we discuss about X last month?"            │
├──────────────────────────────────────────────────────────┤
│ Layer 2: Working Memory (key-value store)                │
│   → InMemoryStore / database-backed store                │
│   → User profiles, preferences, cross-conversation facts │
├──────────────────────────────────────────────────────────┤
│ Layer 1: Conversation Window (short-term)                │
│   → MemorySaver checkpointer                             │
│   → Current conversation messages, thread-scoped         │
└──────────────────────────────────────────────────────────┘
```

| Layer | Scope | Persistence | Use Case |
|-------|-------|-------------|----------|
| **1. Conversation Window** | Single thread | Session (dev) / DB (prod) | Chat history, multi-turn context |
| **2. Working Memory** | Cross-thread, per-user | In-memory (dev) / DB (prod) | User profiles, preferences, task state |
| **3. Semantic Recall** | Cross-thread, searchable | Vector store | Past conversation retrieval, long-term learning |

---

## Layer 1: MemorySaver Checkpointer

The checkpointer stores full conversation state, scoped by `thread_id`. Each thread is an independent conversation.

### Basic Usage

```typescript
import { MemorySaver } from "@langchain/langgraph";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { ChatOpenAI } from "@langchain/openai";

const checkpointer = new MemorySaver(); // In-memory — dev/testing only

const agent = createReactAgent({
  llm: model,
  tools: [],
  checkpointSaver: checkpointer,
});

// thread_id isolates conversations
const config = { configurable: { thread_id: "user-alice-session-1" } };

// Turn 1: introduce a fact
const result1 = await agent.invoke(
  { messages: [{ role: "user", content: "My name is Alice and I work at Acme Corp." }] },
  config
);

// Turn 2: same thread remembers
const result2 = await agent.invoke(
  { messages: [{ role: "user", content: "What is my name and where do I work?" }] },
  config
);
// → "Your name is Alice and you work at Acme Corp."

// Different thread_id = isolated conversation
const config2 = { configurable: { thread_id: "user-bob-session-1" } };
const result3 = await agent.invoke(
  { messages: [{ role: "user", content: "What is my name?" }] },
  config2
);
// → "I don't know your name."
```

### With StateGraph

```typescript
import {
  StateGraph,
  MessagesAnnotation,
  START,
  END,
  MemorySaver,
} from "@langchain/langgraph";

const graph = new StateGraph(MessagesAnnotation)
  .addNode("chat", async (state) => {
    const response = await model.invoke(state.messages);
    return { messages: [response] };
  })
  .addEdge(START, "chat")
  .addEdge("chat", END);

const app = graph.compile({ checkpointer: new MemorySaver() });

const result = await app.invoke(
  { messages: [{ role: "user", content: "Hello!" }] },
  { configurable: { thread_id: "thread-1" } }
);
```

### Production: PostgresSaver

```typescript
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";

const checkpointer = PostgresSaver.fromConnInfo({
  connectionString: process.env.DATABASE_URL!,
});
await checkpointer.setup(); // Creates tables if they don't exist

const agent = createReactAgent({
  llm: model,
  tools,
  checkpointSaver: checkpointer,
});
```

**MemorySaver** — in-memory, lost on restart. Use for dev/testing only.
**PostgresSaver** — persistent, production-ready. Requires `@langchain/langgraph-checkpoint-postgres`.

---

## Layer 2: InMemoryStore (Working Memory)

`InMemoryStore` is a namespaced key-value store for cross-conversation memory. Use it for user profiles, preferences, learned facts, and task state.

### CRUD Operations

```typescript
import { InMemoryStore } from "@langchain/langgraph";

const store = new InMemoryStore();

// PUT: store.put(namespace: string[], key: string, value: object)
await store.put(["users", "alice"], "preferences", {
  theme: "dark",
  language: "en",
  notifications: true,
});

await store.put(["users", "alice"], "profile", {
  name: "Alice",
  company: "Acme Corp",
  role: "Engineer",
});

// GET: returns Item with .key and .value, or null
const item = await store.get(["users", "alice"], "preferences");
console.log(item?.value);
// → { theme: "dark", language: "en", notifications: true }

// SEARCH: find all items in a namespace
const aliceItems = await store.search(["users", "alice"]);
// → [{ key: "preferences", value: {...} }, { key: "profile", value: {...} }]

// SEARCH with limit
const allUsers = await store.search(["users"], { limit: 10 });

// UPDATE: same put() overwrites the key
await store.put(["users", "alice"], "preferences", {
  theme: "light",
  language: "en",
  notifications: false,
});

// DELETE
await store.delete(["users", "alice"], "preferences");
const deleted = await store.get(["users", "alice"], "preferences");
// → null
```

### Namespace Design

Namespaces are `string[]` creating a hierarchical key space:

```typescript
// User-scoped data
await store.put(["users", "alice"], "profile", { ... });
await store.put(["users", "alice"], "preferences", { ... });

// Project-scoped data
await store.put(["projects", "proj-123"], "config", { ... });
await store.put(["projects", "proj-123"], "status", { ... });

// User + project scoped
await store.put(["users", "alice", "projects", "proj-123"], "notes", { ... });

// Search returns items in that namespace (and sub-namespaces)
const aliceData = await store.search(["users", "alice"]);
// → preferences, profile items
```

### ⚠️ InMemoryStore Gotcha: Mutable References

`InMemoryStore.get()` returns a **mutable reference**. If you update the same key later, previously retrieved references may reflect the new value.

```typescript
// ❌ Problem: reference changes after update
const item1 = await store.get(["users", "alice"], "prefs");
const theme1 = item1?.value; // { theme: "dark" }

await store.put(["users", "alice"], "prefs", { theme: "light" });

// theme1 may now be { theme: "light" } — the reference was mutated!

// ✅ Fix: capture primitive values immediately
const item = await store.get(["users", "alice"], "prefs");
const savedTheme = (item?.value as any)?.theme; // "dark" — primitive, safe
// OR deep clone:
const savedValue = JSON.parse(JSON.stringify(item?.value));
```

### Using Store with an Agent

```typescript
import { InMemoryStore, MemorySaver } from "@langchain/langgraph";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const store = new InMemoryStore();
const checkpointer = new MemorySaver();

// Tool that reads/writes to the store
const savePreference = tool(
  async ({ key, value }: { key: string; value: string }, runConfig) => {
    const userId = runConfig?.configurable?.user_id ?? "default";
    await store.put(["users", userId], key, { value });
    return `Saved preference: ${key} = ${value}`;
  },
  {
    name: "save_preference",
    description: "Save a user preference for future conversations",
    schema: z.object({
      key: z.string().describe("The preference name"),
      value: z.string().describe("The preference value"),
    }),
  }
);

const agent = createReactAgent({
  llm: model,
  tools: [savePreference],
  checkpointSaver: checkpointer,
});
```

### Production: Database-Backed Stores

For production, `InMemoryStore` should be replaced with a persistent store. Options:

- **PostgreSQL-backed store** — Use a custom store implementation backed by PostgreSQL
- **Redis-backed store** — For fast read/write with TTL support
- **Any database** — Implement the `BaseStore` interface with `get`, `put`, `search`, `delete`

```typescript
// InMemoryStore API that any persistent implementation should match:
interface StoreInterface {
  get(namespace: string[], key: string): Promise<Item | null>;
  put(namespace: string[], key: string, value: Record<string, any>): Promise<void>;
  search(namespace: string[], options?: { limit?: number }): Promise<Item[]>;
  delete(namespace: string[], key: string): Promise<void>;
}
```

---

## Layer 3: Semantic Recall (RAG Over Past Conversations)

Use a vector store to enable searching past conversations by meaning, not just by thread_id.

```typescript
import { OpenAIEmbeddings } from "@langchain/openai";
import { MemoryVectorStore } from "langchain/vectorstores/memory";
import { Document } from "@langchain/core/documents";

const embeddings = new OpenAIEmbeddings({
  model: "text-embedding-3-small",
  openAIApiKey: process.env.OPENAI_API_KEY!,
});
const memoryVectorStore = await MemoryVectorStore.fromDocuments([], embeddings);

// After each conversation turn, index the exchange
async function indexConversationTurn(
  userId: string,
  threadId: string,
  userMessage: string,
  assistantResponse: string
) {
  const doc = new Document({
    pageContent: `User: ${userMessage}\nAssistant: ${assistantResponse}`,
    metadata: {
      userId,
      threadId,
      timestamp: new Date().toISOString(),
    },
  });
  await memoryVectorStore.addDocuments([doc]);
}

// Later, recall past conversations by semantic similarity
async function recallPastConversations(
  query: string,
  k: number = 3
): Promise<Document[]> {
  return memoryVectorStore.similaritySearch(query, k);
}

// Use recalled context in a new conversation
const pastContext = await recallPastConversations("What did we discuss about deployment?");
const contextStr = pastContext
  .map((doc) => doc.pageContent)
  .join("\n---\n");
// Inject contextStr into the system prompt
```

**When to use semantic recall**:
- Personal assistants that remember past conversations
- Support agents that reference prior interactions
- Research agents that build knowledge over time

---

## Agent Type → Memory Layer Matrix

| Agent Type | Layer 1 (Checkpointer) | Layer 2 (Store) | Layer 3 (Semantic) |
|-----------|------------------------|-----------------|-------------------|
| **One-shot Q&A** | Not needed | Not needed | Not needed |
| **Chatbot** | ✅ Required | Optional | Not needed |
| **Personal assistant** | ✅ Required | ✅ Required (preferences) | ✅ Recommended |
| **Support agent** | ✅ Required | ✅ Required (ticket state) | ✅ Recommended |
| **Research agent** | ✅ Required | Optional (task state) | ✅ Required |
| **Multi-turn form/wizard** | ✅ Required | ✅ Required (form state) | Not needed |

---

## trimMessages Utility

Trim conversation history to fit within a token budget before sending to the LLM.

### Basic Usage

```typescript
import {
  trimMessages,
  HumanMessage,
  AIMessage,
  SystemMessage,
} from "@langchain/core/messages";

const messages = [
  new SystemMessage("You are a helpful assistant."),
  new HumanMessage("Question 1"),
  new AIMessage("Answer 1"),
  new HumanMessage("Question 2"),
  new AIMessage("Answer 2"),
  new HumanMessage("Question 3"),
  new AIMessage("Answer 3"),
  new HumanMessage("Latest question"),
];

// Keep most recent messages within token budget
const trimmed = await trimMessages(messages, {
  maxTokens: 150,
  tokenCounter: (msgs) => {
    // Simple char-based approximation (~4 chars per token)
    if (Array.isArray(msgs)) {
      return msgs.reduce(
        (sum, m) => sum + Math.ceil(String(m.content).length / 4),
        0
      );
    }
    return Math.ceil(String(msgs.content).length / 4);
  },
  strategy: "last", // Keep most recent
});
```

### Strategies

```typescript
// "last" — keep the most recent messages (most common for chat)
const recentMessages = await trimMessages(messages, {
  maxTokens: 200,
  tokenCounter,
  strategy: "last",
});

// "first" — keep the oldest messages (rare, for context preservation)
const oldestMessages = await trimMessages(messages, {
  maxTokens: 200,
  tokenCounter,
  strategy: "first",
});

// Preserve system message regardless of strategy
const withSystem = await trimMessages(messages, {
  maxTokens: 200,
  tokenCounter,
  strategy: "last",
  includeSystem: true, // System message always kept
});
```

### tokenCounter

The `tokenCounter` function must handle both a single message and an array of messages:

```typescript
const tokenCounter = (msgs: any) => {
  if (Array.isArray(msgs)) {
    return msgs.reduce(
      (sum: number, m: any) => sum + Math.ceil(String(m.content).length / 4),
      0
    );
  }
  return Math.ceil(String(msgs.content).length / 4);
};
```

For accurate counting, use a proper tokenizer (e.g., `tiktoken` via `@langchain/openai`):

```typescript
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({ model: "gpt-4o" });
// model.getNumTokens(text) returns accurate token count
const tokenCounter = async (msgs: any) => {
  if (Array.isArray(msgs)) {
    const texts = msgs.map((m: any) => String(m.content));
    const counts = await Promise.all(texts.map((t) => model.getNumTokens(t)));
    return counts.reduce((a, b) => a + b, 0);
  }
  return model.getNumTokens(String(msgs.content));
};
```

---

## summarizationMiddleware

Automatically compresses conversation history when it grows beyond a threshold.

```typescript
import { MemorySaver } from "@langchain/langgraph";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { summarizationMiddleware } from "langchain";

const checkpointer = new MemorySaver();

const agent = createReactAgent({
  llm: model,
  tools: [],
  checkpointSaver: checkpointer,
  messageMiddleware: summarizationMiddleware({
    maxMessages: 6,  // Summarize when history exceeds this count
    model,           // Model used to generate the summary
  }),
});

const config = { configurable: { thread_id: "long-conversation" } };

// As you send many messages, the middleware auto-summarizes older turns
for (const msg of userMessages) {
  await agent.invoke(
    { messages: [{ role: "user", content: msg }] },
    config
  );
}
// The agent retains knowledge from all turns, even those summarized away
```

**Key points**:
- Requires a `checkpointSaver` — the middleware reads/writes conversation state
- `maxMessages` triggers summarization when message count exceeds this value
- The `model` parameter specifies which LLM generates the summary
- Summarized content is preserved as context — the agent still "remembers" old turns
- The summary replaces older messages, reducing token usage for long conversations

---

## Memory Processors (Concepts)

Beyond `trimMessages` and `summarizationMiddleware`, consider these processing strategies:

### Token Limiting

Enforce a hard token budget on the message history before each LLM call:

```typescript
async function tokenLimitedMessages(
  messages: any[],
  maxTokens: number
): Promise<any[]> {
  const trimmed = await trimMessages(messages, {
    maxTokens,
    tokenCounter: /* your counter */,
    strategy: "last",
    includeSystem: true,
  });
  return trimmed;
}
```

### Tool Call Filtering

Remove verbose tool call/response pairs from history to save tokens:

```typescript
import { BaseMessage, isAIMessage } from "@langchain/core/messages";

function filterToolCalls(messages: BaseMessage[]): BaseMessage[] {
  return messages.filter((msg) => {
    // Keep all non-AI messages
    if (!isAIMessage(msg)) return true;
    // For AI messages, keep only those without tool calls (or the last one)
    return !msg.tool_calls || msg.tool_calls.length === 0;
  });
}
```

---

## Working Memory Patterns

### User Profile Injection

Store user-specific information and inject it into the system prompt:

```typescript
import { InMemoryStore } from "@langchain/langgraph";

const store = new InMemoryStore();

// Store user profile
await store.put(["users", "alice"], "profile", {
  name: "Alice",
  role: "Senior Engineer",
  preferences: { responseStyle: "concise", codeLanguage: "TypeScript" },
});

// Retrieve and inject into system prompt
async function buildSystemPrompt(userId: string): Promise<string> {
  const profile = await store.get(["users", userId], "profile");
  const prefs = profile?.value as any;

  let systemPrompt = "You are a helpful assistant.";
  if (prefs) {
    systemPrompt += `\n\nUser context:`;
    if (prefs.name) systemPrompt += `\n- Name: ${prefs.name}`;
    if (prefs.role) systemPrompt += `\n- Role: ${prefs.role}`;
    if (prefs.preferences?.responseStyle) {
      systemPrompt += `\n- Preferred response style: ${prefs.preferences.responseStyle}`;
    }
    if (prefs.preferences?.codeLanguage) {
      systemPrompt += `\n- Preferred code language: ${prefs.preferences.codeLanguage}`;
    }
  }
  return systemPrompt;
}
```

### Task State Tracking

Use working memory to track multi-step task progress across conversation turns:

```typescript
const store = new InMemoryStore();

// Initialize task state
await store.put(["tasks", "onboarding-alice"], "state", {
  currentStep: 1,
  totalSteps: 5,
  completedSteps: [],
  data: {},
});

// Update task state as steps complete
async function completeStep(
  taskId: string,
  stepNumber: number,
  stepData: Record<string, any>
) {
  const item = await store.get(["tasks", taskId], "state");
  const state = item?.value as any;
  if (!state) throw new Error(`Task ${taskId} not found`);

  // ⚠️ Clone before mutating — mutable reference gotcha
  const updatedState = JSON.parse(JSON.stringify(state));
  updatedState.completedSteps.push(stepNumber);
  updatedState.currentStep = stepNumber + 1;
  updatedState.data = { ...updatedState.data, ...stepData };

  await store.put(["tasks", taskId], "state", updatedState);
}
```

---

## Migration from Legacy Memory Classes

### ConversationBufferMemory → MemorySaver

```typescript
// ❌ Legacy (removed in v1)
import { ConversationBufferMemory } from "langchain/memory";
const memory = new ConversationBufferMemory();
const chain = new ConversationChain({ llm: model, memory });

// ✅ Modern: MemorySaver checkpointer
import { MemorySaver } from "@langchain/langgraph";
import { createReactAgent } from "@langchain/langgraph/prebuilt";

const agent = createReactAgent({
  llm: model,
  tools: [],
  checkpointSaver: new MemorySaver(),
});

// Conversation state persists automatically per thread_id
await agent.invoke(
  { messages: [{ role: "user", content: "Hello" }] },
  { configurable: { thread_id: "my-thread" } }
);
```

### BufferWindowMemory → trimMessages

```typescript
// ❌ Legacy (removed in v1)
import { BufferWindowMemory } from "langchain/memory";
const memory = new BufferWindowMemory({ k: 5 }); // keep last 5 exchanges

// ✅ Modern: trimMessages before invoking
import { trimMessages } from "@langchain/core/messages";

const trimmed = await trimMessages(messages, {
  maxTokens: 500,
  tokenCounter,
  strategy: "last",
  includeSystem: true,
});
// Use trimmed messages in your agent or chain
```

### ConversationSummaryMemory → summarizationMiddleware

```typescript
// ❌ Legacy (removed in v1)
import { ConversationSummaryMemory } from "langchain/memory";
const memory = new ConversationSummaryMemory({ llm: model });

// ✅ Modern: summarizationMiddleware
import { summarizationMiddleware } from "langchain";
import { MemorySaver } from "@langchain/langgraph";

const agent = createReactAgent({
  llm: model,
  tools: [],
  checkpointSaver: new MemorySaver(),
  messageMiddleware: summarizationMiddleware({
    maxMessages: 10,
    model,
  }),
});
```

---

## Production Memory Architecture

### Recommended Stack

| Layer | Development | Production |
|-------|------------|------------|
| **Checkpointer** | `MemorySaver` (in-memory) | `PostgresSaver` (`@langchain/langgraph-checkpoint-postgres`) |
| **Working Memory** | `InMemoryStore` | PostgreSQL / Redis-backed store |
| **Semantic Recall** | `MemoryVectorStore` | Pinecone / PGVector / Supabase |

### PostgresSaver Setup

```typescript
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";

const checkpointer = PostgresSaver.fromConnInfo({
  connectionString: process.env.DATABASE_URL!,
});
await checkpointer.setup(); // Run once — creates checkpoint tables

const agent = createReactAgent({
  llm: model,
  tools,
  checkpointSaver: checkpointer,
});

// Same API as MemorySaver — just swap the checkpointer
await agent.invoke(
  { messages: [{ role: "user", content: "Hello" }] },
  { configurable: { thread_id: "prod-thread-123" } }
);
```

### Memory Lifecycle Best Practices

1. **Thread cleanup** — Archive or delete old threads after inactivity (e.g., 30 days)
2. **Store pruning** — Remove stale key-value entries that haven't been accessed
3. **Vector deduplication** — Avoid re-indexing the same conversation turns
4. **Monitoring** — Track memory size per user, checkpoint write latency, store query latency

---

## Import Quick Reference

| What | Import |
|------|--------|
| `MemorySaver` | `@langchain/langgraph` |
| `InMemoryStore` | `@langchain/langgraph` |
| `PostgresSaver` | `@langchain/langgraph-checkpoint-postgres` |
| `trimMessages` | `@langchain/core/messages` |
| `HumanMessage`, `AIMessage`, `SystemMessage` | `@langchain/core/messages` |
| `isAIMessage` | `@langchain/core/messages` |
| `summarizationMiddleware` | `langchain` |
| `createReactAgent` | `@langchain/langgraph/prebuilt` |
| `StateGraph`, `MessagesAnnotation`, `START`, `END` | `@langchain/langgraph` |
| `Document` | `@langchain/core/documents` |
| `OpenAIEmbeddings` | `@langchain/openai` |
| `MemoryVectorStore` | `langchain/vectorstores/memory` |
