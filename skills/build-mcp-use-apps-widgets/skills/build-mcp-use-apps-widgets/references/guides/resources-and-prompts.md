# Resources and Prompts

Guide to registering resources (read-only data) and prompts (reusable LLM instruction templates) with the mcp-use `MCPServer` API.

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
import { object, text } from "mcp-use/server";

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

Available response helpers (import from `"mcp-use/server"`):

| Helper | Signature | Description |
|--------|-----------|-------------|
| `text` | `text(content: string)` | Plain-text response |
| `markdown` | `markdown(content: string)` | Markdown response |
| `html` | `html(content: string)` | HTML response |
| `xml` | `xml(content: string)` | XML response |
| `css` | `css(content: string)` | CSS response |
| `javascript` | `javascript(content: string)` | JavaScript response |
| `object` | `object(obj: any)` | JSON-serialised object |
| `array` | `array(items: any[])` | JSON array |
| `image` | `image(data: Buffer \| Uint8Array, mime: string)` | Binary image |
| `audio` | `audio(data: Buffer \| Uint8Array, mime: string)` | Binary audio |
| `binary` | `binary(data: Buffer \| Uint8Array, mime: string)` | Generic binary payload |
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
  async (uri, { userId }) => object(await db.getUser(userId))
);
```

The callback receives `(uri, params)` — `uri` is the resolved `URL` object, `params` is an object of extracted template variables. An optional third argument `ctx` provides auth and request context:

```typescript
server.resourceTemplate(
  { name: "private", uriTemplate: "private://{id}" },
  async (uri, { id }, ctx) => object(await getPrivateData(id, ctx.auth))
);
```

### Resource Annotations

Metadata that helps clients understand resource purpose and priority:

```typescript
server.resource(
  {
    name: "metrics",
    uri: "data://metrics",
    title: "System Metrics",
    mimeType: "application/json",
    annotations: {
      audience: ["user", "assistant"], // who should see this
      priority: 0.9,                   // 0.0 (low) to 1.0 (high)
      lastModified: new Date().toISOString(),
    },
  },
  async () => object(await getMetrics())
);
```

| Field | Type | Description |
| --- | --- | --- |
| `audience` | `('user' \| 'assistant')[]` | Who the resource is intended for |
| `priority` | `number` | Importance hint, 0.0–1.0 |
| `lastModified` | `string` | ISO 8601 timestamp of last change |

### Autocomplete for Template Variables

Provide completion suggestions so clients can autocomplete URI template values.

**List-based** — static array, automatically prefix-filtered:

```typescript
server.resourceTemplate(
  {
    name: "user",
    uriTemplate: "users://{userId}",
    callbacks: {
      complete: {
        userId: ["user-1", "user-2", "user-3"],
      },
    },
  },
  async (uri, { userId }) => object(await db.getUser(userId))
);
```

**Callback-based** — dynamic suggestions with context access:

```typescript
server.resourceTemplate(
  {
    name: "document",
    uriTemplate: "docs://{category}/{docId}",
    callbacks: {
      complete: {
        category: async (value) => categories.filter((c) => c.startsWith(value)),
        docId: async (value, context) => {
          const category = context?.arguments?.category;
          return docs.search(category, value).map((d) => d.id);
        },
      },
    },
  },
  async (uri, { category, docId }) => text((await db.getDocument(category, docId)).content)
);
```

Each callback receives `(currentInput, context?)`. The context `arguments` map contains previously resolved parameter values.

### Multiple Content Items

Return multiple content items from a single resource using `mix()`:

```typescript
import { text, object, image, mix } from "mcp-use/server";

server.resource(
  { name: "report-bundle", uri: "reports://latest", title: "Latest Reports Bundle" },
  async () => {
    const reportData = await getReportData();
    const chartImage = await generateChart(reportData);
    return mix(
      text("Executive Summary..."),
      object(reportData),
      image(chartImage, "image/png")
    );
  }
);
```

### Binary Resources

Return binary content (images, PDFs, audio) using `binary()`, `image()`, or `audio()`. Pass a `Buffer` or `Uint8Array` directly — no base64 encoding needed:

```typescript
import { readFile } from "node:fs/promises";
import { image } from "mcp-use/server";

