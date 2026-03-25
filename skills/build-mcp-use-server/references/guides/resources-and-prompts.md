# Resources and Prompts

Guide to registering resources (read-only data) and prompts (reusable LLM instruction templates) with the `MCPServer` API.

---

## When to Use Which Primitive

| Primitive | Purpose | Example |
| --- | --- | --- |
| **Resource** | Data the agent can read | Config, user profiles, logs |
| **Tool** | Actions the agent can perform | Update settings, send email |
| **Prompt** | Templates the user can invoke | Code review instructions, debug workflow |

```
Need to expose data? → Read-only? → Yes → RESOURCE / No → TOOL
Need to guide the LLM? → Reusable? → Yes → PROMPT / No → Tool description
```

---

## Resources

Resources expose **read-only data** to MCP clients — config, documents, database records, files — without side effects.

### Static Resources

Use `server.resource(definition, handler)` with a fixed URI:

```typescript
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
  { name: "readme", uri: "docs://readme", title: "README", mimeType: "text/markdown" },
  async () => text("# My Project\n\nWelcome to the project.")
);
```

- `uri` is a **fixed string** — no template parameters
- Use `object()` for JSON, `text()` for plain text / markdown

Available response helpers for resource content:

```typescript
import {
  text, markdown, html, xml, css, javascript, object, array,
  image, audio, binary, mix,
} from 'mcp-use/server';
```

| Helper | Signature | Description |
|--------|-----------|-------------|
| `text` | `text(content: string)` | Plain-text or markdown response |
| `markdown` | `markdown(content: string)` | Markdown response |
| `html` | `html(content: string)` | HTML response |
| `xml` | `xml(content: string)` | XML response |
| `css` | `css(content: string)` | CSS response |
| `javascript` | `javascript(content: string)` | JavaScript response |
| `object` | `object(obj: any)` | JSON-serialised object |
| `array` | `array(items: any[])` | JSON array |
| `image` | `image(data: string, mimeType?: string)` | Base64-encoded image (default: `image/png`) |
| `audio` | `audio(dataOrPath: string, mimeType?: string)` | Base64 string or file path (path returns Promise) |
| `binary` | `binary(base64Data: string, mimeType: string)` | Base64-encoded binary data |
| `mix` | `mix(...responses: Response[])` | Composite response with multiple items |

### Resource Templates

Templates use `{paramName}` placeholders. Use `server.resourceTemplate()` with `uriTemplate`:

```typescript
server.resourceTemplate(
  {
    name: "user-profile",
    uriTemplate: "users://{userId}/profile",
    title: "User Profile",
    mimeType: "application/json",
  },
  async (uri, { userId }) => {
    const user = await db.getUser(userId);
    if (!user) throw new Error("User not found");
    return object(user);
  }
);
```

The callback receives `(uri, params)` — `uri` is the resolved `URL` object, `params` is an object of extracted template variables. An optional third argument `ctx` provides auth and request context:

```typescript
server.resourceTemplate(
  { name: "private", uriTemplate: "private://{id}" },
  async (uri, { id }, ctx) => {
    // Check permissions
    if (!ctx.auth?.userId) throw new Error("Unauthorized");
    return object(await getPrivateData(id));
  }
);
```

### Autocomplete for Template Variables

Provide completion suggestions for URI template variables so clients can autocomplete values. Use the `callbacks.complete` property on the resource template definition:

**List-based** — static array, auto-filtered by prefix:

```typescript
server.resourceTemplate({
  name: 'user_data',
  uriTemplate: 'user://{userId}/profile',
  callbacks: {
    complete: {
      userId: ['user-1', 'user-2', 'user-3'],
    },
  },
}, async (uri, { userId }) => {
  const userData = await fetchUserData(userId);
  return text(`User name: ${userData.name}`);
});
```

**Callback-based** — dynamic suggestions:

