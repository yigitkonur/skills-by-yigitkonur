# Resources and Prompts (v2)

Same concepts as v1 but with `ServerContext` instead of `RequestHandlerExtra` and Zod v4 schemas.

## Resources

### Static resource

```typescript
server.registerResource("readme", "file:///project/README.md", {
  description: "Project README",
  mimeType: "text/markdown",
}, async (uri, ctx) => ({
  contents: [{
    uri: uri.href,
    text: await readFile("/project/README.md", "utf-8"),
    mimeType: "text/markdown",
  }],
}));
```

### Template resource

```typescript
import { ResourceTemplate } from "@modelcontextprotocol/server";

const userTemplate = new ResourceTemplate("users://{userId}/profile", {
  list: async (ctx) => ({
    resources: [
      { uri: "users://alice/profile", name: "Alice" },
      { uri: "users://bob/profile", name: "Bob" },
    ],
  }),
  complete: {
    userId: async (value) => ["alice", "bob"].filter(u => u.startsWith(value)),
  },
});

server.registerResource("user-profile", userTemplate, {
  description: "User profile by ID",
  mimeType: "application/json",
}, async (uri, variables, ctx) => ({
  contents: [{
    uri: uri.href,
    text: JSON.stringify(await getUser(variables.userId)),
  }],
}));
```

### Resource subscriptions

Via low-level `server.server`:

```typescript
server.server.setRequestHandler("resources/subscribe", async (req, ctx) => {
  subscriptions.add(req.params.uri);
  return {};
});

// Notify on change:
await server.server.sendResourceUpdated({ uri: resourceUri });
```

## Prompts

```typescript
import * as z from "zod/v4";

server.registerPrompt("review-code", {
  title: "Code Review",
  description: "Review code for best practices",
  argsSchema: z.object({
    code: z.string().describe("Code to review"),
    language: z.string().describe("Programming language"),
  }),
}, async ({ code, language }, ctx) => ({
  messages: [{
    role: "user" as const,
    content: {
      type: "text" as const,
      text: `Review this ${language} code:\n\n\`\`\`${language}\n${code}\n\`\`\``,
    },
  }],
}));
```

Note: Prompt `argsSchema` must be a full `z.object()` in v2 (not raw shape).

## RegisteredResource / RegisteredPrompt handles

Same pattern as tools:

```typescript
const res = server.registerResource("data", uri, config, handler);
res.enable(); res.disable(); res.remove();
res.update({ name?, uri?, metadata?, callback?, enabled? });

const prompt = server.registerPrompt("review", config, handler);
prompt.enable(); prompt.disable(); prompt.remove();
prompt.update({ name?, description?, argsSchema?, callback?, enabled? });
```