server.resource(
  { name: "logo", uri: "assets://logo.png", title: "Company Logo", mimeType: "image/png" },
  async () => {
    const data = await readFile("./assets/logo.png");
    return image(data, "image/png");
  }
);
```

| Helper | Signature | Use |
|--------|-----------|-----|
| `image` | `image(data: Buffer \| Uint8Array, mime: string)` | Image files (PNG, JPEG, GIF, etc.) |
| `audio` | `audio(data: Buffer \| Uint8Array, mime: string)` | Audio files (MP3, WAV, etc.) |
| `binary` | `binary(data: Buffer \| Uint8Array, mime: string)` | Generic binary (PDF, ZIP, etc.) |

### UI Resources

Expose UI widgets to clients using `server.uiResource()`. The URI is auto-generated from the name.

> **Recommended pattern for MCP Apps**: Define widgets as React components in `resources/<name>/widget.tsx` and expose them through custom tools using the `widget` config and `widget()` response helper. This gives you full control over the tool schema, description, and business logic. `server.uiResource()` is for lower-level, non-React widget registration or custom HTML templates.

```typescript
server.uiResource({
  name: "dashboard-widget",
  type: "mcpApps",  // Recommended: dual-protocol (MCP Apps + ChatGPT)
  title: "Dashboard Widget",
  description: "Displays system metrics",
  htmlTemplate: "<div id='root'></div><script>...</script>",
  metadata: {
    csp: { connectDomains: ["https://api.example.com"] },
    prefersBorder: true,
    autoResize: true,          // MCP Apps clients: auto-resize iframe
    widgetDescription: "...",  // ChatGPT: shown in tool invocation UI
    invoking: "Loading...",    // Status text while tool runs
    invoked: "Ready",          // Status text after completion
  },
});
```

**Supported `type` values:**

| Type | Protocol | Notes |
|---|---|---|
| `mcpApps` | MCP Apps + ChatGPT Apps SDK | **Recommended.** Dual-protocol; auto-generates metadata for both |
| `appsSdk` | ChatGPT only | Deprecated in favor of `mcpApps` |
| `externalUrl` | MCP-UI | Embeds an external URL in an iframe |
| `rawHtml` | MCP-UI | Serves raw HTML inline |
| `remoteDom` | MCP-UI | Remote DOM rendering |

Use `mcpApps` for all new widgets — it supports both MCP Apps clients (Claude, Goose, etc.) and ChatGPT automatically.

### Widget Registration via `widget.tsx`

For React widgets in `resources/<name>/widget.tsx`, the `WidgetMetadata` export controls widget behavior:

```typescript
// resources/my-widget/widget.tsx
export const widgetMetadata: WidgetMetadata = {
  description: "Widget description",
  props: z.object({ ... }),          // Runtime props schema
  exposeAsTool: false,               // true = auto-register as MCP resource tool; default: false
  annotations: { readOnlyHint: true },
  metadata: {
    prefersBorder: true,
    autoResize: true,
    csp: { connectDomains: ["https://api.example.com"] },
    widgetDescription: "...",        // ChatGPT-specific
  },
};
```

> **`exposeAsTool`** — when `true`, the widget is auto-registered as both an MCP resource and a tool. When `false` (default), use a custom `server.tool()` with `widget: { name }` and `widget()` response helper for full control.

### Notifying Resource Changes

Two notification methods for keeping clients in sync:

```typescript
// List changed — after adding/removing resources dynamically
server.resource(
  { name: "new-data", uri: "data://new", description: "Dynamically added" },
  async () => text("New content")
);
await server.sendResourcesListChanged();

// Content updated — after a specific resource's data changes
await server.notifyResourceUpdated("data://metrics");
```

- `sendResourcesListChanged()` — tells clients to re-fetch the resource list
- `notifyResourceUpdated(uri)` — tells subscribed clients to re-read that resource

### Resource Best Practices

1. **Use descriptive URI schemes** — `docs://`, `users://`, `config://`. Schemes act as namespaces.
2. **Set `mimeType` accurately** — clients use it for rendering (`application/json`, `text/markdown`, `image/png`).
3. **Keep resources read-only** — never mutate state in a resource handler. Use tools for writes.
4. **Use template parameters, not query strings** — `users://{userId}` not `users://lookup?id={userId}`.
5. **Provide completion for dynamic templates** — use `callbacks.complete` for parameters with many values.
6. **Keep payloads focused** — return only needed data. Cap large lists.

---

## Prompts

Prompts are **reusable instruction templates** that guide LLM interactions with structured, parameterized messages.

### Prompt Registration

Use `server.prompt(definition, handler)` with a Zod schema for input validation:

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
  { name: "new-prompt", description: "Dynamically added", schema: z.object({ topic: z.string() }) },
  async ({ topic }) => text(`You are an expert in ${topic}.`)
);
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

---

## Migration Notes

### Binary Helper Signatures

`image()`, `audio()`, and `binary()` accept `Buffer | Uint8Array` directly — **do not** call `.toString("base64")` before passing data.
- ❌ `image(buffer.toString("base64"), "image/png")`
- ✅ `image(buffer, "image/png")`

### Deprecated Notification Method

`server.notifyResourcesChanged()` is deprecated. Use `server.sendResourcesListChanged()` instead.

### List-based Completion Filtering

Static `complete` arrays and `completable` static lists now perform **case-insensitive** prefix filtering automatically.
