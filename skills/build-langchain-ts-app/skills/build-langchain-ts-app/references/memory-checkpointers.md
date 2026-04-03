# Memory: Checkpointers & Short-Term Reference

Complete reference for LangGraph checkpointers, message transformer APIs, middleware-based memory management, and thread lifecycle. All APIs verified against `@langchain/langgraph@1.x`, `@langchain/core@1.x`, `langchain@1.x` — March 2026. TypeScript only.

---

## Quick Reference — Imports

```typescript
// Checkpointers
import { MemorySaver } from "@langchain/langgraph";
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";
import { RedisSaver } from "@langchain/langgraph-checkpoint-redis";
import { MongoDBSaver } from "@langchain/langgraph-checkpoint-mongodb";
import { SqliteSaver } from "@langchain/langgraph-checkpoint-sqlite";

// Message transformers
import { trimMessages, filterMessages, mergeMessageRuns } from "@langchain/core/messages";
import { RemoveMessage } from "@langchain/core/messages";
import { REMOVE_ALL_MESSAGES } from "@langchain/langgraph";

// Graph primitives
import { StateGraph, StateSchema, MessagesValue, START, END } from "@langchain/langgraph";

// Middleware
import { createAgent, createMiddleware, summarizationMiddleware } from "langchain";
import { countTokensApproximately } from "langchain";
```

---

## Conceptual Architecture

Short-term memory in LangChain.js is **thread-scoped**: it lives within a single conversation thread, implemented as part of the **LangGraph graph state**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Conversation Thread                                                        │
│                                                                             │
│  State { messages: BaseMessage[], ...customFields }                         │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────┐  checkpoint  ┌─────────────────────────────┐             │
│  │  Graph Node  │ ──────────── │  Checkpointer               │             │
│  │  (LLM call)  │             │  MemorySaver / PostgresSaver │             │
│  └──────────────┘             │  RedisSaver / MongoDBSaver   │             │
│                               └─────────────────────────────┘             │
│                                                                             │
│  Short-term (thread-scoped): graph state, persisted by checkpointer        │
│  Long-term (cross-thread):   BaseStore (see memory-stores.md)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**The central problem**: Long conversations exceed LLM context windows. Solution hierarchy:

1. **Trimming** — filter messages before model call (state kept intact)
2. **Deletion** — permanently remove messages from state via `RemoveMessage`
3. **Summarization** — replace old messages with an LLM-generated summary
4. **Middleware** — apply domain-specific rules via `createMiddleware`

---

## Checkpointer Comparison

| Checkpointer | Package | Backend | Durability | ACID | TTL | Best For |
|---|---|---|---|---|---|---|
| `MemorySaver` | `@langchain/langgraph` | RAM | None | No | No | Dev, testing |
| `SqliteSaver` | `@langchain/langgraph-checkpoint-sqlite` | SQLite file | File-based | Partial | No | Small apps, demos |
| `PostgresSaver` | `@langchain/langgraph-checkpoint-postgres` | PostgreSQL | Full | Yes | Via cron | Production (relational) |
| `MongoDBSaver` | `@langchain/langgraph-checkpoint-mongodb` | MongoDB | Full | Doc-level | Via TTL index | Production (document) |
| `RedisSaver` | `@langchain/langgraph-checkpoint-redis` | Redis / Upstash | Configurable | No | Native TTL | High-throughput, serverless |

All checkpointers implement `BaseCheckpointSaver`:

```typescript
interface BaseCheckpointSaver {
  put(config: RunnableConfig, snapshot: StateSnapshot): Promise<void>;
  putWrites(config: RunnableConfig, writes: Record<string, any>): Promise<void>;
  getTuple(config: RunnableConfig): Promise<CheckpointTuple>;
  list(config: RunnableConfig, filter?: any): Promise<CheckpointTuple[]>;
  setup?(): Promise<void>;
  deleteThread?(threadId: string): Promise<void>;
}
```

