# Advanced mcp-use Features

Use elicitation, sampling, notifications, output schemas, widgets, capability detection, and middleware to build production-grade MCP servers.

---

## 1. Elicitation (Asking Users for Input)

Elicitation pauses tool execution and requests structured input from the user via a form rendered by the client.

```typescript
import { MCPServer, text, object } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "config-server", version: "1.0.0" });

server.tool(
  { name: "create-config" },
  async (_args, ctx) => {
    const result = await ctx.elicit(
      "Configure your project",
      z.object({
        projectName: z.string().min(1).describe("Project name"),
        language: z.enum(["typescript", "javascript"]).describe("Language"),
        features: z.array(
          z.enum(["auth", "db", "cache"])
        ).describe("Features to enable"),
      })
    );

    if (result.action === "accept") {
      return object({
        config: result.data,
        message: `Project ${result.data.projectName} configured.`,
      });
    }
    return text("Configuration cancelled.");
  }
);
```

### Elicitation Rules

- Always check `result.action` before accessing `result.data`. Values: `"accept"`, `"decline"`, `"cancel"`.
- Use `.describe()` on every field — it becomes the form label.
- Use `.default()` to pre-fill and `.optional()` for optional fields.
- Supported types: `string`, `number`, `boolean`, `enum`, `array of enum`.

---

## 2. Sampling (LLM Completions from the Client)

Sampling requests an LLM completion from the connected client's model.

```typescript
server.tool(
  {
    name: "analyze-text",
    schema: z.object({ content: z.string() }),
  },
  async ({ content }, ctx) => {
    const result = await ctx.sample({
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Analyze for sentiment and key themes:\n\n${content}`,
          },
        },
      ],
      systemPrompt: "You are a text analysis expert. Be concise.",
      maxTokens: 500,
    });

    return text(result.content[0].text);
  }
);
```

### Sampling Considerations

- Requires the client to support the `sampling` capability — check `ctx.client.capabilities().sampling` first.
- The client may show a confirmation dialog before sending to the LLM.
- Use `maxTokens` to limit response length and cost.
- Not all clients support sampling — handle errors gracefully or provide a fallback.

---

## 3. Notifications

Send real-time notifications to connected clients for progress updates and state changes.

```typescript
// Broadcast to all connected sessions
await server.sendNotification("custom/update", { status: "ready" });

// Target a specific session
await server.sendNotificationToSession(sessionId, "custom/event", {
  type: "file-changed",
  path: "/data/report.csv",
});

// Notify clients that a resource has been updated
await server.sendResourceUpdated("data://reports/latest");

