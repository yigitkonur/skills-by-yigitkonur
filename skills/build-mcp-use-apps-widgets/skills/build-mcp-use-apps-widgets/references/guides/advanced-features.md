# Advanced Features

Dual-protocol widgets, host context, display modes, state management patterns, and how mcp-use compares to alternative MCP implementations.

---

## 1. Dual-Protocol Widget Support

mcp-use automatically generates metadata for both protocols from a single widget definition:

- **MCP Apps Extension (SEP-1865)** — used by Claude, Goose, and MCP Apps-compatible clients
- **OpenAI Apps SDK** — used by ChatGPT

No code changes are required. The server detects the connected client and serves the appropriate protocol format.

### How it Works

When you define a widget with `metadata` (camelCase), the server:
1. Serves `text/html;profile=mcp-app` with `_meta.ui.*` namespace for MCP Apps clients.
2. Serves `text/html+skybridge` with `openai/*` prefixed keys (snake_case CSP) for ChatGPT.

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Interactive weather card",
  props: propSchema,
  // Using `metadata` (not appsSdkMetadata) enables dual-protocol automatically
  metadata: {
    csp: {
      connectDomains: ["https://api.weather.com"],
      resourceDomains: ["https://cdn.weather.com"],
      scriptDirectives: ["'unsafe-eval'"], // Required for React runtime
    },
    prefersBorder: true,
    autoResize: true,                 // MCP Apps clients
    widgetDescription: "Weather card", // ChatGPT-specific display description
  },
};
```

### Protocol Adapters (Advanced)

Usually handled automatically, but accessible when needed:

```typescript
import { McpAppsAdapter, AppsSdkAdapter } from "mcp-use/server";

const mcpAppsAdapter = new McpAppsAdapter();
const appsSdkAdapter = new AppsSdkAdapter();

const mcpMeta = mcpAppsAdapter.transformMetadata(unifiedMeta);
const chatgptMeta = appsSdkAdapter.transformMetadata(unifiedMeta);
```

### Metadata Mapping

| Widget metadata key | MCP Apps (_meta.ui.*) | ChatGPT (openai/*) |
|---|---|---|
| `csp.connectDomains` | `connectDomains` (camelCase) | `connect_domains` (snake_case) |
| `csp.resourceDomains` | `resourceDomains` | `resource_domains` |
| `csp.frameDomains` | `frameDomains` | `frame_domains` |
| `csp.redirectDomains` | `redirectDomains` | `redirect_domains` |
| `prefersBorder` | `prefersBorder` | `openai/widgetPrefersBorder` |
| `widgetDescription` | — | `openai/widgetDescription` |

---

## 2. Widget Tool Response Structure

The `widget()` helper maps to different transport fields:

```typescript
return widget({
  props: { city, temperature, conditions },     // → structuredContent (model-safe widget props)
  message: `Weather in ${city}: ${conditions}`, // → content[0].text (LLM sees this)
  metadata: { totalCount: 5, cursor: "abc" },   // → _meta (private/client-only widget data)
});
```

- **`props`** → available in `useWidget().props` — model-safe data the widget renders.
- **`message`** → the human-readable summary passed to the LLM as `content`.
- **`metadata`** → private, bulky, or UI-only data accessible via `useWidget().metadata`.

---

## 3. Host Context in Widgets

`useWidget()` exposes full host context from the MCP Apps Extension:

```typescript
function WidgetContent() {
  const {
    props,
    isPending,
    isStreaming,
    partialToolInput,   // Partial args while LLM is streaming
    theme,              // "light" | "dark"
    locale,             // BCP-47, e.g. "en-US"
    timeZone,           // IANA timezone, e.g. "America/New_York"
    maxWidth,           // Available width in the host (MCP Apps only)
    maxHeight,          // Available height
    userAgent,          // { device: { type }, capabilities: { touch } }
    safeArea,           // { insets: { top, right, bottom, left } }
    displayMode,        // "inline" | "pip" | "fullscreen"
    requestDisplayMode, // (mode) => Promise<void>
    sendFollowUpMessage,// (msg: string) => void
    state,              // Widget-owned UI state
    setState,           // (newState) => Promise<void>
  } = useWidget<Props, Output, Meta, State>();

  const isDark = theme === "dark";
  const platform = userAgent?.device?.type ?? "unknown";
  const hasTouch = userAgent?.capabilities?.touch ?? false;
  const { top = 0, bottom = 0 } = safeArea?.insets ?? {};
  // ...
}
```

> **Note:** `maxWidth`, `maxHeight`, `userAgent`, and `safeArea` are provided by MCP Apps clients. ChatGPT provides `theme`, `locale`, and some others via the Apps SDK.

---

## 4. Display Modes

Widgets can request three display modes:

```typescript
const { displayMode, requestDisplayMode } = useWidget();