---

## Checkpointer Setup

### MemorySaver (Dev/Test Only)

```typescript
import { MemorySaver } from "@langchain/langgraph";

const checkpointer = new MemorySaver();
const graph = workflow.compile({ checkpointer });
```

**Warning:** All state is lost on process restart. Never use in production. Also conflicts with `InMemoryCache` — do not use both together (see Known Pitfalls).

### PostgresSaver (Production)

```typescript
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";

const checkpointer = PostgresSaver.fromConnString(
  process.env.DATABASE_URL ?? "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"
);

// MUST call once at app startup — creates checkpoints, checkpoint_writes, checkpoint_blobs tables
await checkpointer.setup();

const graph = workflow.compile({ checkpointer });
```

`PostgresSaver.fromConnString` signature:

```typescript
PostgresSaver.fromConnString(
  connString: string,
  options?: {
    schema?: string;  // default: "public"
  }
): PostgresSaver
```

### RedisSaver (High-Throughput / Serverless)

```typescript
import { RedisSaver } from "@langchain/langgraph-checkpoint-redis";

// Standard Redis
const checkpointer = new RedisSaver({ url: process.env.REDIS_URL! });

// Upstash (edge-compatible, serverless)
const checkpointer = new RedisSaver({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
  ttlSeconds: 7 * 24 * 60 * 60,  // 7 days
});

const graph = workflow.compile({ checkpointer });
```

### SqliteSaver (Single-Node / Demo)

```typescript
import { SqliteSaver } from "@langchain/langgraph-checkpoint-sqlite";

const checkpointer = new SqliteSaver({ path: "./checkpoints.db" });
await checkpointer.setup();

const graph = workflow.compile({ checkpointer });
```

### MongoDBSaver (Document-Centric Production)

```typescript
import { MongoDBSaver } from "@langchain/langgraph-checkpoint-mongodb";

const checkpointer = new MongoDBSaver({
  url: process.env.MONGODB_URI!,
  dbName: "langgraph",
});

const graph = workflow.compile({ checkpointer });
```

---

## Thread ID & Configuration

The `thread_id` is the primary key for a conversation. Every invocation with a checkpointer MUST include it:

```typescript
const config = {
  configurable: {
    thread_id: "unique-conversation-id",  // required
    checkpoint_id?: "specific-checkpoint", // optional — for time travel
  },
};

await graph.invoke(input, config);
await graph.stream(input, config);
await graph.getState(config);
await graph.getStateHistory(config);
```

Thread ID strategies:

```typescript
// Per-user (one long-lived conversation per user)
const config = { configurable: { thread_id: userId } };

// Per-session (new thread each session)
const config = { configurable: { thread_id: `${userId}-${sessionId}` } };

// Multi-tenant namespace
const config = { configurable: { thread_id: `org:${orgId}:user:${userId}` } };

// UUID per conversation (safest isolation)
import { v4 as uuidv4 } from "uuid";
const config = { configurable: { thread_id: uuidv4() } };
```

---

## Full Execution Flow

```typescript
import {
  StateGraph, StateSchema, MessagesValue, GraphNode, START, MemorySaver
} from "@langchain/langgraph";
import { ChatAnthropic } from "@langchain/anthropic";

const State = new StateSchema({ messages: MessagesValue });
const model = new ChatAnthropic({ model: "claude-haiku-4-5-20251001" });

const callModel: GraphNode<typeof State> = async (state) => {
  const response = await model.invoke(state.messages);
  return { messages: [response] };
};

const graph = new StateGraph(State)
  .addNode("call_model", callModel)
  .addEdge(START, "call_model")
  .compile({ checkpointer: new MemorySaver() });

const config = { configurable: { thread_id: "1" } };

// First turn
await graph.invoke({ messages: [{ role: "user", content: "Hi, I'm Bob" }] }, config);

// Second turn — automatically loads previous messages from checkpoint
const result = await graph.invoke(
  { messages: [{ role: "user", content: "What's my name?" }] },
  config
);
console.log(result.messages.at(-1)?.content); // → "Your name is Bob."

// Inspect state
const state = await graph.getState(config);
console.log(state.values.messages.length); // → 4

// View checkpoint history
for await (const snapshot of graph.getStateHistory(config)) {
  // one entry per super-step
}

// Delete thread (cleanup / GDPR)
await checkpointer.deleteThread("1");
```

