# List Changed Events

When the set of tools, resources, or prompts changes at runtime — added, removed, or schema-changed — emit a `list_changed` notification so connected clients re-fetch the lists.

## The three helpers

```typescript
await server.sendToolsListChanged();
await server.sendResourcesListChanged();
await server.sendPromptsListChanged();
```

These are convenience methods. Equivalent long-form calls:

```typescript
await server.sendNotification("notifications/tools/list_changed");
await server.sendNotification("notifications/resources/list_changed");
await server.sendNotification("notifications/prompts/list_changed");
```

| Method | When to call | Typical trigger |
|---|---|---|
| `server.sendToolsListChanged()` | Tool list changed | Adding/removing tools, swapping schemas |
| `server.sendResourcesListChanged()` | Resource list changed | Publishing new resource URIs, removing stale ones |
| `server.sendPromptsListChanged()` | Prompt list changed | Dynamic prompt templates added/removed |

## When NOT to emit

| Situation | Don't emit |
|---|---|
| Resource content changed (same URI) | Use `server.notifyResourceUpdated(uri)` instead |
| Tool's runtime behavior changed (same schema) | No notification — clients refetch only on `list_changed` |
| Initial registration during boot | No runtime change happened; clients fetch the initial list with `tools/list`, `resources/list`, or `prompts/list` |

The distinction matters:

| Change | API |
|---|---|
| Resource **content** changed (same URI) | `server.notifyResourceUpdated(uri)` (see `../06-resources/`) |
| Resource **list** changed (URI added/removed) | `server.sendResourcesListChanged()` |

## Dev-mode HMR

`mcp-use dev` already wires `list_changed` to file changes. When you edit a tool/resource/prompt file, the dev server reloads it and emits the appropriate `list_changed` for connected clients. You only call these helpers manually in production code that mutates the registry at runtime.

## Debounce / coalesce

Multiple registry changes in quick succession (e.g., a batch import) should coalesce into one notification:

```typescript
let pending = false;

async function scheduleToolsListChanged(server: MCPServer) {
  if (pending) return;
  pending = true;
  setTimeout(async () => {
    pending = false;
    await server.sendToolsListChanged();
  }, 200);
}
```

Call that helper from the code path that mutates your registry. mcp-use does not expose `tool:registered` / `tool:removed` event hooks.

## Anti-pattern: spamming list_changed

```typescript
// BAD — N events for N registrations
for (const tool of newTools) {
  server.tool(tool.definition, tool.handler);
  await server.sendToolsListChanged();
}

// GOOD — one event after the batch
for (const tool of newTools) {
  server.tool(tool.definition, tool.handler);
}
await server.sendToolsListChanged();
```

## Stateless caveat

Like all notifications, `list_changed` requires stateful transport. Stateless servers should never need this anyway — they don't dynamically register at runtime. See `06-when-notifications-fail.md`.

## Client behavior

On receiving `notifications/tools/list_changed`, a well-behaved client:

1. Re-fetches `tools/list`.
2. Updates its cached registry.
3. Re-renders any UI listing the tools.

There is no `params` payload — the notification is a pure signal.