// Request fullscreen
await requestDisplayMode("fullscreen");

// Request picture-in-picture
await requestDisplayMode("pip");

// Return to inline
await requestDisplayMode("inline");
```

> `requestDisplayMode` is advisory — the host may decline. Always read back `displayMode` to confirm the granted mode.

**Pattern:** show a fullscreen button only when not already fullscreen:

```tsx
{displayMode !== "fullscreen" && (
  <button onClick={() => requestDisplayMode("fullscreen")}>
    Expand
  </button>
)}
{displayMode === "fullscreen" && (
  <button onClick={() => requestDisplayMode("inline")}>
    Close
  </button>
)}
```

---

## 5. Follow-Up Messages

Send a new user-side message from a widget to trigger another LLM turn:

```typescript
const { sendFollowUpMessage } = useWidget();

// Plain string
sendFollowUpMessage("What are the key trends in this data?");

// Structured message blocks
sendFollowUpMessage([
  { type: "text", text: "Compare this with the previous period." },
]);
```

Use this for "Ask AI" buttons that pre-fill contextual questions based on what the widget displays.

---

## 6. Widget State Management

| State type | Where it lives | Lifetime | Use for |
|---|---|---|---|
| **UI state** | Widget instance via `setState` | Per message (session) | Filters, selections, toggles |
| **Business data** | MCP server / backend | Long-lived | Search results, documents |
| **Cross-session** | Backend via tool calls | Across conversations | User preferences, workspace settings |

### UI State (Widget-Owned)

```typescript
interface MyState {
  selectedTab: string;
  favorites: string[];
}

const { state, setState } = useWidget<Props, Output, Meta, MyState>();

// Read
const tab = state?.selectedTab ?? "overview";

// Update
await setState({ selectedTab: "analytics", favorites: state?.favorites ?? [] });
```

`setState` persists via `ui/update-model-context` (MCP Apps) or `window.openai.setWidgetState` (ChatGPT). Do **not** use `localStorage` — it is scoped to the iframe origin, not the conversation.

### Cross-Session State (Backend-Owned)

```typescript
// In widget
const { callTool: savePrefs } = useCallTool("save-user-preferences");
await savePrefs({ theme: "dark", defaultView: "list" });
```

```typescript
// In server
server.tool(
  { name: "save-user-preferences", schema: z.object({ theme: z.string(), defaultView: z.string() }) },
  async ({ theme, defaultView }, ctx) => {
    const userId = ctx.client.user()?.subject;
    if (userId) await db.savePrefs(userId, { theme, defaultView });
    return text("Preferences saved.");
  }
);
```

---

## 7. exposeAsTool

Widgets in `resources/` can be exposed directly as MCP tools without a custom tool handler:

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Greeting card widget",
  props: z.object({ name: z.string(), greeting: z.string() }),
  exposeAsTool: true, // Automatically creates a tool named after the widget
  metadata: { prefersBorder: true },
};
```

When `exposeAsTool: true`, the MCP server auto-generates a tool with the widget's folder name, making it directly callable by clients without a corresponding `server.tool()` definition.

Set `exposeAsTool: false` (default) when the widget is driven by a custom tool handler.

---

## 8. Server Composition / Proxy

`server.proxy()` combines multiple upstream MCP servers into a single aggregator endpoint:

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({ name: "Gateway", version: "1.0.0" });

await server.proxy({
  database: {
    command: "tsx",
    args: ["./db-server.ts"],
  },
  weather: {
    command: "uv",
    args: ["run", "weather_server.py"],
  },
  remote: {
    url: "https://api.example.com/mcp",
  },
});

server.tool(
  { name: "aggregator_status", description: "Check aggregator status" },
  async () => text("All systems operational")
);

await server.listen(3000);
```

Child tools are namespaced: `database_query`, `weather_get_forecast`, etc.

**How proxying works:**
1. Introspects the child server (`listTools`, `listResources`, `listPrompts`).
2. Translates raw JSON Schemas into runtime Zod schemas for validation.
3. Namespaces component names to prevent collisions.
4. Relays tool calls to the child server.
5. Synchronizes `list_changed` notifications to all aggregator clients.
6. Transparently routes sampling, elicitation, and progress requests back to the correct user's client.

---

## 9. Autocomplete (completable)

The `completable()` helper enables argument completion suggestions for prompts and resource templates:

```typescript
import { MCPServer, completable } from "mcp-use/server";
import { z } from "zod";