```typescript
server.resourceTemplate({
  name: 'user_data',
  uriTemplate: 'user://{userId}/profile',
  callbacks: {
    complete: {
      userId: async (value) => (await fetchUserIds(value)).map(u => u.id),
    },
  },
}, async (uri, { userId }) => {
  const userData = await fetchUserData(userId);
  return text(`User name: ${userData.name}`);
});
```

### Resource Annotations

Provide metadata to help clients use resources effectively:

```typescript
server.resource(
  {
    name: 'app_config',
    uri: 'config://application',
    annotations: {
      // Target audience: 'user' or 'assistant'
      audience: ['user'],
      // Priority: 0.0 to 1.0
      priority: 0.9,
      // Last modified timestamp
      lastModified: new Date().toISOString(),
    },
  },
  async () => object({ version: '1.0.0', environment: 'production' })
);
```

### URI Template Patterns

URI templates follow RFC 6570 Level 1 (simple expansion).

| Template | URI | Extracted Params |
|---|---|---|
| `users://{id}` | `users://123` | `{ id: "123" }` |
| `docs://{category}/{id}` | `docs://api/auth` | `{ category: "api", id: "auth" }` |
| `logs://{date}/{level}` | `logs://2023-01-01/error` | `{ date: "2023-01-01", level: "error" }` |

**Note:** Only simple variable expansion `{var}` is supported. Reserved characters like `?` or `#` are treated as literals in the template but delimiters in the URI.

### Dynamic Resource Listing

Resources can be completely dynamic, fetched from a database or external API.

```typescript
// Register a template that covers many potential resources
server.resourceTemplate(
  {
    name: "issue",
    uriTemplate: "issues://{repo}/{number}",
    title: "GitHub Issue",
    mimeType: "application/json",
  },
  async (uri, { repo, number }) => {
    const issue = await github.getIssue(repo, number);
    return object(issue);
  }
);
```

To help clients discover these resources, use `listRoots()` and `onRootsChanged()` (see `notifications-and-subscriptions.md`).

---

## Dynamic Resource Examples

### Database Records

```typescript
server.resourceTemplate(
  {
    name: "user",
    uriTemplate: "users://{id}",
    mimeType: "application/json",
  },
  async (uri, { id }) => {
    const user = await db.users.findUnique({ where: { id } });
    if (!user) throw new Error(`User ${id} not found`);
    return object(user);
  }
);
```

### File System Access

```typescript
import { readFile } from "fs/promises";
import { join } from "path";

server.resourceTemplate(
  {
    name: "log-file",
    uriTemplate: "logs://{date}/{file}",
    mimeType: "text/plain",
  },
  async (uri, { date, file }) => {
    // Security: Validate path to prevent traversal
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new Error("Invalid date");
    if (!/^[a-z0-9-]+\.log$/.test(file)) throw new Error("Invalid file");

    const path = join(process.cwd(), "logs", date, file);
    const content = await readFile(path, "utf-8");
    return text(content);
  }
);
```

### External API Proxy

```typescript
server.resourceTemplate(
  {
    name: "github-issue",
    uriTemplate: "github://{owner}/{repo}/issues/{number}",
    mimeType: "application/json",
  },
  async (uri, { owner, repo, number }) => {
    const response = await fetch(
      `https://api.github.com/repos/${owner}/${repo}/issues/${number}`
    );
    if (!response.ok) throw new Error("GitHub API error");
    return object(await response.json());
  }
);
```

---

## URI Scheme Design

Choosing a good URI scheme is critical for resource discoverability.

### Best Practices

1.  **Use a unique scheme prefix**: `myapp://` or `vendor://` prevents collisions.
2.  **Follow RESTful hierarchy**: `resource://collection/id/subresource`.
3.  **Keep it readable**: Use kebab-case for segments.
4.  **Avoid query parameters**: Use path segments for identification (`users/123` not `users?id=123`).

| Bad | Good | Why |
|---|---|---|
| `data://get?id=1` | `data://items/1` | Path params are easier to route |
| `file:///tmp/foo` | `app://files/foo` | Abstract implementation details |
| `config` | `config://main` | Missing scheme makes routing ambiguous |

