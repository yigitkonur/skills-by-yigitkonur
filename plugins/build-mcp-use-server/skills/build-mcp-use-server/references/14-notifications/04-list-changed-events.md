# List-Changed Events

*Read this when signaling that tools, prompts, or resources changed between requests.*

Send server-level notifications when a discoverable or subscribed surface changes. These methods live on `server`, not `ctx`; call them from a tool callback, custom route, background event, or other code that changes external state.

## Server Methods

```typescript
await server.notifyToolsChanged(): Promise<void>
await server.notifyPromptsChanged(): Promise<void>
await server.notifyResourcesChanged(): Promise<void>
await server.notifyResourceUpdated(uri: string): Promise<void>
```

## Usage

```typescript
// All tools are registered up front, before the server starts. Registration
// methods throw once the server has handled its first request or bound a
// listener — there is no "register a new tool from inside a request handler"
// pattern in v2.
server.tool(
  { name: "import_pdf", description: "Import PDF documents" },
  async (params, ctx) => ({ content: [{ type: "text", text: "OK" }] })
);
server.tool(
  { name: "import_csv", description: "Import CSV documents" },
  async (params, ctx) => ({ content: [{ type: "text", text: "OK" }] })
);

// To change which tools a given client sees, filter mcp:tools/list per
// request instead of registering/unregistering tools at runtime.
const enabledFormats = new Set(["pdf"]);

server.use("mcp:tools/list", async (_ctx, next) => {
  const tools = await next();
  return tools.filter(
    (tool) => !tool.name.startsWith("import_") ||
      enabledFormats.has(tool.name.replace("import_", ""))
  );
});

server.post("/api/enable-importer", async (c) => {
  const { format } = await c.req.json();
  enabledFormats.add(format);

  // Tell listening clients that the discoverable tool set changed for them.
  await server.notifyToolsChanged();

  return c.json({ ok: true });
});

// Resource updated
server.post("/api/config/update", async (c) => {
  const { newValue } = await c.req.json();
  state.config = newValue;

  // Notify clients with active subscriptions
  await server.notifyResourceUpdated("config://app");

  return c.json({ ok: true });
});
```

## Key points

- **Server-level only.** These methods are on `server`, not `ctx`. They may be called from request callbacks/routes or external/background code; delivery still reaches only clients with an active matching listener.
- **Registration is up-front only.** `server.tool()`, `server.resource()`, and `server.prompt()` throw if called after the server has started handling requests (`listen()` bound, or the first `server.fetch()` call mounted). Register every tool/resource/prompt at module scope; vary what a given client sees by filtering `mcp:tools/list` / `mcp:resources/list` / `mcp:prompts/list` middleware, and call `notify*Changed()` when the filtered result would change.
- **Stateless delivery.** Notifications are sent only to clients with an active `subscriptions/listen` request for that type. If no client is listening, the notification is lost.
- **Client must re-sync.** After receiving `resourceUpdated(uri)`, clients re-read that resource. They do not cache; each notification triggers a new fetch.
- **No backlog.** Clients connecting after a notification fires do not receive past events. They query normally and get the current state.

## When to use each

| Method | Scenario |
|--------|----------|
| `notifyToolsChanged()` | The tool list visible to a listener changes because external state or `mcp:tools/list` filtering changed |
| `notifyPromptsChanged()` | The prompt list visible to a listener changes because external state or filtering changed |
| `notifyResourcesChanged()` | The resource list visible to a listener changes (not merely one resource's content) |
| `notifyResourceUpdated(uri)` | Specific resource content changed; clients re-read this URI |

See also: `references/06-resources/06-subscriptions-listen.md` for the client-side subscription workflow.