server.prompt(
  {
    name: "code-review",
    schema: z.object({
      language: completable(z.string(), ["python", "javascript", "typescript", "java"]),
      code: z.string(),
    }),
  },
  async ({ language, code }) => ({
    messages: [{ role: "system", content: `Review this ${language} code: ${code}` }],
  })
);
```

**Dynamic completion (context-aware):**

```typescript
projectId: completable(z.string(), async (value, context) => {
  const userId = context?.arguments?.userId;
  const projects = await fetchUserProjects(userId);
  return projects.filter((p) => p.id.startsWith(value)).map((p) => p.id);
}),
```

---

## 10. User Context Extraction

`ctx.client.user()` returns per-invocation caller metadata from `params._meta`. Returns `undefined` for clients that do not send this metadata (Inspector, Claude Desktop, CLI, etc.).

> **Warning:** This data is client-reported and unverified. Do not use it for access control. Use OAuth authentication with `ctx.auth` for verified identity.

```typescript
server.tool({ name: "personalise", schema: z.object({}) }, async (_p, ctx) => {
  const caller = ctx.client.user();
  if (!caller) return text("Hello! (no caller context available)");

  const city = caller.location?.city ?? "there";
  const greeting = caller.locale?.startsWith("it") ? "Ciao" : "Hello";
  return text(`${greeting} from ${city}!`);
});
```

**`UserContext` fields:**

| Field | Type | Description |
|---|---|---|
| `subject` | `string` | Stable opaque user identifier (same across conversations) |
| `conversationId` | `string` | Current chat thread ID (changes per chat) |
| `locale` | `string` | BCP-47 locale, e.g. `"it-IT"` |
| `location` | `object` | `{ city, region, country, timezone, latitude, longitude }` |
| `userAgent` | `string` | Browser / host user-agent string |
| `timezoneOffsetMinutes` | `number` | UTC offset in minutes |

**ChatGPT multi-tenant model:** ChatGPT shares a single MCP session across all users. Use `ctx.client.user()?.subject` to identify individual users and `conversationId` for chat threads.

---

## 11. Client Capability Checking

```typescript
server.tool({ name: "smart-tool", schema: z.object({}) }, async (_p, ctx) => {
  const { name, version } = ctx.client.info();
  const hasSampling    = ctx.client.can("sampling");
  const hasElicitation = ctx.client.can("elicitation");
  const isAppsClient   = ctx.client.supportsApps();
  const uiExt          = ctx.client.extension("io.modelcontextprotocol/ui");

  if (isAppsClient) {
    return widget({ props: { message: "Widget supported!" }, message: "Widget rendered." });
  } else {
    return text(`Hello from ${name} v${version} — no widget support.`);
  }
});
```

| Method | Returns | Description |
|---|---|---|
| `info()` | `{ name, version }` | Client name and version from initialize handshake |
| `can(capability)` | `boolean` | Check for `"sampling"`, `"elicitation"`, `"roots"`, etc. |
| `supportsApps()` | `boolean` | Convenience check for MCP Apps support (SEP-1865) |
| `extension(id)` | `object \| undefined` | Access raw MCP extension data by ID |
| `user()` | `UserContext \| undefined` | Per-invocation caller metadata |
| `capabilities()` | `Record<string, any>` | Full raw capabilities object |

---

## 12. Comparison with Other MCP Implementations

| Feature | mcp-use | Official SDK | FastMCP | tmcp | xmcp |
|---------|---------|-------------|---------|------|------|
| Language | TypeScript | TypeScript | Python | JavaScript | TypeScript |
| MCP Apps / Widgets | ✅ | ❌ | ❌ | ❌ | ❌ |
| Dual-Protocol (ChatGPT + MCP Apps) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Stateful + Stateless | ✅ | ✅ | ✅ | Stateful only | Stateless only |
| Registration Replay | ✅ | ❌ | ❌ | ❌ | ❌ |
| Auto Runtime Detection | ✅ | ❌ | ❌ | ❌ | ❌ |
| Redis Sessions | ✅ | ❌ | ✅ | ✅ | N/A |
| Server Composition (Proxy) | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## See Also

- **Widgets, MCP Apps & React Hooks** → `widgets-and-ui.md`
- **Streaming Props Preview** → `streaming-and-preview.md`
- **Elicitation & Sampling** → `elicitation-and-sampling.md`
- **Notifications & Subscriptions** → `notifications-and-subscriptions.md`
- **Middleware & Server Configuration** → `server-configuration.md`
