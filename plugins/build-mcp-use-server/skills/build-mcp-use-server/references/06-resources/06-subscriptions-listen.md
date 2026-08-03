# Resource Subscriptions & Listening (Stateless Model)

*Read this when you need clients to be notified when resource content changes, using v2's stateless per-request subscription model.*

## Overview

v2 subscriptions use a stateless per-request `subscriptions/listen` model, not session-backed subscribe handlers. Clients open a long-lived request to listen for resource change notifications; the server publishes updates via `server.notifyResourceUpdated(uri)`, and listeners receive them without session storage.

| When | Do |
|---|---|
| Resource content changed | Call `server.notifyResourceUpdated(uri)` |
| Resource set changed (add/remove) | Call `server.notifyResourcesChanged()` |
| Only list-changed updates, not resource content | Only call `server.notifyResourcesChanged()` |

---

## The Stateless Listen Pattern

Clients do **not** call the legacy per-resource `resources/subscribe` request to receive updates in v2 — on a modern (`2026-07-28`) negotiated connection that method is rejected outright (see "Legacy `resources/subscribe`/`resources/unsubscribe`" below). Instead, they send one `subscriptions/listen` request (protocol revision `2026-07-28`) carrying a `notifications` filter object, and keep that request's response stream open. The server has no session storage for subscriptions — delivery is scoped entirely to that one open request.

The filter (`SubscriptionFilter`) is opt-in per notification kind:

```typescript
{
  toolsListChanged?: boolean;
  promptsListChanged?: boolean;
  resourcesListChanged?: boolean;
  resourceSubscriptions?: string[]; // exact URIs to receive resources/updated for
}
```

- `notifications` is **required** on the request; an absent or invalid filter is rejected with `-32602`.
- `resource_updated` events are delivered **only** for URIs explicitly listed in `resourceSubscriptions` — listing a resource's URI there is the v2 replacement for calling `resources/subscribe` on it. A listener that omits a URI, or omits `resourceSubscriptions` entirely, never receives `notifyResourceUpdated()` calls for it, even though it still receives list-changed events it did opt into.
- The server narrows the requested filter against its own advertised capabilities (`resources.subscribe`, `resources.listChanged`, `tools.listChanged`, `prompts.listChanged` — mcp-use v2 servers advertise all of these as `true`) and echoes back the **honored** subset as the first message on the stream: a `notifications/subscriptions/acknowledged` notification.
- Each notification on the stream carries the listen request's ID under `_meta` so a client with multiple concurrent listeners can attribute events to the right one.
- A capacity guard rejects a new listen request with `-32603` once the server-wide open-subscription count hits its limit (`1024` by default, from the underlying SDK — not configured by mcp-use).

**Server-side workflow:**

1. Define a stable-URI resource with callback.
2. When state changes, call `server.notifyResourceUpdated(uri)` or `server.notifyResourcesChanged()`.
3. Active `subscriptions/listen` clients whose filter matches (and, for content updates, whose `resourceSubscriptions` includes that URI) receive the notification and re-read the resource via `resources/read`.

**Lifecycle:**

```
client                              server
  |  POST /mcp { subscriptions/listen } |  (open long-lived request)
  | ---------------------------------> |
  |                                   |
  |                                   |  (resource state changes)
  |  notification: resources/updated  |
  | <--------------------------------- |
  |                                   |
  |  resources/read(uri)              |
  | ---------------------------------> |
  |  (connection drops)               |
  |  X                                |  (listen request ends)
```

---

## Legacy `resources/subscribe`/`resources/unsubscribe`

mcp-use's server capabilities still advertise `resources: { subscribe: true }`, and the underlying `@modelcontextprotocol/server` SDK still ships `resources/subscribe`/`resources/unsubscribe` request schemas. Despite that, a client that sends `resources/subscribe` against a v2 mcp-use server does **not** get its request wired to `resourceSubscriptions`, and does not get a silent no-op success — it is **rejected with `-32601 Method Not Found`**, for two independent reasons that both hold:

1. **Modern (`2026-07-28`) negotiated connections** — the era this skill targets — have their own request-method registry, and `resources/subscribe`/`resources/unsubscribe` are **not members of it** (only `subscriptions/listen` is). The dispatcher checks method-registry membership before it even looks for a handler; a spec method absent from the negotiated era's registry is answered `-32601` at that gate, before params or capabilities are examined.
2. **Even on a legacy-era-negotiated connection** (mcp-use's `createMcpMount()` defaults `legacy: "stateless"`, so 2025-era requests are still served) — the shared `McpServer` class's resource setup (`setResourceRequestHandlers()`) only ever registers handlers for `resources/list`, `resources/templates/list`, and `resources/read`. It never calls `setRequestHandler("resources/subscribe", ...)` or `"resources/unsubscribe"`, in the SDK or in mcp-use's own source. With no handler installed, the dispatcher's fallback-handler lookup also comes up empty and returns the same `-32601`.

The `resources.subscribe: true` capability bit is not a promise that `resources/subscribe` works — the SDK's own internal comment on this is explicit: *"the serving entries serve `subscriptions/listen` themselves, so the `listChanged` and `resources.subscribe` capability bits are advertised as-is: a modern-era client uses them to decide which notification types to request on its listen filter."* In other words, `resources.subscribe: true` tells a modern client "resource-level change notifications exist here — ask for them via `resourceSubscriptions` in your `subscriptions/listen` filter," not "the legacy request method is implemented." Do not build client or server logic that sends or expects to handle `resources/subscribe`/`resources/unsubscribe` against a v2 mcp-use server; use `subscriptions/listen` with `resourceSubscriptions` exclusively.

---

## Notify on Content Change

When a resource's **content** at a stable URI changes, call `server.notifyResourceUpdated(uri)`:

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "app", version: "1.0.0" });

