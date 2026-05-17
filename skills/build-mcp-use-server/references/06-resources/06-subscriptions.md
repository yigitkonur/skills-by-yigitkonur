# Resource Subscriptions

Subscriptions push resource-change notifications to clients in real time. This file is the canonical home for subscription wiring — `../14-notifications/` links here rather than duplicating.

## Two notification methods

| Method | Triggers | Use when |
|---|---|---|
| `server.notifyResourceUpdated(uri)` | `notifications/resources/updated` | The **content** of a known URI changed |
| `server.sendResourcesListChanged()` | `notifications/resources/list_changed` | A resource or template was **added or removed** |

Both depend on active client sessions. `sendResourcesListChanged()` is documented as stateful-only; `notifyResourceUpdated()` only sends to sessions that subscribed to the exact URI.

## `notifyResourceUpdated` — single URI

```typescript
// Update database
await db.users.update({ where: { id }, data });

// Notify subscribed clients
await server.notifyResourceUpdated(`users://${id}`);
```

Clients that subscribed to `users://${id}` re-fetch via `resources/read`. Clients that did not subscribe ignore the message.

## `sendResourcesListChanged` — registry change

```typescript
// After dynamically adding a new resource
server.resource(
  { name: "new-data", uri: "data://new" },
  async () => text("New content"),
);
await server.sendResourcesListChanged();
```

Clients re-issue `resources/list` or the `listResourceTemplates()` client helper as appropriate and refresh their picker UIs.

## Subscription lifecycle

```
client                           server
  |  resources/subscribe(uri)     |
  | ----------------------------> |
  |                               |  (server records subscription on transport)
  |  notifications/resources/updated
  | <---------------------------- |
  |  resources/read(uri)          |
  | ----------------------------> |
  |  resources/unsubscribe(uri)   |
  | ----------------------------> |
```

The server library handles subscribe/unsubscribe routing internally — you do not write subscription bookkeeping yourself. Just call `notifyResourceUpdated(uri)` whenever the underlying data changes; the transport delivers to interested clients.

## Pattern: dynamic resource set

```typescript
const activeFiles = new Set<string>();

server.resourceTemplate(
  { name: "file", uriTemplate: "file://{path}" },
  async (uri, { path }) => {
    if (!activeFiles.has(path)) throw new Error("File not open");
    return text(await readFile(path, "utf-8"));
  },
);

server.tool(
  { name: "open-file", schema: z.object({ path: z.string() }) },
  async ({ path }) => {
    activeFiles.add(path);
    await server.sendResourcesListChanged(); // tell clients to re-list
    return text(`Opened ${path}`);
  },
);

server.tool(
  { name: "edit-file", schema: z.object({ path: z.string(), content: z.string() }) },
  async ({ path, content }) => {
    await writeFile(path, content);
    await server.notifyResourceUpdated(`file://${path}`); // tell subscribers to re-read
    return text(`Saved ${path}`);
  },
);
```

## When to use which

| Situation | Method |
|---|---|
| One resource's content changed | `notifyResourceUpdated(uri)` |
| Resource was added | `sendResourcesListChanged()` |
| Resource was removed | `sendResourcesListChanged()` |
| Many known resource contents changed | Call `notifyResourceUpdated(uri)` for each changed subscribed URI |
| Both registry and contents changed | Both, in that order |

## Active sessions only

Subscriptions require active session tracking:

| Session mode | Subscriptions |
|---|---|
| Stateful sessions | yes |
| Stateless HTTP | no active session tracking |

For transport selection, see `../09-transports/`.

## Pairing with roots

When the server's resource set depends on client-side roots, combine `onRootsChanged` with `sendResourcesListChanged()`:

```typescript
server.onRootsChanged(async (roots) => {
  // recompute the set of resources we expose based on client roots
  await rebuildResourceIndex(roots);
  await server.sendResourcesListChanged();
});
```

See `canonical-anchor.md` for the reference implementation.