**Execution lifecycle per invocation:**
1. `checkpointer.getTuple(config)` fetches the latest `StateSnapshot` for `thread_id`
2. Graph state is hydrated from the snapshot
3. Each graph node executes, receiving `(state, runtime)` parameters
4. After each super-step, `checkpointer.put(config, newSnapshot)` saves the updated state
5. On next invocation with the same `thread_id`, step 1 resumes from the latest checkpoint
6. For branching: provide `checkpoint_id` in config to resume from a specific snapshot

---

## Message Transformer APIs

All three utilities import from `@langchain/core/messages`.

### trimMessages

**Purpose**: Remove messages so total token count stays below `maxTokens`. Does NOT remove from graph state — only filters what is passed to the model call. Use `RemoveMessage` to permanently delete from state.

```typescript
import { trimMessages } from "@langchain/core/messages";

interface TrimMessagesFields {
  maxTokens: number;                    // Required
  strategy: "first" | "last";          // Required; "last" keeps recent, "first" keeps oldest
  tokenCounter:                         // Required
    | BaseLanguageModel
    | ((messages: BaseMessage[]) => number)
    | ((messages: BaseMessage[]) => Promise<number>);
  startOn?: MessageTypeOrClass | MessageTypeOrClass[];  // e.g. "human"
  endOn?: MessageTypeOrClass | MessageTypeOrClass[];    // e.g. ["human", "tool"]
  includeSystem?: boolean;              // Default: false
  allowPartial?: boolean;               // Default: false
  textSplitter?: TextSplitterFn;        // Used when allowPartial=true
}

type MessageTypeOrClass =
  | "human" | "ai" | "system" | "tool"
  | typeof HumanMessage | typeof AIMessage | typeof SystemMessage | typeof ToolMessage;
```

**Strategy behavior:**

| Strategy | Removes | Keeps | Best For |
|---|---|---|---|
| `"last"` | Oldest messages first | Most recent | Chatbots, conversational agents |
| `"first"` | Newest messages first | Oldest | Fixed-context grounding, few-shot examples |

**Example — basic usage:**

```typescript
import { trimMessages, HumanMessage, AIMessage, SystemMessage } from "@langchain/core/messages";
import { ChatAnthropic } from "@langchain/anthropic";

const model = new ChatAnthropic({ model: "claude-3-5-sonnet-20241022" });

const trimmed = await trimMessages(messages, {
  maxTokens: 100,
  strategy: "last",
  tokenCounter: model,          // uses model.getNumTokens() for exact counts
  startOn: "human",
  endOn: ["human", "tool"],
  includeSystem: true,
});
```

**Example — using inside a LangGraph node:**

```typescript
const callModel: GraphNode<typeof State> = async (state) => {
  // Full history stays in state; only trimmed view goes to model
  const trimmedMessages = await trimMessages(state.messages, {
    strategy: "last",
    maxTokens: 100_000,
    tokenCounter: model,
    startOn: "human",
  });
  const response = await model.invoke(trimmedMessages);
  return { messages: [response] };
};
```

**Token counting options:**

```typescript
// Option 1: approximate (no API call, ~4 chars/token heuristic)
import { countTokensApproximately } from "langchain";
// countTokensApproximately(messages, tools?) — includes tool schemas in estimate

// Option 2: model's built-in counter (accurate, may make API call)
tokenCounter: model

// Option 3: tiktoken (exact, install: npm i tiktoken)
import { encoding_for_model } from "tiktoken";
const enc = encoding_for_model("gpt-4o");
function exactCounter(messages: BaseMessage[]): number {
  let count = 0;
  for (const msg of messages) {
    count += 4;
    const content = typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content);
    count += enc.encode(content).length;
  }
  return count + 2;
}
```

