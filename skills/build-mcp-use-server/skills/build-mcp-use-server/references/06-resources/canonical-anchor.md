# Example Reference: `mcp-use/mcp-resource-watcher`

The `mcp-resource-watcher` repo is the official example repo for resources, subscriptions, roots, and a config widget. In the current `main` branch, the load-bearing server code is root-level `index.ts`.

**Repo:** https://github.com/mcp-use/mcp-resource-watcher

**Source note:** [README](https://github.com/mcp-use/mcp-resource-watcher/blob/main/README.md) advertises resource templates and change notifications, but current [`index.ts`](https://github.com/mcp-use/mcp-resource-watcher/blob/main/index.ts) demonstrates only `server.resource()` plus `server.notifyResourceUpdated()` for resources; use package docs for `server.resourceTemplate()` and `server.sendResourcesListChanged()`.

## What it demonstrates

- Static resource registration with `server.resource()`
- Resource content update notification with `server.notifyResourceUpdated("config://settings")`
- Custom notification from a tool through `ctx.sendNotification(...)`
- Roots hooks with `server.onRootsChanged(...)` and `server.listRoots(ctx.session?.sessionId)`
- Widget-backed tools that return `widget({ props, output })`

## Load-bearing files

| File | What to read it for |
|---|---|
| `index.ts` | `MCPServer` setup, `server.resource()`, tools, notifications, roots |
| `resources/config-panel/` | Widget implementation consumed by `show-config` |
| `resources/styles.css` | Widget styling |
| `package.json` | `mcp-use` version, scripts, ESM config |

## When to consult it

- Wiring `onRootsChanged()` for the first time
- Checking how a tool updates a static resource and calls `notifyResourceUpdated()`
- Seeing how `listRoots(ctx.session?.sessionId)` is called from a tool handler

## Cross-cluster references

- `06-subscriptions.md` — subscription lifecycle and notification rules
- `03-resource-templates.md` — `uriTemplate` and parameter handlers
- `../14-notifications/` — links back here for resource-update notifications
- `../17-advanced/` — `onRootsChanged` and roots-aware servers
