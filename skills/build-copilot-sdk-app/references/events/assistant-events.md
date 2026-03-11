# Assistant Events — Reference

Assistant events cover the full lifecycle of LLM responses: turn boundaries, streaming text, reasoning, and usage accounting.

## `assistant.turn_start` — Turn Begins

**Persisted.** Emitted when the agent starts processing a turn (a single LLM call cycle, including possible tool loops).

```typescript
type AssistantTurnStartEvent = {
  type: "assistant.turn_start";
  data: {
    turnId: string;          // stringified turn number, e.g., "1", "2"
    interactionId?: string;  // CAPI interaction ID for telemetry correlation
  };
};
```

```typescript
session.on("assistant.turn_start", (event) => {
  console.log(`Turn ${event.data.turnId} started`);
});
```

## `assistant.intent` — Agent Intent Update

**Ephemeral. Streaming only.** Short human-readable description of what the agent is currently doing.

```typescript
session.on("assistant.intent", (event) => {
  updateStatusBar(event.data.intent); // e.g., "Exploring codebase", "Writing tests"
});
```

## `assistant.reasoning` — Complete Reasoning Block

**Persisted.** The full extended thinking block from the model. Emitted after reasoning is complete (after all `assistant.reasoning_delta` events for this `reasoningId`).

```typescript
type AssistantReasoningEvent = {
  type: "assistant.reasoning";
  data: {
    reasoningId: string;  // matches reasoning_delta events for this block
    content: string;      // complete extended thinking text
  };
};
```

```typescript
session.on("assistant.reasoning", (event) => {
  console.log(`[Reasoning ${event.data.reasoningId}]`, event.data.content);
});
```

## `assistant.reasoning_delta` — Streaming Reasoning Chunk

**Ephemeral. Streaming only.** Incremental extended thinking text. Accumulate by `reasoningId` to reconstruct the full reasoning content.

```typescript
type AssistantReasoningDeltaEvent = {
  type: "assistant.reasoning_delta";
  ephemeral: true;
  data: {
    reasoningId: string;   // correlates with assistant.reasoning
    deltaContent: string;  // chunk to append
  };
};
```

## `assistant.message` — Complete Assistant Response

**Persisted.** The assistant's full text response for one LLM call. Always emitted even when streaming is enabled — it is the authoritative final content. `sendAndWait()` returns this event.

```typescript
type AssistantMessageEvent = {
  type: "assistant.message";
  data: {
    messageId: string;
    content: string;
    toolRequests?: {
      toolCallId: string;
      name: string;
      arguments?: Record<string, unknown>;
      type?: "function" | "custom";  // defaults to "function" when absent
    }[];
    reasoningOpaque?: string;     // encrypted extended thinking (Anthropic), session-bound
    reasoningText?: string;       // readable reasoning text
    encryptedContent?: string;    // encrypted reasoning (OpenAI models), session-bound
    phase?: string;               // e.g., "thinking" vs "response" for phased models
    outputTokens?: number;        // actual completion_tokens count
    interactionId?: string;
    parentToolCallId?: string;    // set when originating from a sub-agent
  };
};
```

`toolRequests` is non-empty when the model wants to invoke tools. Each entry triggers a `tool.execution_start` → `tool.execution_complete` pair. A single `assistant.message` can contain multiple tool requests executed in parallel.

```typescript
session.on("assistant.message", (event) => {
  const { messageId, content, toolRequests } = event.data;
  console.log(`[${messageId}] ${content}`);
  if (toolRequests?.length) {
    console.log(`Requesting ${toolRequests.length} tool(s):`, toolRequests.map(t => t.name));
  }
});
```

### Streaming vs Non-Streaming Behavior

| Mode | Delta events emitted | Final `assistant.message` emitted |
|------|---------------------|-----------------------------------|
| `streaming: true` | Yes — multiple `assistant.message_delta` events | Yes — always |
| `streaming: false` | No | Yes — always |

With streaming, the `content` field in `assistant.message` equals the full concatenation of all `deltaContent` chunks from `assistant.message_delta` events sharing the same `messageId`.

## `assistant.message_delta` — Streaming Text Chunk

**Ephemeral. Streaming only.** Incremental text chunk. Accumulate by `messageId` to build the complete response in real time.

```typescript
type AssistantMessageDeltaEvent = {
  type: "assistant.message_delta";
  ephemeral: true;
  data: {
    messageId: string;          // matches the final assistant.message
    deltaContent: string;       // text chunk to append
    parentToolCallId?: string;  // set when originating from a sub-agent
  };
};
```

### Delta Accumulation — Full Pattern