---

### filterMessages

**Purpose**: Include or exclude messages by name, type, or ID.

```typescript
import { filterMessages } from "@langchain/core/messages";

interface FilterMessagesFields {
  includeNames?: string[];
  includeTypes?: (string | typeof BaseMessage)[];
  includeIds?: string[];
  excludeNames?: string[];
  excludeTypes?: (string | typeof BaseMessage)[];
  excludeIds?: string[];
}

// Example
const filtered = filterMessages(messages, {
  includeTypes: ["system", "human"],
  excludeIds: ["msg-id-to-remove"],
});

// Runnable form (pipe-friendly)
const filterRunnable = filterMessages({ includeTypes: ["human", "ai"] });
const result = await filterRunnable.invoke(messages);
```

---

### mergeMessageRuns

**Purpose**: Merge consecutive messages of the same type into one. Useful for deduplication before sending to an LLM. `ToolMessage` instances are NEVER merged (each carries a unique `tool_call_id`).

```typescript
import { mergeMessageRuns, HumanMessage, AIMessage, SystemMessage } from "@langchain/core/messages";

const messages = [
  new SystemMessage("you're a good assistant."),
  new HumanMessage({ content: "what's your name", id: "foo" }),
  new HumanMessage({ content: "wait, your favorite food", id: "bar" }),  // consecutive human
  new AIMessage({
    content: "my favorite color",
    tool_calls: [{ name: "blah_tool", args: { x: 2 }, id: "123" }],
    id: "baz",
  }),
  new AIMessage({
    content: "my favorite dish is lasagna",
    tool_calls: [{ name: "blah_tool", args: { x: -10 }, id: "456" }],
    id: "blur",
  }),
];

const merged = mergeMessageRuns(messages);
// Result:
// [
//   SystemMessage("you're a good assistant."),
//   HumanMessage("what's your name\nwait, your favorite food"),  ← merged
//   AIMessage(content="my favorite color\nmy favorite dish is lasagna",
//             tool_calls=[{id:"123",...},{id:"456",...}])         ← merged
// ]
```

---

## RemoveMessage / REMOVE_ALL_MESSAGES

Permanently removes messages from graph state (affects what is stored in the checkpointer — not just the model view):

```typescript
import { RemoveMessage } from "@langchain/core/messages";
import { REMOVE_ALL_MESSAGES, MessagesValue } from "@langchain/langgraph";

// State MUST use MessagesValue reducer — not z.array() — or RemoveMessage is ignored
const State = new StateSchema({ messages: MessagesValue });

// Remove specific messages by ID
const deleteMessages: GraphNode<typeof State> = (state) => {
  const msgs = state.messages;
  if (msgs.length > 2) {
    return {
      messages: msgs.slice(0, msgs.length - 2).map(
        (m) => new RemoveMessage({ id: m.id! })
      ),
    };
  }
  return {};
};

// Remove ALL messages atomically (single sentinel value)
return {
  messages: [new RemoveMessage({ id: REMOVE_ALL_MESSAGES })],
};
```

---

## Middleware-Based Memory Management

The `langchain` v1 package's `createMiddleware` is the recommended way to manage memory in agents (cleaner than node-level logic).

### createMiddleware API

```typescript
import { createMiddleware } from "langchain";

interface Middleware {
  name: string;
  // Runs BEFORE the model call — can return partial state updates
  beforeModel?: (state: AgentState) => Partial<AgentState> | Promise<Partial<AgentState>> | void;
  // Runs AFTER the model call — can return partial state updates
  afterModel?: (state: AgentState) => Partial<AgentState> | Promise<Partial<AgentState>> | void;
}
```

