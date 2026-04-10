# Experimental Tasks API

Durable state machines for long-running tool operations. Source-verified against `v1.x` branch.

**WARNING:** This API is experimental and may change without notice. Use `server.experimental.tasks`.

## When to use tasks

- Tool operations that take seconds to minutes (API calls, data processing, CI/CD)
- Operations where the client should be able to poll status and cancel
- Workflows requiring intermediate user input (`input_required` state)
- Background jobs where the result is retrieved later

## Server-side: registering task-based tools

### ExperimentalMcpServerTasks.registerToolTask

```typescript
// Access via server.experimental.tasks
const tasks = server.experimental.tasks;

// Overload 1 — no inputSchema
tasks.registerToolTask(
  name: string,
  config: {
    title?: string;
    description?: string;
    outputSchema?: ZodRawShapeCompat | AnySchema;
    annotations?: ToolAnnotations;
    execution?: TaskToolExecution;
    _meta?: Record<string, unknown>;
  },
  handler: ToolTaskHandler<undefined>
): RegisteredTool;

// Overload 2 — with inputSchema
tasks.registerToolTask(
  name: string,
  config: {
    title?: string;
    description?: string;
    inputSchema: InputArgs;
    outputSchema?: ZodRawShapeCompat | AnySchema;
    annotations?: ToolAnnotations;
    execution?: TaskToolExecution;
    _meta?: Record<string, unknown>;
  },
  handler: ToolTaskHandler<InputArgs>
): RegisteredTool;
```

`registerToolTask` internally sets `taskSupport: 'required'` — clients MUST invoke these tools as tasks.

### ToolTaskHandler interface (source-verified)

```typescript
interface ToolTaskHandler<Args> {
  createTask: CreateTaskRequestHandler<CreateTaskResult, Args>;
  getTask: TaskRequestHandler<GetTaskResult, Args>;
  getTaskResult: TaskRequestHandler<CallToolResult, Args>;
}
```

Three callbacks for the three phases of a task lifecycle:

| Callback | When called | Extra fields | Returns |
|---|---|---|---|
| `createTask` | Client invokes tool with `task` param | `extra.taskStore` | `CreateTaskResult` |
| `getTask` | Client polls `tasks/get` | `extra.taskId`, `extra.taskStore` | `GetTaskResult` |
| `getTaskResult` | Client calls `tasks/result` | `extra.taskId`, `extra.taskStore` | `CallToolResult` |

### Handler extra types

```typescript
interface CreateTaskRequestHandlerExtra extends RequestHandlerExtra {
  taskStore: RequestTaskStore;
}

interface TaskRequestHandlerExtra extends RequestHandlerExtra {
  taskId: string;
  taskStore: RequestTaskStore;
}
```

### Task states

```
working → input_required | completed | failed | cancelled
input_required → working | completed | failed | cancelled
completed, failed, cancelled → (terminal, no transitions)
```

### Example: task-based tool

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const server = new McpServer(
  { name: "task-server", version: "1.0.0" },
  {
    capabilities: {
      tasks: {
        list: {},
        cancel: {},
        requests: { tools: { call: {} } },
      },
    },
  }
);

server.experimental.tasks.registerToolTask("long-analysis", {
  description: "Run a long analysis job",
  inputSchema: { datasetId: z.string() },
  execution: { taskSupport: "required" },
}, {
  async createTask({ datasetId }, extra) {
    // Start the background work
    const task = await extra.taskStore.createTask(
      { ttl: 300000 }, // 5 minutes
      extra.requestId,
      { method: "tools/call", params: { name: "long-analysis" } }
    );

    // Kick off async work (don't await)
    startAnalysis(datasetId, task.taskId, extra.taskStore);

    return { task };
  },

  async getTask(args, extra) {
    const task = await extra.taskStore.getTask(extra.taskId);
    if (!task) throw new Error("Task not found");
    return task;
  },

  async getTaskResult(args, extra) {
    const result = await extra.taskStore.getTaskResult(extra.taskId);
    return result as CallToolResult;
  },
});