### URI Template Syntax (RFC 6570)

The `uriTemplate` property supports Level 1 templates:

- `{var}`: Simple string expansion.
- Characters allowed in var names: `a-z`, `A-Z`, `0-9`, `_`.
- Reserved characters in values (`/`, `?`, `#`) are percent-encoded.

```typescript
// Template: "users://{id}"
// Value: "user/1"
// Result: "users://user%2F1" (encoded)
```

---

## Pagination and Large Datasets

Resources are retrieved as a single blob. For large datasets, use pagination patterns in your URI design.

```typescript
server.resourceTemplate(
  {
    name: "users-page",
    uriTemplate: "users://page/{page}",
    mimeType: "application/json",
  },
  async (uri, { page }) => {
    const pageNum = parseInt(page);
    const users = await db.users.findMany({
      skip: (pageNum - 1) * 20,
      take: 20,
    });
    return object({
      data: users,
      next: `users://page/${pageNum + 1}`,
      prev: pageNum > 1 ? `users://page/${pageNum - 1}` : null,
    });
  }
);
```

---

## Multiple Content Items

Resources can return multiple content items using the `mix()` helper:

```typescript
import { mix, text, object, image } from "mcp-use/server";

server.resource(
  {
    name: 'report_bundle',
    uri: 'reports://latest',
    title: 'Latest Reports Bundle',
  },
  async () => {
    const reportData = await getReportData();
    const chartImage = await generateChart(reportData);

    return mix(
      text('Executive Summary...'),
      object(reportData),
      image(chartImage, 'image/png')
    );
  }
);
```

---

## Callback Signature Variations

Resource handlers support multiple callback signatures. Use the simplest one that meets your needs:

```typescript
import { text, object } from 'mcp-use/server';

// No parameters — for static resources with no URI information needed
server.resource(
  { name: 'welcome', uri: 'app://welcome' },
  async () => text('Welcome to our API!')
);

// URI only — when you need the full resolved URI
server.resource(
  { name: 'echo', uri: 'echo://{path}' },
  async (uri) => text(`You requested: ${uri.toString()}`)
);

// URI and params — most common pattern for templates
server.resourceTemplate(
  { name: 'user', uriTemplate: 'user://{userId}' },
  async (uri, { userId }) => {
    const user = await fetchUser(userId);
    return object(user);
  }
);

// With context — for auth or request access
server.resourceTemplate(
  { name: 'private', uriTemplate: 'private://{id}' },
  async (uri, { id }, ctx) => {
    const user = ctx.auth;
    const data = await getPrivateData(id, user);
    return object(data);
  }
);
```

---

## Notifying Clients of Resource Changes

When dynamically adding or removing resources, notify clients to refresh their resource cache:

```typescript
// Register a new resource dynamically
server.resource(
  {
    name: 'new_resource',
    uri: 'app://new',
    description: 'A dynamically added resource',
  },
  async () => text('New resource content')
);

// Notify all connected clients
await server.sendResourcesListChanged();
```

---

## Binary Resources

Use the `binary()` or `image()` helpers for non-text content.

### Images

```typescript
import { image } from "mcp-use/server";
import { readFile } from "fs/promises";

server.resource(
  {
    name: "logo",
    uri: "assets://logo.png",
    mimeType: "image/png",
  },
  async () => {
    const buffer = await readFile("./public/logo.png");
    return image(buffer.toString("base64"), "image/png");
  }
);
```

### PDF Documents

```typescript
import { binary } from "mcp-use/server";

server.resourceTemplate(
  {
    name: "invoice",
    uriTemplate: "invoices://{id}.pdf",
    mimeType: "application/pdf",
  },
  async (uri, { id }) => {
    const pdfBuffer = await generateInvoicePdf(id);
    return binary(pdfBuffer.toString("base64"), "application/pdf");
  }
);
```

### Audio

```typescript
import { audio } from "mcp-use/server";
import { readFile } from "fs/promises";