**Example: keep first message + recent window (beforeModel):**

```typescript
import { RemoveMessage } from "@langchain/core/messages";
import { createAgent, createMiddleware } from "langchain";
import { MemorySaver, REMOVE_ALL_MESSAGES } from "@langchain/langgraph";

const trimMessagesMiddleware = createMiddleware({
  name: "TrimMessages",
  beforeModel: (state) => {
    const msgs = state.messages;
    if (msgs.length <= 3) return;

    const first = msgs[0];
    // Keep 3 if even length, 4 if odd (complete human/ai pairs)
    const recent = msgs.length % 2 === 0 ? msgs.slice(-3) : msgs.slice(-4);
    return {
      messages: [
        new RemoveMessage({ id: REMOVE_ALL_MESSAGES }),
        first,
        ...recent,
      ],
    };
  },
});

const agent = createAgent({
  model: "gpt-4.1",
  tools: [],
  middleware: [trimMessagesMiddleware],
  checkpointer: new MemorySaver(),
});
```

**Example: delete two oldest messages after each response (afterModel):**

```typescript
const deleteOldMessages = createMiddleware({
  name: "DeleteOldMessages",
  afterModel: (state) => {
    if (state.messages.length > 2) {
      return {
        messages: state.messages.slice(0, 2).map(
          (m) => new RemoveMessage({ id: m.id! })
        ),
      };
    }
  },
});
```

**Example: token-budget trimming (beforeModel, with real counter):**

```typescript
import { trimMessages } from "@langchain/core/messages";
import { REMOVE_ALL_MESSAGES, RemoveMessage } from "@langchain/langgraph";

const trimMessageHistory = createMiddleware({
  name: "TrimMessages",
  beforeModel: async (state) => {
    const trimmed = await trimMessages(state.messages, {
      maxTokens: 4096,
      strategy: "last",
      startOn: "human",
      endOn: ["human", "tool"],
      tokenCounter: (msgs) => msgs.reduce((acc, m) => {
        const text = typeof m.content === "string" ? m.content : JSON.stringify(m.content);
        return acc + Math.ceil(text.length / 4) + 4;
      }, 0),
    });
    return {
      messages: [
        new RemoveMessage({ id: REMOVE_ALL_MESSAGES }),
        ...trimmed,
      ],
    };
  },
});
```

---

### summarizationMiddleware

Automatically summarizes older messages when the conversation grows too long. Monitors token counts and replaces old messages with an LLM-generated summary.

```typescript
import { createAgent, summarizationMiddleware } from "langchain";
import { MemorySaver } from "@langchain/langgraph";

const agent = createAgent({
  model: "gpt-4.1",
  tools: [],
  middleware: [
    summarizationMiddleware({
      // Can use a cheaper model for summarization
      model: "gpt-4.1-mini",
      // Summarize when total tokens exceed this threshold
      trigger: { tokens: 4000 },
      // Retain this many recent messages after summarization
      keep: { messages: 20 },
    }),
  ],
  checkpointer: new MemorySaver(),
});
```

**How it works:**
1. Before each model call, checks total token count of `state.messages`
2. If count exceeds `trigger.tokens`, calls the summarizer model with the oldest messages
3. Replaces all but the last `keep.messages` messages with a single summary `AIMessage`
4. The summary is prepended as context on the next invocation

---

### dynamicSystemPromptMiddleware

Injects a system prompt generated dynamically from runtime context (user name, preferences stored in state):

```typescript
import { dynamicSystemPromptMiddleware, createAgent } from "langchain";
import { z } from "zod";

const contextSchema = z.object({
  userName: z.string().optional(),
  language: z.string().default("English"),
});

const agent = createAgent({
  model: "gpt-4.1",
  tools: [],
  contextSchema,
  middleware: [
    dynamicSystemPromptMiddleware<z.infer<typeof contextSchema>>(
      (_, cfg) =>
        `You are a helpful assistant. Address the user as ${cfg.context?.userName ?? "there"}. ` +
        `Respond in ${cfg.context?.language}.`
    ),
  ],
});

await agent.invoke(
  { messages: [{ role: "user", content: "Hello!" }] },
  { context: { userName: "Alice", language: "French" } }
);
```