async function startAnalysis(datasetId: string, taskId: string, store: RequestTaskStore) {
  try {
    // ... long-running work ...
    await store.storeTaskResult(taskId, "completed", {
      content: [{ type: "text", text: `Analysis complete for ${datasetId}` }],
    });
  } catch (error) {
    await store.storeTaskResult(taskId, "failed", {
      content: [{ type: "text", text: `Analysis failed: ${error}` }],
      isError: true,
    });
  }
}
```

## InMemoryTaskStore

Built-in in-memory task storage for development:

```typescript
import { InMemoryTaskStore } from "@modelcontextprotocol/sdk/experimental/tasks/stores/in-memory.js";

class InMemoryTaskStore implements TaskStore {
  async createTask(taskParams, requestId, request, sessionId?): Promise<Task>
  async getTask(taskId, sessionId?): Promise<Task | null>
  async storeTaskResult(taskId, status: 'completed' | 'failed', result, sessionId?): Promise<void>
  async getTaskResult(taskId, sessionId?): Promise<Result>
  async updateTaskStatus(taskId, status, statusMessage?, sessionId?): Promise<void>
  async listTasks(cursor?, sessionId?): Promise<{ tasks: Task[]; nextCursor?: string }>
  cleanup(): void       // Clear timers and tasks (for tests/shutdown)
  getAllTasks(): Task[]  // Debug helper
}
```

Key behaviors:
- Task IDs: 16 random bytes as hex (32 chars)
- Default TTL: `null` (unlimited)
- Default `pollInterval`: 1000 ms
- Pagination: 10 tasks per page
- Guards against transitions out of terminal states
- TTL cleanup uses `setTimeout`

Also exports `InMemoryTaskMessageQueue`:

```typescript
class InMemoryTaskMessageQueue implements TaskMessageQueue {
  async enqueue(taskId, message, sessionId?, maxSize?): Promise<void>
  async dequeue(taskId, sessionId?): Promise<QueuedMessage | undefined>
  async dequeueAll(taskId, sessionId?): Promise<QueuedMessage[]>
}
```

## Client-side: calling task-based tools

### ExperimentalClientTasks (source-verified)

```typescript
const client = new Client({ name: "my-client", version: "1.0.0" });

// Stream-based tool call (auto-detects task tools)
async *callToolStream(
  params: CallToolRequest['params'],
  resultSchema?,
  options?
): AsyncGenerator<ResponseMessage<CallToolResult>, void, void>

// Poll task status
async getTask(taskId: string, options?): Promise<GetTaskResult>

// Retrieve final result (blocks if non-terminal)
async getTaskResult(taskId: string, resultSchema?, options?): Promise<Result>

// List all tasks (paginated)
async listTasks(cursor?: string, options?): Promise<ListTasksResult>

// Cancel a task
async cancelTask(taskId: string, options?): Promise<CancelTaskResult>
```

### callToolStream usage

```typescript
const stream = client.experimental.tasks.callToolStream({
  name: "long-analysis",
  arguments: { datasetId: "dataset-123" },
});

for await (const message of stream) {
  switch (message.type) {
    case "taskCreated":
      console.log("Task created:", message.result.task.taskId);
      break;
    case "taskStatus":
      console.log("Status:", message.result.task.status);
      break;
    case "result":
      console.log("Final result:", message.result);
      break;
    case "error":
      console.error("Error:", message.error);
      break;
  }
}
```

`callToolStream` automatically sets `task: {}` in options when it detects a task-based tool via `isToolTask()`.

## Server capabilities for tasks

```typescript
new McpServer(serverInfo, {
  capabilities: {
    tasks: {
      list: {},           // Enable tasks/list
      cancel: {},         // Enable tasks/cancel
      requests: {
        tools: { call: {} },  // Enable task-augmented tool calls
      },
    },
  },
});
```

Client capabilities:

```typescript
new Client(clientInfo, {
  capabilities: {
    tasks: {
      list: {},
      cancel: {},
      requests: {
        sampling: { createMessage: {} },
        elicitation: { create: {} },
      },
    },
  },
});
```