server.resource(
  {
    name: "notification-sound",
    uri: "assets://notification.mp3",
    mimeType: "audio/mpeg",
  },
  async () => {
    const buffer = await readFile("./assets/notification.mp3");
    return audio(buffer.toString("base64"), "audio/mpeg");
  }
);
```

---

## Prompt Engineering for MCP

Prompts are the interface between the user and the LLM's reasoning capabilities.

### Context Injection

Reference resources directly in your prompt text. Smart clients (like Claude) can resolve these references.

```typescript
server.prompt(
  { name: "analyze-user", schema: z.object({ userId: z.string() }) },
  async ({ userId }) => text(`
Please analyze the user profile at users://${userId}.
Check their recent activity at logs://${userId}/recent.
Recommend next steps based on config://marketing-rules.
`)
);
```

### Multi-Turn Conversation Templates

Use the `{ messages: [] }` return format to seed a conversation history.

```typescript
server.prompt(
  {
    name: "debug-session",
    description: "Start a debugging session with context",
    schema: z.object({ error: z.string() }),
  },
  async ({ error }) => ({
    messages: [
      {
        role: "system",
        content: "You are a senior reliability engineer. Focus on root cause analysis.",
      },
      {
        role: "user",
        content: `I'm seeing this error: ${error}`,
      },
      {
        role: "assistant",
        content: "I understand. Let's check the system logs first.",
      },
      {
        role: "user",
        content: "Please query the logs for the last 15 minutes.",
      },
    ],
  })
);
```

### Prompt Arguments as Configuration

Use prompt arguments to toggle behavior or set strict constraints.

```typescript
server.prompt(
  {
    name: "write-sql",
    schema: z.object({
      dialect: z.enum(["postgres", "mysql", "sqlite"]),
      complexity: z.enum(["simple", "optimized", "explained"]),
    }),
  },
  async ({ dialect, complexity }) => text(`
Write a SQL query for the following request.
Dialect: ${dialect}
Output Style: ${complexity}
- simple: Just the query
- optimized: Query with performance comments
- explained: Query plus execution plan explanation
`)
);
```

---

## Advanced: Dynamic Resource Roots

To let clients know about all available resources (e.g. all 10,000 users), implementing `listRoots` is inefficient. Instead, expose a "root" resource that lists others, or rely on `resourceTemplate` matching.

However, if you have a small, dynamic set of resources (e.g. open tabs, active processes), you can use `sendResourcesListChanged`.

```typescript
// Store resources in memory
const activeFiles = new Set<string>();

// Dynamic resource handler
server.resourceTemplate(
  { name: "file", uriTemplate: "file://{path}" },
  async (uri, { path }) => {
    if (!activeFiles.has(path)) throw new Error("File not open");
    return text(await readFile(path, "utf-8"));
  }
);

// Tool to open a file (updates the resource list)
server.tool(
  { name: "open-file", schema: z.object({ path: z.string() }) },
  async ({ path }) => {
    activeFiles.add(path);
    await server.sendResourcesListChanged(); // Notify client
    return text(`Opened ${path}`);
  }
);
```

---

## Prompts

Prompts are **reusable instruction templates** that guide LLM interactions with structured, parameterized messages.

### Prompt Structure

Every prompt has these main fields:

```typescript
server.prompt({
  name: 'prompt_name',              // Unique identifier (required)
  title: 'Prompt Title',            // Human-readable display name (optional, falls back to name)
  description: 'What it generates', // Clear description (optional)
  schema: z.object({...}),          // Zod schema for arguments (optional)
}, async (args) => {...})           // Generator function
```

**`PromptDefinition` fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Unique identifier |
| `title` | `string` | No | Human-readable display name; falls back to `name` |
| `description` | `string` | No | Description shown to users when listing prompts |
| `schema` | `z.ZodObject` | No | Zod schema for argument validation |
| `args` | `InputDefinition[]` | No | **Deprecated.** Use `schema` (Zod) instead. |
| `cb` | `PromptCallback` | No | Inline handler (alternative to separate callback argument) |

### Prompt Registration with Metadata

Use `server.prompt(definition, handler)` with a Zod schema for input validation:

```typescript
import { z } from "zod";