---

## LangGraph-Native Summarization Pattern

For full control, implement summarization as a graph node (alternative to `summarizationMiddleware`):

```typescript
import { RemoveMessage, HumanMessage, SystemMessage } from "@langchain/core/messages";
import {
  StateGraph, StateSchema, MessagesValue, GraphNode,
  ConditionalEdgeRouter, START, END, MemorySaver
} from "@langchain/langgraph";
import { ChatAnthropic } from "@langchain/anthropic";
import { z } from "zod";
import { v4 as uuidv4 } from "uuid";

// State includes messages AND a summary field
const GraphState = new StateSchema({
  messages: MessagesValue,
  summary: z.string().default(""),
});

const model = new ChatAnthropic({ model: "claude-haiku-4-5-20251001" });

// Main node — prepends summary as system context if available
const callModel: GraphNode<typeof GraphState> = async (state) => {
  const { summary } = state;
  let msgs = state.messages;
  if (summary) {
    msgs = [
      new SystemMessage(`Summary of conversation so far: ${summary}`),
      ...msgs,
    ];
  }
  const response = await model.invoke(msgs);
  return { messages: [response] };
};

// Route: if > 6 messages, trigger summarization
const shouldContinue: ConditionalEdgeRouter<typeof GraphState, "summarize_conversation"> = (state) =>
  state.messages.length > 6 ? "summarize_conversation" : END;

// Summarization node — compresses old messages, retains last 2
const summarizeConversation: GraphNode<typeof GraphState> = async (state) => {
  const { summary, messages } = state;
  const prompt = summary
    ? `This is the conversation summary so far: ${summary}\n\nExtend the summary with the new messages above:`
    : "Create a concise summary of the conversation above:";

  const all = [...messages, new HumanMessage({ id: uuidv4(), content: prompt })];
  const response = await model.invoke(all);

  const toDelete = messages.slice(0, -2).map(
    (m) => new RemoveMessage({ id: m.id! })
  );

  return {
    summary: response.content as string,
    messages: toDelete,
  };
};

const app = new StateGraph(GraphState)
  .addNode("conversation", callModel)
  .addNode("summarize_conversation", summarizeConversation)
  .addEdge(START, "conversation")
  .addConditionalEdges("conversation", shouldContinue)
  .addEdge("summarize_conversation", END)
  .compile({ checkpointer: new MemorySaver() });
```

---

## Delete Messages Pattern

**When to use**: Permanently remove messages from both the model view AND stored state. This affects future invocations.

```typescript
import { RemoveMessage } from "@langchain/core/messages";
import {
  StateGraph, StateSchema, MessagesValue, GraphNode, START, MemorySaver
} from "@langchain/langgraph";

const State = new StateSchema({ messages: MessagesValue });

const deleteMessages: GraphNode<typeof State> = (state) => {
  const msgs = state.messages;
  if (msgs.length > 2) {
    return {
      messages: msgs.slice(0, msgs.length - 2).map(
        (m) => new RemoveMessage({ id: m.id! })
      ),
    };
  }
  return {};
};

const callModel: GraphNode<typeof State> = async (state) => {
  const response = await model.invoke(state.messages);
  return { messages: [response] };
};

const graph = new StateGraph(State)
  .addNode("call_model", callModel)
  .addNode("delete_messages", deleteMessages)
  .addEdge(START, "call_model")
  .addEdge("call_model", "delete_messages")  // delete runs after model response
  .compile({ checkpointer: new MemorySaver() });
```

---

## Custom State Schema Pattern

Store arbitrary fields alongside messages:

