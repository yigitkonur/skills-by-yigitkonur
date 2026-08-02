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

Clients do **not** use `resources/subscribe` in v2. Instead, they open an active `subscriptions/listen` request for notification types they care about. The v2 server has no session storage for subscriptions — it delivers notifications only to active listeners.

**Server-side workflow:**

1. Define a stable-URI resource with callback.
2. When state changes, call `server.notifyResourceUpdated(uri)` or `server.notifyResourcesChanged()`.
3. Active `subscriptions/listen` clients receive the notification and re-read the resource via `resources/read`.

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

## Notify on Registry Change

When the **resource set itself changes** (a resource added or removed), call `server.notifyResourcesChanged()`:

```typescript
server.tool(
  {
    name: "add_report",
    description: "Create a new report",
    inputSchema: z.object({ title: z.string() }),
  },
  async ({ title }, ctx) => {
    // Register a new dynamic resource
    server.resource(
      {
        name: `report_${Date.now()}`,
        uri: `reports://report-${Date.now()}`,
        title,
      },
      async (uri, ctx) => ({
        contents: [{
          uri: uri.href,
          mimeType: "text/plain",
          text: `Report: ${title}`,
        }],
      })
    );

    // Tell listening clients the resource set changed
    await server.notifyResourcesChanged();

    return {
      content: [{ type: "text", text: `Report "${title}" created` }],
    };
  }
);
```

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

---

## Combining with Notifications Cluster

For progress or custom notifications during a tool execution, see `references/14-notifications/02-ctx-sendnotification.md`. For list-change subscriptions and resource updates working together, see `references/14-notifications/05-subscriptions-delivery.md`.