server.prompt(
  {
    name: "code-review",
    description: "Review code for bugs and improvements",
    schema: z.object({
      code: z.string().describe("Source code to review"),
      language: z.string().default("typescript").describe("Programming language"),
    }),
  },
  async ({ code, language }) =>
    text(`Review this ${language} code for bugs and improvements:\n\n\`\`\`${language}\n${code}\n\`\`\``)
);
```

The `schema` uses Zod — enums, defaults, optionals, and all standard validators work. Each field's `.describe()` tells clients what to provide. The server validates inputs before calling your handler.

### Response Format

Two ways to return prompt content:

**Manual message construction** — full control over roles and content types:

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
      { role: "system", content: "You are an expert debugger." },
      { role: "user", content: `Debug this error: ${error}` },
      ...(context
        ? [{ role: "user", content: `Context: ${context}` }]
        : []),
    ],
  })
);
```

**Response helpers** — cleaner, auto-converted to `GetPromptResult`:

```typescript
import { text, object, mix } from "mcp-use/server";

server.prompt(
  { name: "greeting", description: "Generate a greeting", schema: z.object({ name: z.string() }) },
  async ({ name }) => text(`Hello, ${name}! How can I assist you today?`)
);
```

### Multi-Message Prompts

System + user message patterns for structured conversations:

```typescript
server.prompt(
  {
    name: "analyze-config",
    description: "Analyze application configuration",
    schema: z.object({ focus: z.string().describe("Area to focus on") }),
  },
  async ({ focus }) => ({
    messages: [
      {
        role: "user",
        content: "Here is the current application configuration (from config://app). Please review it.",
      },
      {
        role: "user",
        content: `Analyze this configuration focusing on ${focus}. Flag any issues.`,
      },
    ],
  })
);
```

Omit the schema entirely for fixed instructions with no parameters:

```typescript
server.prompt(
  { name: "summarize-logs", description: "Summarize recent application logs" },
  async () => text("Retrieve the recent logs and summarize errors, warnings, and unusual patterns.")
);
```

### Autocomplete for Prompt Arguments

Use `completable()` to provide completion suggestions for prompt arguments.

**List-based** — static array, auto-filtered by prefix:

```typescript
import { completable } from "mcp-use/server";

server.prompt(
  {
    name: "code-review",
    description: "Review code with language completion",
    schema: z.object({
      language: completable(z.string(), ["python", "javascript", "typescript", "java", "cpp"]),
      code: z.string().describe("The code to review"),
    }),
  },
  async ({ language, code }) => text(`Review this ${language} code: ${code}`)
);
```

**Callback-based** — dynamic suggestions with access to other argument values:

```typescript
server.prompt(
  {
    name: "analyze-project",
    description: "Analyze a project with dynamic completion",
    schema: z.object({
      projectId: completable(z.string(), async (value, context) => {
        const userId = context?.arguments?.userId;
        const projects = await fetchUserProjects(userId);
        return projects.filter((p) => p.id.startsWith(value)).map((p) => p.id);
      }),
    }),
  },
  async ({ projectId }) => text(`Analyzing project ${projectId}...`)
);
```

`completable(zodType, valuesOrCallback)` wraps a Zod type so the server provides completion. Use arrays for fixed lists (auto case-insensitive prefix-filtered by the server), callbacks for dynamic values.

### Notifying Prompt Changes

When dynamically adding or removing prompts, notify clients:

```typescript
server.prompt(
  {
    name: "new_prompt",
    description: "A dynamically added prompt",
    schema: z.object({ topic: z.string() }),
  },
  async ({ topic }) => ({
    messages: [{ role: "system", content: `Expert in ${topic}` }],
  })
);

// Notify all connected clients
await server.sendPromptsListChanged();
```

### Prompt Best Practices