```typescript
import { StateSchema, MessagesValue, MemorySaver, StateGraph, START } from "@langchain/langgraph";
import { z } from "zod";

const CustomState = new StateSchema({
  messages: MessagesValue,
  userId: z.string().optional(),
  summary: z.string().default(""),
  preferences: z.record(z.string(), z.any()).default(() => ({})),
  sessionMetadata: z.object({
    startedAt: z.string(),
    messageCount: z.number().default(0),
  }).optional(),
});

const callModel = async (state: typeof CustomState.State, runtime) => {
  const { userName, preferences } = state;
  const system = `You are a helpful assistant.${userName ? ` The user's name is ${userName}.` : ""}`;
  const response = await model.invoke([
    { role: "system", content: system },
    ...state.messages,
  ]);
  return {
    messages: [response],
    sessionMetadata: {
      startedAt: state.sessionMetadata?.startedAt ?? new Date().toISOString(),
      messageCount: (state.sessionMetadata?.messageCount ?? 0) + 1,
    },
  };
};
```

---

## TTL & Memory Lifecycle

Configure TTL in `langgraph.json`:

```json
{
  "checkpointer": {
    "ttl": {
      "strategy": "delete",
      "sweep_interval_minutes": 60,
      "default_ttl": 43200
    }
  }
}
```

| Field | Options | Description |
|---|---|---|
| `strategy` | `"delete"` | Remove entire thread + all checkpoints when TTL expires |
| `strategy` | `"keep_latest"` | Keep thread + latest checkpoint; delete older checkpoints |
| `sweep_interval_minutes` | number | How often cleanup job runs |
| `default_ttl` | number (minutes) | 43200 = 30 days |

Manual cleanup:

```typescript
// Delete all checkpoints for a thread
await checkpointer.deleteThread(threadId);

// Delete a specific checkpoint
await checkpointer.deleteCheckpoint({
  configurable: { thread_id: threadId, checkpoint_id: checkpointId }
});
```

---

## Community Chat Message History Backends (Legacy)

These extend `BaseListChatMessageHistory` and are used with the legacy `RunnableWithMessageHistory` API. For new code, use LangGraph checkpointers instead.

| Backend | Class | Package |
|---|---|---|
| In-memory | `ChatMessageHistory` | `@langchain/community/stores/message/in_memory` |
| Redis (ioredis) | `RedisChatMessageHistory` | `@langchain/community/stores/message/redis` |
| Upstash Redis | `UpstashRedisChatMessageHistory` | `@langchain/community/stores/message/upstash_redis` |
| PostgreSQL | `PostgresChatMessageHistory` | `@langchain/community/stores/message/postgres` |
| DynamoDB | `DynamoDBChatMessageHistory` | `@langchain/community/stores/message/dynamodb` |
| Firestore | `FirestoreChatMessageHistory` | `@langchain/community/stores/message/firestore` |
| MongoDB | `MongoDBChatMessageHistory` | `@langchain/community/stores/message/mongodb` |
| Cassandra | `CassandraChatMessageHistory` | `@langchain/community/stores/message/cassandra` |
| Momento | `MomentoChatMessageHistory` | `@langchain/community/stores/message/momento` |
| Zep Cloud | `ZepCloudChatMessageHistory` | `@langchain/community/stores/message/zep_cloud` |
| AstraDB | `AstraDBChatMessageHistory` | `@langchain/community/stores/message/astradb` |
| Convex | `ConvexChatMessageHistory` | `@langchain/community/stores/message/convex` |

---

## Legacy Memory Migration

### Deprecated Classes → Modern Replacements

| Legacy Class | Package | Replacement |
|---|---|---|
| `ConversationBufferMemory` | `langchain/memory` | `MemorySaver` + full `state.messages` |
| `ConversationBufferWindowMemory` | `langchain/memory` | `trimMessages({ strategy: "last", maxTokens: N })` |
| `ConversationSummaryMemory` | `langchain/memory` | `summarizationMiddleware` or custom summarize node |
| `ConversationSummaryBufferMemory` | `langchain/memory` | Combined trim + summarize pattern |
| `ConversationEntityMemory` | `langchain/memory` | Custom `StateSchema` with entity extraction node |
| `ConversationTokenBufferMemory` | `langchain/memory` | `trimMessages` with `tokenCounter` |

