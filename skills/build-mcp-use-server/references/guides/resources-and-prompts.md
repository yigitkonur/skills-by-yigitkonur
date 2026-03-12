# Resources and Prompts in mcp-use

Guide to registering resources (read-only data) and prompts (reusable LLM instruction templates) with the mcp-use `MCPServer` API.

## Resources

Resources expose **read-only data** to MCP clients — config, documents, database records, and files — without performing side effects.

### Static Resources

A static resource has a fixed URI that never changes. Use these for config, metadata, or documentation.

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });

server.resource(
  {
    name: "config",
    uri: "config://app",
    title: "Application Config",
    description: "Current application configuration",
    mimeType: "application/json",
  },
  async () => object({ env: "production", version: "1.0.0", debug: false })
);

server.resource(
  {
    name: "readme",
    uri: "docs://readme",
    title: "README",
    description: "Project documentation",
    mimeType: "text/markdown",
  },
  async () => text("# My Project\n\nWelcome to the project.")
);
```

Key points:
- `uri` is a **fixed string** — no template parameters
- Use `object()` for JSON data, `text()` for plain text / markdown

### Dynamic Resource Templates

Templates use `{paramName}` placeholders in the URI:

```typescript
server.resource(
  {
    name: "user-profile",
    uri: "users://{userId}/profile",
    title: "User Profile",
    description: "Get a user's profile by ID",
    mimeType: "application/json",
  },
  async ({ userId }) =>
    object({
      id: userId,
      name: "John Doe",
      email: "john@example.com",
    })
);

server.resource(
  {
    name: "document",
    uri: "docs://{category}/{docId}",
    title: "Document",
    description: "Fetch a document by category and ID",
    mimeType: "text/markdown",
  },
  async ({ category, docId }) => {
    const doc = await db.getDocument(category, docId);
    return text(doc.content);
  }
);
```

Template parameters are extracted from the URI pattern and passed as the first argument — destructure them directly.

### Binary Resources

Return binary content (images, PDFs, audio) using `blob()`:

```typescript
import { readFile } from "node:fs/promises";

server.resource(
  {
    name: "logo",
    uri: "assets://logo.png",
    title: "Company Logo",
    description: "PNG logo image",
    mimeType: "image/png",
  },
  async () => {
    const data = await readFile("./assets/logo.png");
    return blob(data, "image/png");
  }
);
```

### List Resources

Expose collections as a single resource:

```typescript
server.resource(
  {
    name: "recent-logs",
    uri: "logs://recent",
    title: "Recent Logs",
    description: "Last 50 log entries",
    mimeType: "application/json",
  },
  async () => {
    const logs = await db.getLogs({ limit: 50, order: "desc" });
    return object(logs);
  }
);
```

### Resource Completion

Provide auto-completion hints so clients can suggest valid values:

```typescript
server.resource(
  {
    name: "user",
    uri: "users://{userId}",
    title: "User",
    description: "User record by ID",
    mimeType: "application/json",
    complete: {
      userId: async (partial) => {
        const users = await db.searchUsers(partial);
        return users.map((u) => u.id);
      },
    },
  },
  async ({ userId }) => object(await db.getUser(userId))
);

```

Each key in `complete` maps to a URI template parameter. It receives the partial input and returns matching values.

## Resource Best Practices

1. **Use descriptive URI schemes** — `docs://`, `users://`, `config://`, `logs://`. Schemes act as namespaces.

2. **Set `mimeType` accurately** — Clients use this for rendering. Common values: `application/json`, `text/markdown`, `text/plain`, `image/png`, `application/pdf`.

3. **Keep resources read-only** — Never mutate state in a resource handler. Use tools for writes.

4. **Return consistent structure** — All resources under the same scheme should return a predictable shape.

5. **Use template parameters, not query strings** — `users://{userId}` is correct. Avoid `users://lookup?id={userId}`.

6. **Provide completion for dynamic templates** — Add `complete` handlers for parameters with many possible values.

7. **Keep payloads focused** — Return only needed data. Cap large lists (e.g., last 100 entries).

## Prompts

Prompts are **reusable instruction templates** that guide LLM interactions with structured, parameterized messages.

### Simple Prompt

A single-message prompt using the `text()` helper:

