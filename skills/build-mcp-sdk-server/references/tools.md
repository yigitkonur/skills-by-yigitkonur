# Tools Reference

Tools let MCP clients ask your server to take actions. They are the primary way LLMs interact with your application.

## Registration API (v2)

```typescript
server.registerTool(name, config, callback);
```

- `name`: Tool identifier (lowercase, hyphens, underscores)
- `config`: Object with `title?`, `description?`, `inputSchema?`, `outputSchema?`, `annotations?`, `_meta?`
- `callback`: `async (args, ctx) => CallToolResult`

## Basic Tool

```typescript
import { z } from 'zod/v4';

server.registerTool(
  'search-docs',
  {
    title: 'Search Documents',
    description: 'Search the document store by keyword. Returns up to 10 results.',
    inputSchema: z.object({
      query: z.string().min(1).describe('Search keywords'),
      limit: z.number().min(1).max(50).default(10).describe('Maximum results to return'),
    }),
  },
  async ({ query, limit }) => {
    const results = await documentStore.search(query, limit);
    return {
      content: [{ type: 'text', text: JSON.stringify(results, null, 2) }],
    };
  }
);
```

## Tool with Output Schema

When you declare an `outputSchema`, return `structuredContent` alongside `content`:

```typescript
server.registerTool(
  'calculate-bmi',
  {
    title: 'BMI Calculator',
    description: 'Calculate Body Mass Index from weight and height',
    inputSchema: z.object({
      weightKg: z.number().positive().describe('Weight in kilograms'),
      heightM: z.number().positive().describe('Height in meters'),
    }),
    outputSchema: z.object({
      bmi: z.number(),
      category: z.string(),
    }),
  },
  async ({ weightKg, heightM }) => {
    const bmi = weightKg / (heightM * heightM);
    const category = bmi < 18.5 ? 'underweight' : bmi < 25 ? 'normal' : bmi < 30 ? 'overweight' : 'obese';
    const output = { bmi: Math.round(bmi * 10) / 10, category };
    return {
      content: [{ type: 'text', text: JSON.stringify(output) }],
      structuredContent: output,
    };
  }
);
```

## Tool Annotations

Annotations hint at tool behavior without changing execution:

```typescript
server.registerTool(
  'read-file',
  {
    description: 'Read a file from the filesystem',
    inputSchema: z.object({ path: z.string() }),
    annotations: {
      readOnlyHint: true,     // Does not modify state
      idempotentHint: true,   // Same input → same result
      openWorldHint: true,    // Interacts with external systems
    },
  },
  async ({ path }) => { /* ... */ }
);
```

| Annotation | Meaning |
|-----------|---------|
| `readOnlyHint` | Tool does not modify state |
| `destructiveHint` | Tool may irreversibly modify state |
| `idempotentHint` | Repeated calls with same args produce same result |
| `openWorldHint` | Tool interacts with external entities |

## ResourceLink Outputs

Return references to large resources without embedding content:

```typescript
import type { CallToolResult, ResourceLink } from '@modelcontextprotocol/server';

server.registerTool(
  'list-files',
  {
    title: 'List Files',
    description: 'List project files as resource links',
  },
  async (): Promise<CallToolResult> => {
    const links: ResourceLink[] = [
      { type: 'resource_link', uri: 'file:///readme.md', name: 'README', mimeType: 'text/markdown' },
      { type: 'resource_link', uri: 'file:///config.json', name: 'Config', mimeType: 'application/json' },
    ];
    return { content: links };
  }
);
```

## Dynamic Tool Management

Tools can be enabled, disabled, or removed at runtime:

```typescript
const tool = server.registerTool('feature-x', { /* ... */ }, handler);

// Disable without removing
tool.disable();

// Re-enable
tool.enable();

// Remove entirely
tool.remove();

// Update configuration
tool.update({
  description: 'Updated description',
  enabled: true,
});
```

## Error Handling Pattern

Always return errors as text content. Never throw unhandled exceptions:

```typescript
server.registerTool('api-call', {
  inputSchema: z.object({ endpoint: z.string().url() }),
}, async ({ endpoint }) => {
  try {
    const response = await fetch(endpoint);
    if (!response.ok) {
      return {
        content: [{ type: 'text', text: `HTTP ${response.status}: ${response.statusText}` }],
        isError: true,
      };
    }
    const data = await response.json();
    return { content: [{ type: 'text', text: JSON.stringify(data) }] };
  } catch (error) {
    return {
      content: [{ type: 'text', text: `Error: ${error instanceof Error ? error.message : String(error)}` }],
      isError: true,
    };
  }
});
```

## Schema Best Practices

1. Always use `.describe()` on every Zod field — LLMs rely on descriptions
2. Use `.default()` for optional parameters
3. Use `.min()` / `.max()` to constrain numbers
4. Use `z.enum()` for fixed option sets
5. Wrap all schemas with `z.object()` (v2 requirement)
6. Keep descriptions concise but clear — they appear in tool listings

```typescript
inputSchema: z.object({
  query: z.string().min(1).describe('Search terms'),
  category: z.enum(['docs', 'code', 'issues']).default('docs').describe('Content type to search'),
  limit: z.number().int().min(1).max(100).default(10).describe('Maximum number of results'),
  includeArchived: z.boolean().default(false).describe('Include archived items'),
}),
```