let appSettings = { theme: "light", language: "en" };

server.resource(
  {
    name: "app_settings",
    uri: "settings://app",
    description: "Current application settings",
  },
  async (uri, ctx) => ({
    contents: [{
      uri: uri.href,
      mimeType: "application/json",
      text: JSON.stringify(appSettings),
    }],
  })
);

server.tool(
  {
    name: "update_settings",
    description: "Update settings",
    inputSchema: z.object({
      theme: z.enum(["light", "dark"]).optional(),
      language: z.string().optional(),
    }),
  },
  async ({ theme, language }, ctx) => {
    if (theme) appSettings.theme = theme;
    if (language) appSettings.language = language;

    // Notify active listeners; they will re-read the resource
    await server.notifyResourceUpdated("settings://app");

    return {
      content: [{ type: "text", text: "Settings updated" }],
    };
  }
);

await server.listen(3000);
```

---

## Notify After External Resource Changes

Resource and template registration is frozen after startup. Register a template up front, store dynamic records externally, then notify listeners when a concrete URI becomes readable or changes:

```typescript
const reports = new Map<string, string>();

server.resourceTemplate(
  {
    name: "report",
    uriTemplate: "reports://{reportId}",
    title: "Report",
    mimeType: "text/plain",
  },
  async (uri, { reportId }) => {
    const id = Array.isArray(reportId) ? reportId[0] : reportId;
    const text = reports.get(id);
    if (text === undefined) throw new Error(`Report ${id} not found`);
    return {
      contents: [{ uri: uri.href, mimeType: "text/plain", text }],
    };
  },
);

server.tool(
  {
    name: "add_report",
    description: "Create a new report",
    inputSchema: z.object({ title: z.string() }),
  },
  async ({ title }) => {
    const id = crypto.randomUUID();
    const uri = `reports://${id}`;
    reports.set(id, `Report: ${title}`);

    // Reach only clients actively listening for this exact URI.
    await server.notifyResourceUpdated(uri);

    return {
      content: [{ type: "text", text: `Created ${uri}` }],
    };
  },
);
```

Call `notifyResourcesChanged()` only when the discoverable list returned by `resources/list` changes — for example, when `mcp:resources/list` middleware filters an up-front registry using external state. Never call `server.resource()` or `server.resourceTemplate()` after the server has mounted.

---

## Pattern: Dynamic Resource Templates

Combine `resourceTemplate` with list-change and content-change notifications:

```typescript
const activeFiles = new Set<string>();

server.resourceTemplate(
  {
    name: "file",
    uriTemplate: "file://{path}",
    description: "Open file by path",
  },
  async (uri, { path }, ctx) => {
    if (!activeFiles.has(path)) {
      return {
        isError: true,
        content: [{ type: "text", text: `File not open: ${path}` }],
      };
    }
    const contents = await readFile(path, "utf-8");
    return {
      contents: [{
        uri: uri.href,
        mimeType: "text/plain",
        text: contents,
      }],
    };
  }
);

// Tool: open a file
server.tool(
  {
    name: "open_file",
    inputSchema: z.object({ path: z.string() }),
  },
  async ({ path }, ctx) => {
    activeFiles.add(path);
    await server.notifyResourcesChanged(); // Set changed, clients re-list
    return { content: [{ type: "text", text: `Opened ${path}` }] };
  }
);

// Tool: edit a file
server.tool(
  {
    name: "edit_file",
    inputSchema: z.object({ path: z.string(), content: z.string() }),
  },
  async ({ path, content }, ctx) => {
    if (!activeFiles.has(path)) {
      return {
        isError: true,
        content: [{ type: "text", text: `File not open: ${path}` }],
      };
    }
    await writeFile(path, content);
    await server.notifyResourceUpdated(`file://${path}`); // Content changed
    return { content: [{ type: "text", text: `Saved ${path}` }] };
  }
);
```

---

## Limitations & Design Notes

**Subscriptions are not durable:**
- No queue, no delivery guarantees, no replay.
- Clients must re-read the resource after notification.
- A client that disconnects before receiving the notification loses it.

**Use subscriptions when:**
- Clients are actively connected and listening.
- Missing an update is acceptable (client can re-read).
- The resource URI is stable (or templated with known parameters).

**Do not use subscriptions for:**
- Audit logs or durable event queues — use a database.
- Critical job notifications — use a message broker.
- Fire-and-forget updates — clients won't see offline updates.

**Stateless guarantees:**
- No in-server subscription registry required.
- Every instance can independently call `notifyResourceUpdated()`.
- Listeners receive notifications only while actively connected.
- mcp-use does not implement the listen router itself — it declares `resources: { listChanged: true, subscribe: true }`, `tools: { listChanged: true }`, and `prompts: { listChanged: true }` in its server capabilities and delegates `subscriptions/listen` handling entirely to the underlying `@modelcontextprotocol/server` request handler that `server.listen()`/`server.fetch()` mount.

---

## Combining with Notifications Cluster

For progress or custom notifications during a tool execution, see `references/14-notifications/02-ctx-sendnotification.md`. For list-change subscriptions and resource updates working together, see `references/14-notifications/05-subscriptions-delivery.md`.