```typescript
import { z } from "zod";

server.prompt(
  {
    name: "code-review",
    description: "Review code for bugs and improvements",
    schema: z.object({
      code: z.string().describe("Source code to review"),
      language: z.string().describe("Programming language"),
    }),
  },
  async ({ code, language }) =>
    text(
      `Review this ${language} code for bugs, security issues, and improvements:\n\n\`\`\`${language}\n${code}\n\`\`\``
    )
);
```

The `schema` uses Zod to define and validate parameters. Each field's `.describe()` tells clients what to provide.

### Multi-Message Prompt

Return a `messages` array for prompts needing multiple turns or system context:

```typescript
server.prompt(
  {
    name: "debug-assistant",
    description: "Help debug an error",
    schema: z.object({
      error: z.string().describe("Error message"),
      context: z.string().optional().describe("Additional context"),
    }),
  },
  async ({ error, context }) => ({
    messages: [
      {
        role: "user" as const,
        content: { type: "text" as const, text: `Debug this error: ${error}` },
      },
      ...(context
        ? [
            {
              role: "user" as const,
              content: {
                type: "text" as const,
                text: `Context: ${context}`,
              },
            },
          ]
        : []),
    ],
  })
);
```

### Prompt With Embedded Resource

Reference resources inside prompts to include dynamic data:

```typescript
server.prompt(
  {
    name: "analyze-config",
    description: "Analyze the current application config",
    schema: z.object({
      focus: z.string().describe("Area to focus on (security, performance, etc.)"),
    }),
  },
  async ({ focus }) => ({
    messages: [
      {
        role: "user" as const,
        content: {
          type: "resource" as const,
          resource: { uri: "config://app", mimeType: "application/json" },
        },
      },
      {
        role: "user" as const,
        content: {
          type: "text" as const,
          text: `Analyze this configuration with a focus on ${focus}. Flag any issues.`,
        },
      },
    ],
  })
);
```

### Prompt Without Parameters

Omit the schema for fixed instructions:

```typescript
server.prompt(
  {
    name: "summarize-logs",
    description: "Summarize recent application logs",
  },
  async () =>
    text(
      "Retrieve the recent logs resource and summarize any errors, warnings, or unusual patterns. Group findings by severity."
    )
);
```

---

## Prompt Best Practices

1. **Use prompts for reusable instruction templates** — If you write the same LLM instructions repeatedly, extract them into a prompt.

2. **Keep schema parameters minimal and clear** — Each parameter should have a `.describe()`. Fewer parameters = better UX.

3. **Use multi-message format for structured conversations** — When a prompt needs system context or multi-turn setup, return a `messages` array.

4. **Reference resources in prompts** — Use `type: "resource"` content blocks to pull in dynamic data while keeping prompts reusable.

5. **Prompts complement tools** — Tools perform actions. Prompts guide the LLM on *how to think* about results. Use them together.

## When to Use Resources vs Tools vs Prompts

| Use Case | Primitive | Why |
| --- | --- | --- |
| Read data | **Resource** | Data access, supports caching |
| Perform action | **Tool** | Side effects, input/output schemas |
| Reusable LLM instruction | **Prompt** | Structured interaction templates |
| Search/query | **Tool** | Flexible parameters, computed results |
| Config/metadata | **Resource** | Read-only, cacheable |
| Write/update data | **Tool** | Side effects need explicit action |
| Guide analysis | **Prompt** | Combines template with resource refs |

### Decision Flow

```
Need to expose data? → Is it read-only? → Yes → RESOURCE / No → TOOL
Need to guide the LLM? → Is it reusable? → Yes → PROMPT / No → Tool description
```

## Common Patterns

### Resource + Tool Pair

```typescript
// Read: resource
server.resource(
  {
    name: "user-settings",
    uri: "settings://{userId}",
    title: "User Settings",
    description: "Current settings for a user",
    mimeType: "application/json",
  },
  async ({ userId }) => object(await db.getUserSettings(userId))
);

// Write: tool
server.tool(
  {
    name: "update-user-settings",
    description: "Update a user's settings",
    schema: z.object({
      userId: z.string(),
      settings: z.record(z.unknown()),
    }),
  },
  async ({ userId, settings }) => {
    await db.updateUserSettings(userId, settings);
    return text(`Updated settings for user ${userId}`);
  }
);
```

