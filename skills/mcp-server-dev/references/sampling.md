# Sampling Reference

Sampling lets MCP servers request LLM completions from the client. This enables server-side agent loops where tools can invoke the LLM to process, classify, or generate content.

## Basic Sampling

Request a completion from within a tool handler:

```typescript
server.registerTool(
  'summarize-document',
  {
    description: 'Summarize a document using the LLM',
    inputSchema: z.object({
      documentUri: z.string().describe('URI of the document to summarize'),
    }),
  },
  async ({ documentUri }, ctx) => {
    const content = await fetchDocument(documentUri);

    const samplingResult = await ctx.mcpReq.createMessage({
      messages: [
        {
          role: 'user',
          content: { type: 'text', text: `Summarize this document concisely:\n\n${content}` },
        },
      ],
      maxTokens: 500,
    });

    return {
      content: [{ type: 'text', text: samplingResult.content.text }],
    };
  }
);
```

## Sampling with Tool Calling

The 2025-11-25 spec supports sampling with tool calling — the LLM can invoke tools during a sampling request:

```typescript
server.registerTool(
  'analyze-codebase',
  {
    description: 'Analyze a codebase using agent-style sampling with tool access',
    inputSchema: z.object({
      repoPath: z.string().describe('Path to the repository'),
    }),
  },
  async ({ repoPath }, ctx) => {
    const samplingResult = await ctx.mcpReq.createMessage({
      messages: [
        {
          role: 'user',
          content: {
            type: 'text',
            text: `Analyze the code quality of the repository at ${repoPath}. Use the available tools to read files and check for issues.`,
          },
        },
      ],
      maxTokens: 2000,
      includeContext: 'allServers', // Make all registered tools available
    });

    return {
      content: [{ type: 'text', text: samplingResult.content.text }],
    };
  }
);
```

## Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `messages` | Conversation messages to complete | Required |
| `maxTokens` | Maximum tokens to generate | Required |
| `temperature` | Sampling temperature (0-1) | Client default |
| `stopSequences` | Sequences that stop generation | None |
| `includeContext` | `'none'`, `'thisServer'`, `'allServers'` | `'none'` |
| `modelPreferences` | Hints for model selection | Client default |

## Client Capability Check

Sampling requires the client to declare the `sampling` capability:

```typescript
const client = new Client(
  { name: 'my-client', version: '1.0.0' },
  { capabilities: { sampling: {} } }
);
```

## Best Practices

1. Set reasonable `maxTokens` limits to control cost and latency
2. Use lower temperature for factual tasks, higher for creative ones
3. Check if the client supports sampling before using it
4. Handle sampling failures gracefully — not all clients support it
5. Be mindful of cost — each sampling request consumes LLM API credits
6. Use `includeContext: 'thisServer'` to give the LLM access to your tools during sampling
