# MCP App Server Recipes

Complete, copy-pasteable server examples for building MCP Apps — widget-enabled MCP servers using mcp-use TypeScript (v1.21.4, zod ^4.0.0).

The key difference from plain MCP servers: tools return `widget({ props, message })` and reference a widget component in `resources/`.

---

## Recipe 1: Weather Widget Server

A server with a weather tool that renders an interactive widget. Demonstrates `widget()` response, dual-protocol support, and a REST endpoint for widget data.

```typescript
import { MCPServer, widget, text, object, error } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "weather-server",
  version: "1.0.0",
  description: "Weather data with interactive widget display",
  baseUrl: process.env.MCP_URL,
});

const cache = new Map<string, { data: any; expires: number }>();

async function getWeather(city: string) {
  const c = cache.get(city);
  if (c && Date.now() < c.expires) return c.data;
  const apiKey = process.env.OPENWEATHER_API_KEY;
  const res = await fetch(
    `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(city)}&units=metric&appid=${apiKey}`
  );
  if (!res.ok) throw new Error(`Weather API ${res.status}`);
  const data = await res.json();
  cache.set(city, { data, expires: Date.now() + 600_000 });
  return data;
}

server.tool(
  {
    name: "get-weather",
    description: "Get current weather for a city",
    schema: z.object({
      city: z.string().describe("City name"),
      units: z.enum(["metric", "imperial"]).default("metric"),
    }),
    widget: {
      name: "weather-display",       // matches resources/weather-display/
      invoking: "Fetching weather...",
      invoked: "Weather loaded",
    },
  },
  async ({ city, units }) => {
    try {
      const data = await getWeather(city);
      return widget({
        props: {
          city: data.name,
          temperature: Math.round(data.main.temp),
          conditions: data.weather[0].main,
          humidity: data.main.humidity,
          windSpeed: data.wind.speed,
          units,
        },
        message: `Weather in ${data.name}: ${Math.round(data.main.temp)}°${units === "metric" ? "C" : "F"}, ${data.weather[0].description}`,
      });
    } catch (e) {
      return error((e as Error).message);
    }
  }
);

// REST endpoint for widget to fetch fresh data
server.get("/api/weather/:city", async (c) => {
  try {
    return c.json(await getWeather(c.req.param("city")));
  } catch (e) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

server.resource(
  { name: "monitored-cities", uri: "weather://monitored", title: "Monitored Cities" },
  async () => object({ cities: ["Tokyo", "London", "New York", "Paris"] })
);

await server.listen();
```

**`resources/weather-display/widget.tsx`** — see `widget-recipes.md` Recipe 1 for the full component.

---

## Recipe 2: Product Search Widget Server

A product search tool with widget response and additional tools callable from the widget.

```typescript
import { MCPServer, widget, object, error } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "product-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL,
});

// Main tool — returns widget response
server.tool(
  {
    name: "search-products",
    description: "Search for products by query and display results interactively",
    schema: z.object({
      query: z.string().describe("Search query"),
      category: z.string().optional().describe("Product category filter"),
      limit: z.number().int().min(1).max(20).default(8),
    }),
    widget: {
      name: "product-carousel",
      invoking: "Searching products...",
      invoked: "Products found",
    },
  },
  async ({ query, category, limit }) => {
    // Replace with real product API
    const products = Array.from({ length: limit }, (_, i) => ({
      id: `prod-${i + 1}`,
      name: `${query} Product ${i + 1}`,
      price: Math.round(Math.random() * 200 + 10),
      image: `/products/placeholder-${(i % 4) + 1}.png`,
      rating: Math.round(Math.random() * 20 + 30) / 10,
      category: category ?? "general",
    }));

    return widget({
      props: { products, query, totalResults: products.length },
      message: `Found ${products.length} products for "${query}"`,
    });
  }
);

// Secondary tool — called from the widget via useCallTool
server.tool(
  {
    name: "get-product-details",
    description: "Get detailed info about a specific product",
    schema: z.object({ productId: z.string() }),
  },
  async ({ productId }) => {
    return object({
      id: productId,
      name: `Product ${productId}`,
      description: "A high-quality product with great reviews.",
      price: 49.99,
      specs: { weight: "200g", dimensions: "10x5x3cm" },
      reviews: 128,
    });
  }
);

// Secondary tool — called from the widget via useCallTool
server.tool(
  {
    name: "toggle-favorite",
    description: "Add or remove a product from favorites",
    schema: z.object({
      productId: z.string(),
      action: z.enum(["add", "remove"]),
    }),
  },
  async ({ productId, action }, ctx) => {
    const userId = ctx.client.user()?.subject;
    // Persist to database if userId available
    return object({
      productId,
      favorited: action === "add",
      message: `Product ${action === "add" ? "added to" : "removed from"} favorites`,
    });
  }
);

await server.listen();
```