// Listen for client notifications
server.onRootsChanged(async (roots) => {
  console.error("Client roots changed:", roots);
});
```

### Progress Reporting in Long-Running Tools

```typescript
server.tool(
  {
    name: "process-batch",
    schema: z.object({ items: z.array(z.string()) }),
  },
  async ({ items }, ctx) => {
    for (let i = 0; i < items.length; i++) {
      await processItem(items[i]);
      await ctx.reportProgress({
        progress: i + 1,
        total: items.length,
        message: `Processing ${i + 1} of ${items.length}`,
      });
    }
    return text(`Processed ${items.length} items.`);
  }
);
```

---

## 4. Tool Output Schemas (Structured Output)

Define `outputSchema` to guarantee the shape of a tool's response. Return with `object()`.

```typescript
server.tool(
  {
    name: "get-weather",
    schema: z.object({ city: z.string() }),
    outputSchema: z.object({
      temperature: z.number().describe("Temperature in °F"),
      conditions: z.string(),
      humidity: z.number(),
    }),
  },
  async ({ city }) => {
    const weather = await fetchWeather(city);
    return object({
      temperature: weather.temp,
      conditions: weather.description,
      humidity: weather.humidity,
    });
  }
);
```

### Output Schema Rules

- Use `object()` (not `text()`) when `outputSchema` is defined.
- The returned object must match the schema exactly — extra or missing fields cause errors.
- Clients use the schema for type-safe parsing and UI rendering.

---

## 5. Widgets (React Components for MCP Apps)

Widgets return rich UI to clients that support MCP Apps. Always provide a fallback.

```typescript
server.tool(
  {
    name: "show-chart",
    schema: z.object({ data: z.array(z.number()) }),
    widget: {
      name: "chart-widget",       // matches a registered React component
      invoking: "Generating chart...",
      invoked: "Chart ready",
    },
  },
  async ({ data }, ctx) => {
    if (ctx.client.supportsApps()) {
      return widget({
        props: { data, type: "bar" },
        output: text(`Chart: ${data.join(", ")}`),
      });
    }
    return text(`Chart data: ${data.join(", ")}`);
  }
);
```

| Widget field | Purpose |
|---|---|
| `name` | Identifier matching a registered React component |
| `invoking` | Text shown while tool executes |
| `invoked` | Text shown after tool completes |

---

## 6. Client Capability Detection

Inspect the connected client to adapt tool behavior.

```typescript
server.tool(
  { name: "adaptive-response" },
  async (_args, ctx) => {
    const info = ctx.client.info();           // { name, version }
    const caps = ctx.client.capabilities();   // { sampling?, roots?, ... }
    const supportsApps = ctx.client.supportsApps();
    const caller = ctx.client.user();         // multi-tenant context

    if (supportsApps) {
      return widget({ props: { rich: true }, output: text("Widget") });
    }
    if (caps.sampling) {
      const analysis = await ctx.sample({
        messages: [{ role: "user", content: { type: "text", text: "Summarize." } }],
        maxTokens: 200,
      });
      return text(analysis.content[0].text);
    }
    return markdown("# Result\nPlain markdown for this client.");
  }
);
```

### Multi-Tenant Pattern

```typescript
server.tool(
  { name: "get-my-data", schema: z.object({ collection: z.string() }) },
  async ({ collection }, ctx) => {
    const user = ctx.client.user();
    if (!user) return text("Error: User context not available.");
    const data = await db.query(collection, { ownerId: user.id });
    return object({ items: data, owner: user.name });
  }
);
```

---

## 7. Middleware

mcp-use HTTP servers support Express-compatible and Hono-style middleware.

### Express Middleware

```typescript
import morgan from "morgan";
import cors from "cors";

server.use(morgan("combined"));
server.use(cors({ origin: "https://myapp.com" }));
```

### Path-Scoped Middleware

```typescript
import rateLimit from "express-rate-limit";

server.use("/mcp", rateLimit({ windowMs: 60_000, max: 100 }));
server.use("/api", requireApiKey);
```

### Hono-Style Middleware

```typescript
server.use(async (c, next) => {
  const start = Date.now();
  await next();
  console.error(`${c.req.method} ${c.req.path} — ${Date.now() - start}ms`);
});
```

### Custom Routes

```typescript
server.get("/health", (c) => c.json({ status: "ok" }));

server.post("/webhooks/github", async (c) => {
  const payload = await c.req.json();
  await handleWebhook(payload);
  return c.json({ received: true });
});
```

Middleware runs in registration order: CORS → logging → auth → rate limit → MCP handler.

---

## Feature Compatibility Matrix

| Feature | Claude Desktop | Claude Code | Inspector | Custom Client |
|---|---|---|---|---|
| Tools (basic) | ✅ | ✅ | ✅ | ✅ |
| Resources | ✅ | ✅ | ✅ | Depends |
| Prompts | ✅ | ✅ | ✅ | Depends |
| Elicitation | ✅ | ❌ | ❌ | Depends |
| Sampling | ✅ | ❌ | ❌ | Depends |
| Widgets / Apps | ❌ | ❌ | ❌ | Claude.ai only |
| Output Schemas | ✅ | ✅ | ✅ | ✅ |
| Notifications | ✅ | ✅ | ✅ | ✅ |
| Middleware | N/A (HTTP) | N/A (HTTP) | N/A | ✅ |

Always provide fallbacks for features that may not be supported.