1. **Use prompts for reusable instruction templates** — extract repeated LLM instructions into prompts.
2. **Keep schema parameters minimal** — each parameter should have `.describe()`. Fewer params = better UX.
3. **Use multi-message format for structured conversations** — system context + user instructions.
4. **Reference resources by URI in prompts** — mention resource URIs in prompt text so the LLM knows what data to consult.
5. **Prompts complement tools** — tools perform actions, prompts guide the LLM on *how to think*.

---

## Common Patterns

### Resource + Tool Pair

```typescript
// Read: resource template
server.resourceTemplate(
  { name: "user-settings", uriTemplate: "settings://{userId}", title: "User Settings", mimeType: "application/json" },
  async (uri, { userId }) => object(await db.getUserSettings(userId))
);

// Write: tool
server.tool(
  {
    name: "update-user-settings",
    description: "Update a user's settings",
    schema: z.object({ userId: z.string(), settings: z.record(z.unknown()) }),
  },
  async ({ userId, settings }) => {
    await db.updateUserSettings(userId, settings);
    return text(`Updated settings for user ${userId}`);
  }
);
```

## Resource Patterns

### URI Schemes

```typescript
// ❌ BAD: Query parameters
uriTemplate: "users://get?id={id}"

// ✅ GOOD: Path parameters
uriTemplate: "users://{id}"
```

### Prompt Schemas

```typescript
// ❌ BAD: Too many optional fields
z.object({ a: z.string().optional(), b: z.string().optional() })

// ✅ GOOD: Focused schema
z.object({ mode: z.enum(["quick", "full"]) })
```

### Static Data

```typescript
// ❌ BAD: Static resource for data that varies per user
server.resource(
  { name: "user", uri: "users://me" },
  async () => object(currentUser)
);

// ✅ GOOD: Dynamic template for variable data
server.resourceTemplate(
  { name: "user", uriTemplate: "users://{id}" },
  async (uri, { id }) => object(await fetchUser(id))
);
```

## Troubleshooting Resources

### Resource Not Found (404)

If a client cannot read a resource:
1. Check the URI scheme matches exactly (`users://` vs `user://`).
2. Verify template parameters match the regex (simple string expansion only).
3. Check logs for handler errors.

### Invalid Template

`Error: Invalid URI template`
- Templates must follow RFC 6570 Level 1.
- Only `{var}` is allowed. No `{?query}` or `{*path}`.

### Performance Issues

Large binary resources can block the main thread.
- Use streams if available (future API).
- Offload generation to worker threads.
- Cache results using a simple LRU cache.

---

## Advanced: Resource Subscriptions

Real-time applications rely on resource updates.

### Manual Notifications

When a resource changes, notify all subscribers.

```typescript
// Update database
await db.users.update(id, data);

// Notify MCP clients
await server.notifyResourceUpdated(`users://${id}`);
```

### Batch Notifications

If many resources change at once, send a list update.

```typescript
// Mass update
await db.users.updateMany({ active: false });

// Force re-fetch of resource list
await server.sendResourcesListChanged();
```

### Subscription Lifecycle

Clients subscribe to specific URIs. The server does not track subscriptions manually; the transport layer handles routing `notifications/resources/updated` messages to interested clients.

---

## Migration from v1.0

### `readResource` -> `resources/read`

The method name in JSON-RPC changed, but the `server.resource()` API remains the same.

### URI Scheme Changes

v2.0 enforces stricter URI parsing. Ensure your URIs are valid URLs (e.g., must have a scheme).
- ❌ `config.json`
- ✅ `file:///config.json` or `config://main`

### Binary Helper Signatures

`image()`, `audio()`, and `binary()` accept base64 **strings** — you MUST call `.toString("base64")` on Buffers before passing.
- ❌ `image(buffer, "image/png")` — wrong type, Buffer is not accepted
- ✅ `image(buffer.toString("base64"), "image/png")` — correct, base64 string

### Deprecated Notification Method

`server.notifyResourcesChanged()` is deprecated. Use `server.sendResourcesListChanged()` instead.

### List-based Completion Filtering

Static `complete` arrays now perform **case-insensitive** prefix filtering automatically.