---

## Recipe 3: Analytics Dashboard Server

A dashboard server with a single tool that returns rich analytics data for a widget.

```typescript
import { MCPServer, widget, object, text } from "mcp-use/server";
import { z } from "zod";
import pg from "pg";

const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });

const server = new MCPServer({
  name: "analytics-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL,
});

server.tool(
  {
    name: "get-analytics",
    description: "Get analytics dashboard data for a date range",
    schema: z.object({
      range: z.enum(["7d", "30d", "90d"]).default("7d").describe("Date range"),
    }),
    widget: {
      name: "data-dashboard",
      invoking: "Loading analytics...",
      invoked: "Dashboard ready",
    },
  },
  async ({ range }) => {
    const days = range === "7d" ? 7 : range === "30d" ? 30 : 90;
    const since = new Date(Date.now() - days * 86400000).toISOString();

    // Replace with real analytics queries
    const { rows: summary } = await pool.query(
      `SELECT
        COUNT(DISTINCT session_id) AS total_visitors,
        COUNT(*) AS page_views,
        ROUND(AVG(bounce::int) * 100, 1) AS bounce_rate,
        ROUND(AVG(session_duration)) AS avg_session_duration
       FROM page_events WHERE occurred_at > $1`,
      [since]
    );

    const { rows: topPages } = await pool.query(
      `SELECT path, COUNT(*) AS views,
        ROUND((COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY COUNT(*) DESC))
          / NULLIF(LAG(COUNT(*)) OVER (ORDER BY COUNT(*) DESC), 0) * 100, 1) AS change
       FROM page_events WHERE occurred_at > $1
       GROUP BY path ORDER BY views DESC LIMIT 5`,
      [since]
    );

    return widget({
      props: { summary: summary[0], topPages, range },
      message: `Analytics for ${range}: ${summary[0].total_visitors} visitors, ${summary[0].page_views} page views`,
    });
  }
);

process.on("SIGINT", async () => { await pool.end(); process.exit(0); });
await server.listen();
```

---

## Recipe 4: Kanban Board Server

A task management server with a board widget, drag-and-drop state, and tools callable from the widget.