### RunnableWithMessageHistory → LangGraph Checkpointing

**Before** (legacy — do not use for new code):

```typescript
import { RunnableWithMessageHistory } from "@langchain/core/runnables";
import { InMemoryChatMessageHistory } from "@langchain/core/chat_history";

const store: Record<string, InMemoryChatMessageHistory> = {};

const chainWithHistory = new RunnableWithMessageHistory({
  runnable: chain,
  getMessageHistory: (sessionId) => {
    if (!store[sessionId]) store[sessionId] = new InMemoryChatMessageHistory();
    return store[sessionId];
  },
  inputMessagesKey: "input",
  historyMessagesKey: "history",
});

await chainWithHistory.invoke(
  { input: "Hello" },
  { configurable: { sessionId: "user-123" } }
);
```

**After** (LangGraph checkpointing):

```typescript
import { StateGraph, StateSchema, MessagesValue, START, MemorySaver } from "@langchain/langgraph";
import { ChatOpenAI } from "@langchain/openai";

const State = new StateSchema({ messages: MessagesValue });
const model = new ChatOpenAI({ model: "gpt-4o" });

const graph = new StateGraph(State)
  .addNode("call_model", async (state) => ({
    messages: [await model.invoke(state.messages)],
  }))
  .addEdge(START, "call_model")
  .compile({ checkpointer: new MemorySaver() });

// sessionId → thread_id
await graph.invoke(
  { messages: [{ role: "user", content: "Hello" }] },
  { configurable: { thread_id: "user-123" } }
);
```

Key differences:
- `sessionId` → `thread_id` in `configurable`
- `inputMessagesKey` / `historyMessagesKey` → unified `state.messages` array
- No `MessagesPlaceholder` needed
- Full history in state; apply `trimMessages` before model call if needed
- Enables branching, time-travel, tool calls, multi-node graphs

---

## Known Pitfalls

| Pitfall | Symptom | Solution |
|---------|---------|----------|
| `InMemoryCache` + `MemorySaver` conflict | Cache stops working; internal state management conflict | Use `RedisCache` + `RedisSaver` or Postgres for both |
| `MemorySaver` in production | All data lost on process restart | Use `PostgresSaver` or `RedisSaver` |
| `setup()` not called on DB-backed savers | Tables don't exist; throws on first operation | Always call `await checkpointer.setup()` at app startup |
| `RemoveMessage` with `z.array()` state reducer | Remove markers ignored; messages never deleted | Use `MessagesValue` reducer — not plain `z.array()` |
| `REMOVE_ALL_MESSAGES` missing import | Runtime error on sentinel value | Import from `@langchain/langgraph`, not `@langchain/core` |
| Reusing thread IDs across users | All users share the same conversation history | Use `thread_id: user:${userId}:session:${sessionId}` |
| Infinite message growth without trimming | Context window exceeded; latency/cost spikes | Apply `trimMessages` inside the model node |
| Forgetting tool schemas in token count | Token budget underestimated by 500–2000 tokens per tool | Use `countTokensApproximately(messages, tools)` |
| `await` missing on `graph.invoke()` | Fire-and-forget; checkpoints not saved | Always `await graph.invoke(...)` |
| No TTL configured | Inactive threads accumulate indefinitely in DB | Configure `langgraph.json` TTL or use `RedisSaver` native TTL |
| `trimMessages` removes from state | Misunderstanding: full history disappears | `trimMessages` only filters the model view; use `RemoveMessage` to delete from state |
| Thread deletion not honouring GDPR | Thread data persists after user deletion request | Call `checkpointer.deleteThread(threadId)` for all of a user's threads |
