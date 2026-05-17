# Canonical: `mcp-use/mcp-resource-watcher`

**URL:** https://github.com/mcp-use/mcp-resource-watcher

The resources + subscriptions reference. Demonstrates how server state becomes an observable MCP resource, how mutations push `notifications/resources/updated`, and how `server.onRootsChanged` and `server.listRoots` drive the workspace-roots feature.

## Load-bearing files

| File | What to read it for |
|---|---|
| `index.ts` (`server.resource(...)` block) | Defining a subscribable resource (`config://settings`) |
| `index.ts` (`update-config` tool calling `server.notifyResourceUpdated(uri)`) | The push side of resource subscriptions |
| `index.ts` (`toggle-feature` tool calling `server.sendToolsListChanged()`) | Re-announcing the tool list after server-side change |
| `index.ts` (`server.onRootsChanged(handler)`) | Listening for client roots changes |
| `index.ts` (`list-roots` tool calling `server.listRoots(sessionId)`) | Server → client `roots/list` request |
| `resources/config-panel/widget.tsx` | UI that mirrors and mutates the resource via `useCallTool` |

## Patterns demonstrated

| Pattern | Where |
|---|---|
| `server.resource({uri, ...}, async () => object(state))` | `config://settings` |
| `server.notifyResourceUpdated(uri)` — push to subscribed clients | `update-config` |
| `await ctx.sendNotification("custom/...", payload)` for non-resource clients | `update-config` |
| `server.sendToolsListChanged()` — invalidate the tool cache on the client | `toggle-feature` |
| `server.onRootsChanged(handler)` — react to workspace changes | top of `index.ts` |
| `server.listRoots(sessionId)` — pull workspace roots on demand | `list-roots` |

## Clusters this complements

- `../06-resources/` — resource registration and templates
- `../14-notifications/` — `notifyResourceUpdated`, `sendToolsListChanged`, `sendNotification`
- `../16-client-introspection/` — workspace roots
- `../30-workflows/13-resource-watcher-with-subscriptions.md` — workflow derived from this repo

## When to study this repo

- You have mutable server state and want clients to know when it changes without polling.
- You added or removed tools at runtime and need clients to refresh `tools/list`.
- You want to consume client-side workspace roots from the server.
- You are reasoning about whether a piece of state should be a resource or a tool result.

## Local run

```bash
gh repo clone mcp-use/mcp-resource-watcher
cd mcp-resource-watcher
npm install
npm run dev
```