```typescript
import { MCPServer, widget, object, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "kanban-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL,
});

interface Task {
  id: string;
  title: string;
  column: "todo" | "in-progress" | "done";
  priority: "low" | "medium" | "high";
}

// In production, persist to a database keyed by userId
const projectTasks = new Map<string, Task[]>();

server.tool(
  {
    name: "show-kanban",
    description: "Display a kanban board for a project",
    schema: z.object({
      projectName: z.string().describe("Project name"),
    }),
    widget: {
      name: "kanban-board",
      invoking: "Loading board...",
      invoked: "Board ready",
    },
  },
  async ({ projectName }, ctx) => {
    const userId = ctx.client.user()?.subject ?? "default";
    const key = `${userId}:${projectName}`;

    if (!projectTasks.has(key)) {
      projectTasks.set(key, [
        { id: "1", title: "Design homepage", column: "todo", priority: "high" },
        { id: "2", title: "Set up CI/CD", column: "todo", priority: "medium" },
        { id: "3", title: "API authentication", column: "in-progress", priority: "high" },
        { id: "4", title: "Project scaffolding", column: "done", priority: "medium" },
      ]);
    }

    const tasks = projectTasks.get(key)!;
    return widget({
      props: {
        projectName,
        columns: ["todo", "in-progress", "done"],
        tasks,
      },
      message: `Kanban board for "${projectName}": ${tasks.length} tasks`,
    });
  }
);

server.tool(
  {
    name: "update-task",
    description: "Move a task or update its priority/title",
    schema: z.object({
      projectName: z.string(),
      taskId: z.string(),
      column: z.string().optional(),
      priority: z.enum(["low", "medium", "high"]).optional(),
      title: z.string().optional(),
    }),
  },
  async ({ projectName, taskId, column, priority, title }, ctx) => {
    const userId = ctx.client.user()?.subject ?? "default";
    const key = `${userId}:${projectName}`;
    const tasks = projectTasks.get(key) ?? [];
    const task = tasks.find((t) => t.id === taskId);
    if (!task) return object({ success: false, error: `Task not found: ${taskId}` });
    if (column) task.column = column as Task["column"];
    if (priority) task.priority = priority;
    if (title) task.title = title;
    return object({ taskId, updated: { column, priority, title }, success: true });
  }
);

server.tool(
  {
    name: "create-task",
    description: "Create a new task on the board",
    schema: z.object({
      projectName: z.string(),
      title: z.string(),
      column: z.string().default("todo"),
      priority: z.enum(["low", "medium", "high"]).default("medium"),
    }),
  },
  async ({ projectName, title, column, priority }, ctx) => {
    const userId = ctx.client.user()?.subject ?? "default";
    const key = `${userId}:${projectName}`;
    const tasks = projectTasks.get(key) ?? [];
    const id = Date.now().toString(36);
    const newTask: Task = { id, title, column: column as Task["column"], priority };
    tasks.push(newTask);
    projectTasks.set(key, tasks);
    return object({ id, title, column, priority, success: true });
  }
);

await server.listen();
```

---

## Recipe 5: Contact Form Server

A server that shows a contact form widget and processes submissions via a separate tool.

```typescript
import { MCPServer, widget, object, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "forms-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL,
});

// Shows the form widget
server.tool(
  {
    name: "show-contact-form",
    description: "Show an interactive contact form",
    schema: z.object({
      topic: z.string().optional().describe("Pre-filled topic"),
    }),
    widget: {
      name: "contact-form",
      invoking: "Loading form...",
      invoked: "Form ready",
    },
  },
  async ({ topic }) => {
    return widget({
      props: {
        topic: topic ?? "",
        departments: ["Sales", "Support", "Engineering", "Billing"],
      },
      message: "Contact form is ready for input.",
    });
  }
);

// Called from the widget via useCallTool
server.tool(
  {
    name: "submit-contact-form",
    description: "Submit a contact form",
    schema: z.object({
      name: z.string().min(1),
      email: z.string().email(),
      department: z.string(),
      message: z.string().min(10),
      priority: z.enum(["low", "medium", "high"]).default("medium"),
    }),
  },
  async ({ name, email, department, message, priority }) => {
    const ticketId = `TICKET-${Date.now().toString(36).toUpperCase()}`;
    // Send to your ticketing system here
    return object({
      ticketId,
      status: "submitted",
      message: `Thank you, ${name}. Your ${priority}-priority ticket ${ticketId} has been sent to ${department}.`,
    });
  }
);

await server.listen();
```

---

## Recipe 6: Raw HTML Widget Server

A server using `uiResource` to serve a raw HTML widget without a React component.

