# Tool Events — Reference

Tool events cover the full execution lifecycle of every tool invocation — from the model requesting a tool, through execution, to the final result. Correlate events by `toolCallId`.

## Event Flow

```
assistant.message (with toolRequests)
  └─ [for each toolRequest in parallel:]
       tool.user_requested          (only if user explicitly requested the tool)
       permission.requested         (ephemeral — if permissions required)
       permission.completed         (ephemeral — approval result)
       tool.execution_start
       tool.execution_partial_result* (ephemeral, repeated — streaming output)
       tool.execution_progress*       (ephemeral, repeated — progress messages)
       tool.execution_complete
```

After all tool calls complete, the agent makes another LLM call, potentially emitting another `assistant.message` with more tool requests. This loop continues until the model stops requesting tools.

## `tool.execution_start` — Tool Begins

**Persisted.** Emitted immediately when a tool starts executing.

```typescript
type ToolExecutionStartEvent = {
  type: "tool.execution_start";
  data: {
    toolCallId: string;              // unique ID — correlate all tool events by this
    toolName: string;                // e.g., "bash", "edit", "grep", "read"
    arguments?: Record<string, unknown>;
    mcpServerName?: string;          // set when tool comes from an MCP server
    mcpToolName?: string;            // original tool name on the MCP server
    parentToolCallId?: string;       // set when invoked by a sub-agent
  };
};
```

```typescript
session.on("tool.execution_start", (event) => {
  const { toolCallId, toolName, arguments: args } = event.data;
  console.log(`[${toolCallId}] Starting tool: ${toolName}`);
  if (args) console.log("Args:", JSON.stringify(args, null, 2));
  startTimer(toolCallId);
});
```

## `tool.execution_partial_result` — Streaming Tool Output

**Ephemeral. Streaming only.** Incremental output from a running tool. Useful for displaying bash command output in real time.

```typescript
type ToolExecutionPartialResultEvent = {
  type: "tool.execution_partial_result";
  ephemeral: true;
  data: {
    toolCallId: string;   // matches tool.execution_start
    partialOutput: string;
  };
};
```

```typescript
const toolOutputBuffers = new Map<string, string>();

session.on("tool.execution_partial_result", (event) => {
  const prev = toolOutputBuffers.get(event.data.toolCallId) ?? "";
  toolOutputBuffers.set(event.data.toolCallId, prev + event.data.partialOutput);
  process.stdout.write(event.data.partialOutput); // stream to terminal
});
```

## `tool.execution_progress` — Progress Status

**Ephemeral. Streaming only.** Human-readable progress message from the running tool. Primarily emitted by MCP servers via progress notifications.

```typescript
session.on("tool.execution_progress", (event) => {
  console.log(`[${event.data.toolCallId}] Progress: ${event.data.progressMessage}`);
});
```

## `tool.execution_complete` — Tool Finished

**Persisted.** Emitted when the tool finishes — either successfully or with an error.

```typescript
type ToolExecutionCompleteEvent = {
  type: "tool.execution_complete";
  data: {
    toolCallId: string;
    success: boolean;
    model?: string;              // model that requested this tool call
    interactionId?: string;
    isUserRequested?: boolean;   // true if user explicitly triggered this tool call
    result?: {
      content: string;           // concise result sent to the LLM (may be truncated)
      detailedContent?: string;  // full result for UI display (e.g., complete diffs)
      contents?: (
        | { type: "text"; text: string }
        | { type: "terminal"; text: string; exitCode?: number; cwd?: string }
        | { type: "image"; data: string; mimeType: string }
        | { type: "audio"; data: string; mimeType: string }
        | { type: "resource_link"; uri: string; name: string; title?: string; description?: string; mimeType?: string; size?: number; icons?: { src: string; mimeType?: string; sizes?: string[]; theme?: "light" | "dark" }[] }
        | { type: "resource"; resource: { uri: string; mimeType?: string; text: string } | { uri: string; mimeType?: string; blob: string } }
      )[];
    };
    error?: {
      message: string;
      code?: string;
    };
    toolTelemetry?: Record<string, unknown>;  // e.g., CodeQL check counts
    parentToolCallId?: string;
  };
};
```

### Result Content Blocks

The `result.contents` array is a discriminated union. Display based on `type`:

