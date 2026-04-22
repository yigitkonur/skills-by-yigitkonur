# Resources and Prompts

Resources expose data for LLMs to read. Prompts provide reusable message templates. Both are optional — most servers only need tools.

## Resources

Resources are read-only data sources identified by URIs. Use them when the LLM needs to access structured data (files, database records, API responses) without calling a tool.

### Static resources (fixed URI)

```typescript
server.registerResource("readme", "file:///project/README.md", {
  description: "Project README",
  mimeType: "text/markdown",
}, async (uri) => ({
  contents: [{
    uri: uri.href,
    text: await readFile("/project/README.md", "utf-8"),
    mimeType: "text/markdown",
  }],
}));
```

### Template resources (parameterized URI)

```typescript
import { ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";

const userTemplate = new ResourceTemplate("users://{userId}/profile", {
  list: async () => ({
    resources: [
      { uri: "users://alice/profile", name: "Alice's profile" },
      { uri: "users://bob/profile", name: "Bob's profile" },
    ],
  }),
  complete: {
    userId: async (value) =>
      ["alice", "bob", "charlie"].filter((u) => u.startsWith(value)),
  },
});

server.registerResource("user-profile", userTemplate, {
  description: "User profile by ID",
  mimeType: "application/json",
}, async (uri, variables) => ({
  contents: [{
    uri: uri.href,
    text: JSON.stringify(await getUser(variables.userId)),
    mimeType: "application/json",
  }],
}));
```

The `variables` parameter is a `Record<string, string>` extracted from the URI template.

### Binary resources

```typescript
server.registerResource("logo", "assets://logo.png", {
  description: "Company logo",
  mimeType: "image/png",
}, async (uri) => ({
  contents: [{
    uri: uri.href,
    blob: readFileSync("logo.png").toString("base64"),
    mimeType: "image/png",
  }],
}));
```

### Resource metadata

```typescript
{
  title?: string,          // Human-readable display name
  description?: string,    // What the resource contains
  mimeType?: string,       // Content type
  annotations?: {
    audience?: ("user" | "assistant")[],  // Who should see this
  },
}
```

### RegisteredResource handle

```typescript
const res = server.registerResource("my-data", uri, config, handler);

res.enable();
res.disable();
res.remove();
res.update({ name?: string, uri?: string, metadata?, callback? });
```

### Resource subscriptions

Resource subscriptions require accessing the low-level `Server` via `server.server`:

```typescript
import {
  SubscribeRequestSchema,
  UnsubscribeRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const subscriptions = new Set<string>();

server.server.setRequestHandler(SubscribeRequestSchema, async (request) => {
  subscriptions.add(request.params.uri);
  return {};
});

server.server.setRequestHandler(UnsubscribeRequestSchema, async (request) => {
  subscriptions.delete(request.params.uri);
  return {};
});

// When a subscribed resource changes:
async function notifyResourceUpdate(uri: string) {
  if (subscriptions.has(uri)) {
    await server.server.sendResourceUpdated({ uri });
  }
}
```

## Prompts

Prompts are reusable message templates that LLMs or UIs can invoke to get pre-structured context.

### Simple prompt

```typescript
server.registerPrompt("summarize", {
  description: "Summarize a document",
  argsSchema: {
    content: z.string().describe("The document content to summarize"),
    style: z.enum(["brief", "detailed"]).default("brief").describe("Summary style"),
  },
}, async ({ content, style }) => ({
  messages: [{
    role: "user",
    content: {
      type: "text",
      text: style === "brief"
        ? `Summarize this in 2-3 sentences:\n\n${content}`
        : `Provide a detailed summary with key points:\n\n${content}`,
    },
  }],
}));
```

### Multi-message prompt

```typescript
server.registerPrompt("code-review", {
  description: "Review code with best practices",
  argsSchema: {
    code: z.string().describe("Code to review"),
    language: z.string().describe("Programming language"),
  },
}, async ({ code, language }) => ({
  messages: [
    {
      role: "user",
      content: {
        type: "text",
        text: `Review this ${language} code for bugs, security issues, and style:`,
      },
    },
    {
      role: "user",
      content: {
        type: "text",
        text: "```" + language + "\n" + code + "\n```",
      },
    },
  ],
  description: `Code review for ${language}`,
}));
```

### Prompt with embedded resource

```typescript
server.registerPrompt("analyze-data", {
  description: "Analyze a dataset",
  argsSchema: {
    dataUri: z.string().describe("URI of the data resource"),
  },
}, async ({ dataUri }) => ({
  messages: [{
    role: "user",
    content: {
      type: "resource",
      resource: { uri: dataUri, text: await fetchResourceContent(dataUri) },
    },
  }],
}));
```

### RegisteredPrompt handle

Same pattern as tools and resources:

```typescript
const prompt = server.registerPrompt("my-prompt", config, handler);
prompt.enable();
prompt.disable();
prompt.remove();
prompt.update({ name?, description?, argsSchema?, callback? });
```

## When to use resources vs tools

| Use resources when | Use tools when |
|---|---|
| Data is read-only | The operation has side effects |
| Data is addressable by URI | The operation requires complex input |
| Client may want to subscribe to changes | Results depend on computation |
| Data should be browseable/listable | The LLM needs to take an action |

Many servers use both: resources for data access and tools for operations on that data.