```typescript
const responseBuffer = new Map<string, string>();

// Accumulate during streaming
session.on("assistant.message_delta", (event) => {
  const prev = responseBuffer.get(event.data.messageId) ?? "";
  responseBuffer.set(event.data.messageId, prev + event.data.deltaContent);
  process.stdout.write(event.data.deltaContent); // real-time display
});

// Final event — clean up buffer and process complete response
session.on("assistant.message", (event) => {
  const accumulated = responseBuffer.get(event.data.messageId);
  responseBuffer.delete(event.data.messageId);
  // event.data.content === accumulated (always use event.data.content as authoritative)
  handleCompleteResponse(event.data.content, event.data.toolRequests);
});
```

### Sub-agent Streaming

When a sub-agent produces streaming output, both `assistant.message_delta` and `assistant.message` events carry `parentToolCallId` identifying the parent tool call that spawned the sub-agent. Filter by this field to isolate sub-agent output from main-agent output.

```typescript
session.on("assistant.message_delta", (event) => {
  if (event.data.parentToolCallId) {
    // sub-agent streaming output
    appendToSubAgentUI(event.data.parentToolCallId, event.data.deltaContent);
  } else {
    // main agent streaming output
    appendToMainUI(event.data.deltaContent);
  }
});
```

## `assistant.turn_end` — Turn Complete

**Persisted.** Emitted when the agent finishes a turn (all tools executed, final response delivered). `turnId` matches the corresponding `assistant.turn_start`.

```typescript
session.on("assistant.turn_end", (event) => {
  console.log(`Turn ${event.data.turnId} complete`);
});
```

## `assistant.usage` — Token Usage and Cost

**Ephemeral.** Emitted per LLM API call with detailed token accounting.

```typescript
type AssistantUsageEvent = {
  type: "assistant.usage";
  ephemeral: true;
  data: {
    model: string;
    inputTokens?: number;
    outputTokens?: number;
    cacheReadTokens?: number;
    cacheWriteTokens?: number;
    cost?: number;              // model multiplier (not USD)
    duration?: number;          // API call latency in ms
    initiator?: string;         // absent for user-initiated; "sub-agent" for sub-agent calls
    apiCallId?: string;         // chatcmpl-abc123 style provider ID
    providerCallId?: string;    // x-github-request-id header
    parentToolCallId?: string;  // set for sub-agent usage
    quotaSnapshots?: {
      [quotaId: string]: {
        isUnlimitedEntitlement: boolean;
        entitlementRequests: number;
        usedRequests: number;
        usageAllowedWithExhaustedQuota: boolean;
        overage: number;
        overageAllowedWithExhaustedQuota: boolean;
        remainingPercentage: number;  // 0.0 to 1.0
        resetDate?: string;
      };
    };
    copilotUsage?: {
      tokenDetails: {
        batchSize: number;
        costPerBatch: number;
        tokenCount: number;
        tokenType: string;  // "input" | "output"
      }[];
      totalNanoAiu: number;
    };
  };
};
```

Track aggregate token usage across a session:

```typescript
let totalInputTokens = 0;
let totalOutputTokens = 0;

session.on("assistant.usage", (event) => {
  totalInputTokens += event.data.inputTokens ?? 0;
  totalOutputTokens += event.data.outputTokens ?? 0;
  console.log(`API call: ${event.data.model} ${event.data.duration}ms`);
});

session.on("session.idle", () => {
  console.log(`Turn tokens: in=${totalInputTokens} out=${totalOutputTokens}`);
  totalInputTokens = 0;
  totalOutputTokens = 0;
});
```

## `assistant.streaming_delta` — Network Progress

**Ephemeral.** Low-level bytes-received counter from the streaming API response. Use for network progress indicators, not for content.

```typescript
session.on("assistant.streaming_delta", (event) => {
  updateBytesReceived(event.data.totalResponseSizeBytes);
});
```

## Complete Streaming Setup Example

```typescript
import { CopilotClient, approveAll } from "@github/copilot-sdk";

const client = new CopilotClient();
const session = await client.createSession({
  streaming: true,
  onPermissionRequest: approveAll,
});

const responseBuffer = new Map<string, string>();
const reasoningBuffer = new Map<string, string>();
let currentTurnId: string | null = null;

session.on("assistant.turn_start", (e) => { currentTurnId = e.data.turnId; });

session.on("assistant.reasoning_delta", (e) => {
  const prev = reasoningBuffer.get(e.data.reasoningId) ?? "";
  reasoningBuffer.set(e.data.reasoningId, prev + e.data.deltaContent);
});

session.on("assistant.message_delta", (e) => {
  if (!e.data.parentToolCallId) {  // main agent only
    const prev = responseBuffer.get(e.data.messageId) ?? "";
    responseBuffer.set(e.data.messageId, prev + e.data.deltaContent);
    process.stdout.write(e.data.deltaContent);
  }
});

session.on("assistant.message", (e) => {
  responseBuffer.delete(e.data.messageId);
  process.stdout.write("\n");
});

session.on("assistant.turn_end", (e) => { currentTurnId = null; });

const response = await session.sendAndWait({ prompt: "Explain async/await in TypeScript." });
console.log("Final response:", response?.data.content);

await session.disconnect();
```