```typescript
session.on("tool.execution_complete", (event) => {
  if (!event.data.success) {
    console.error(`Tool ${event.data.toolCallId} failed:`, event.data.error?.message);
    return;
  }

  const result = event.data.result;
  if (!result) return;

  // Use detailedContent for UI display when available (e.g., full diff)
  const displayContent = result.detailedContent ?? result.content;

  if (result.contents) {
    for (const block of result.contents) {
      switch (block.type) {
        case "text":
          renderText(block.text);
          break;
        case "terminal":
          renderTerminal(block.text, block.exitCode, block.cwd);
          break;
        case "image":
          renderImage(block.data, block.mimeType);
          break;
        case "resource_link":
          renderLink(block.uri, block.title ?? block.name);
          break;
      }
    }
  }
});
```

## `tool.user_requested` — User-Initiated Tool Call

**Persisted.** Emitted when the user explicitly requests a tool invocation (not the model). Always precedes `tool.execution_start` for user-initiated calls.

```typescript
type ToolUserRequestedEvent = {
  type: "tool.user_requested";
  data: {
    toolCallId: string;
    toolName: string;
    arguments?: Record<string, unknown>;
  };
};
```

## Monitoring Tool Execution — Full Pattern

```typescript
interface ToolExecution {
  toolName: string;
  startTime: number;
  partialOutput: string;
}

const activeTools = new Map<string, ToolExecution>();

session.on("tool.execution_start", (event) => {
  activeTools.set(event.data.toolCallId, {
    toolName: event.data.toolName,
    startTime: Date.now(),
    partialOutput: "",
  });
  renderToolStart(event.data.toolCallId, event.data.toolName, event.data.arguments);
});

session.on("tool.execution_partial_result", (event) => {
  const tool = activeTools.get(event.data.toolCallId);
  if (tool) {
    tool.partialOutput += event.data.partialOutput;
    appendToolOutput(event.data.toolCallId, event.data.partialOutput);
  }
});

session.on("tool.execution_progress", (event) => {
  updateToolProgress(event.data.toolCallId, event.data.progressMessage);
});

session.on("tool.execution_complete", (event) => {
  const tool = activeTools.get(event.data.toolCallId);
  const duration = tool ? Date.now() - tool.startTime : 0;
  activeTools.delete(event.data.toolCallId);

  if (event.data.success) {
    renderToolSuccess(event.data.toolCallId, event.data.result?.content ?? "", duration);
  } else {
    renderToolError(event.data.toolCallId, event.data.error?.message ?? "unknown", duration);
  }
});
```

## Correlating Tools to Assistant Messages

The `toolCallId` in tool events matches the `toolCallId` in `assistant.message.data.toolRequests`. Use this to display which tool call originated from which assistant message:

```typescript
const messageToTools = new Map<string, string[]>(); // messageId → toolCallId[]

session.on("assistant.message", (event) => {
  if (event.data.toolRequests?.length) {
    const toolIds = event.data.toolRequests.map(t => t.toolCallId);
    messageToTools.set(event.data.messageId, toolIds);
    console.log(`Message ${event.data.messageId} will invoke: ${toolIds.join(", ")}`);
  }
});
```

## MCP Tool Detection

Detect MCP tools by checking `mcpServerName` on `tool.execution_start`:

```typescript
session.on("tool.execution_start", (event) => {
  if (event.data.mcpServerName) {
    console.log(
      `MCP tool: ${event.data.mcpServerName}/${event.data.mcpToolName ?? event.data.toolName}`
    );
  }
});
```

## Sub-agent Tool Events

Tool events from sub-agents carry `parentToolCallId` linking them to the parent tool invocation that spawned the sub-agent. Use this to build hierarchical tool execution trees:

```typescript
session.on("tool.execution_start", (event) => {
  if (event.data.parentToolCallId) {
    // This tool was invoked by a sub-agent
    addChildToolNode(event.data.parentToolCallId, event.data.toolCallId, event.data.toolName);
  } else {
    // Top-level tool invocation
    addRootToolNode(event.data.toolCallId, event.data.toolName);
  }
});
```

## Tool Execution Metrics

Aggregate tool performance data from `tool.execution_complete`:

```typescript
interface ToolMetrics {
  callCount: number;
  successCount: number;
  failureCount: number;
}

const toolMetrics = new Map<string, ToolMetrics>();
const toolStartTimes = new Map<string, number>();

session.on("tool.execution_start", (event) => {
  toolStartTimes.set(event.data.toolCallId, Date.now());
});

session.on("tool.execution_complete", (event) => {
  const duration = Date.now() - (toolStartTimes.get(event.data.toolCallId) ?? Date.now());
  toolStartTimes.delete(event.data.toolCallId);

  const toolName = event.data.toolCallId; // use toolCallId for per-call tracking
  // Note: toolName is not on tool.execution_complete; track via Map from execution_start
});
```
