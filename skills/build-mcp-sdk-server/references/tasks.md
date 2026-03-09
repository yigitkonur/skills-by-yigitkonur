# Tasks Reference (Experimental)

Tasks enable "call-now, fetch-later" patterns for long-running tool operations. Instead of returning immediately, a tool creates a task that can be polled or resumed.

> **Warning:** The tasks API is experimental and may change without notice.

## Setup

Enable tasks by providing a `TaskStore`:

```typescript
import { McpServer, InMemoryTaskStore } from '@modelcontextprotocol/server';

const server = new McpServer(
  { name: 'my-server', version: '1.0.0' },
  {
    capabilities: {
      tasks: {}, // Enable tasks capability
    },
  }
);

const taskStore = new InMemoryTaskStore();
```

## Registering a Task Tool

Use `server.experimental.tasks.registerToolTask()`:

```typescript
server.experimental.tasks.registerToolTask(
  'long-analysis',
  {
    description: 'Run a long-running code analysis',
    inputSchema: z.object({
      repoPath: z.string().describe('Path to the repository'),
    }),
    execution: {
      taskSupport: 'required', // or 'optional'
    },
  },
  {
    createTask: async ({ repoPath }, ctx) => {
      // Start the long-running operation
      const taskId = await startAnalysis(repoPath);

      return {
        taskId,
        status: 'running',
        message: 'Analysis started...',
      };
    },
    getTaskResult: async (taskId) => {
      const result = await getAnalysisResult(taskId);
      if (!result.done) {
        return { status: 'running', progress: result.percentComplete };
      }
      return {
        status: 'completed',
        content: [{ type: 'text', text: JSON.stringify(result.data) }],
      };
    },
  },
  taskStore
);
```

## Task Support Modes

| Mode | Behavior |
|------|----------|
| `'required'` | Tool always creates a task; fails without task augmentation |
| `'optional'` | Creates a task if client requests it; otherwise blocks until complete |

## Best Practices

1. Use tasks only for operations that genuinely take a long time (>5 seconds)
2. Implement `getTaskResult` to return progress updates
3. Use `InMemoryTaskStore` for development; implement persistent storage for production
4. Consider `'optional'` mode for flexibility — clients without task support still work