```typescript
import { MCPServer, type RawHtmlUIResource } from "mcp-use/server";

const server = new MCPServer({
  name: "html-widget-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL,
});

server.uiResource({
  type: "rawHtml",
  name: "welcome-card",
  title: "Welcome Message",
  description: "A welcome card with server information",
  htmlContent: `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body { margin: 0; padding: 20px; font-family: system-ui, sans-serif;
               background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
        .card { background: rgba(255,255,255,0.1); border-radius: 16px; padding: 30px;
                backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.18); }
        h1 { margin: 0 0 10px; font-size: 2em; }
        p { margin: 10px 0; opacity: 0.9; }
      </style>
    </head>
    <body>
      <div class="card">
        <h1>Welcome to MCP Apps</h1>
        <p>Your server is running and ready to serve interactive widgets.</p>
      </div>
    </body>
    </html>
  `,
  encoding: "text",
  size: ["600px", "300px"],
} satisfies RawHtmlUIResource);

await server.listen();
```

---

## Recipe 7: Remote DOM Widget Server

A server using `uiResource` with the `remoteDom` type for interactive polling.

```typescript
import { MCPServer, type RemoteDomUIResource } from "mcp-use/server";

const server = new MCPServer({
  name: "poll-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL,
});

server.uiResource({
  type: "remoteDom",
  name: "quick-poll",
  title: "Quick Poll",
  description: "Create instant polls with interactive voting",
  script: `
// Remote DOM only supports registered MCP-UI components: ui-stack, ui-text, ui-button, etc.
const container = document.createElement('ui-stack');
container.setAttribute('direction', 'column');
container.setAttribute('spacing', 'medium');
container.setAttribute('padding', 'large');

const title = document.createElement('ui-text');
title.setAttribute('size', 'xlarge');
title.setAttribute('weight', 'bold');
title.textContent = 'Quick Poll';
container.appendChild(title);

const question = document.createElement('ui-text');
question.setAttribute('size', 'large');
question.textContent = props.question || 'What is your preference?';
container.appendChild(question);

const buttonStack = document.createElement('ui-stack');
buttonStack.setAttribute('direction', 'row');
buttonStack.setAttribute('spacing', 'small');

const options = props.options || ['Option 1', 'Option 2', 'Option 3'];
options.forEach((option) => {
  const button = document.createElement('ui-button');
  button.setAttribute('label', option);
  button.setAttribute('variant', 'secondary');
  button.addEventListener('press', () => {
    window.parent.postMessage({ type: 'vote', option }, '*');
  });
  buttonStack.appendChild(button);
});
container.appendChild(buttonStack);
root.appendChild(container);
  `,
  framework: "react",
  encoding: "text",
  size: ["500px", "400px"],
  props: {
    question: { type: "string", description: "The poll question", default: "What do you prefer?" },
    options: { type: "array", description: "Poll options", default: ["React", "Vue", "Svelte"] },
  },
} satisfies RemoteDomUIResource);

await server.listen();
```

---

## Key Patterns

**widget() response** — always use `message` (not `output`) for the LLM-visible summary:
```typescript
return widget({
  props: { ... },           // → structuredContent (widget only)
  message: "Summary...",    // → content[0].text (LLM sees this)
  metadata: { ... },        // → _meta (optional extra data)
});
```

**Secondary tools for widgets** — keep tools that widgets call via `useCallTool` as separate `server.tool()` definitions without a `widget` property.

**baseUrl is required for production** — set it so widgets can call back to the server:
```typescript
const server = new MCPServer({
  name: "my-app",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});
```

**User identity** — use `ctx.client.user()?.subject` to key per-user data when building multi-user apps.

**CSP for external APIs** — declare all external domains in `widgetMetadata.metadata.csp`:
```typescript
metadata: {
  csp: {
    connectDomains: ["https://api.openweathermap.org"],
    resourceDomains: ["https://openweathermap.org"],
  },
}
```
