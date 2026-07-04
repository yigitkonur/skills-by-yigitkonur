# Workflow: Resource Watcher with Subscriptions

**Goal:** expose mutable server state as an MCP resource, push `notifications/resources/updated` to subscribed clients whenever the state changes, and surface the same state in a config-panel widget. Modeled on `mcp-use/mcp-resource-watcher`.

## Prerequisites

- mcp-use 1.26.0 or newer.

## Layout

```
resource-watcher/
├── package.json
├── index.ts
└── resources/
    └── config-panel/
        └── widget.tsx
```

## `index.ts`

```typescript
import { MCPServer, text, widget, object } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "resource-watcher",
  version: "1.0.0",
  description: "Resources, subscriptions, and roots showcase",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

// In-process state — replace with a real store in production.
let config: Record<string, string> = {
  theme: "light",
  language: "en",
  notifications: "on",
};

let featureFlags: Record<string, boolean> = {
  darkMode: true,
  betaFeatures: false,
};

// ── Resource: subscribable JSON document ────────────────────────────────────

server.resource(
  {
    name: "settings",
    uri: "config://settings",
    title: "Application Settings",
    description: "Current application configuration",
    mimeType: "application/json",
  },
  async () => object(config)
);

// ── Roots: client workspace roots, observable from server ───────────────────

server.onRootsChanged(async (roots) => {
  console.log("client roots changed:", JSON.stringify(roots));
});

// ── Tool: show the panel widget ─────────────────────────────────────────────

server.tool(
  {
    name: "show-config",
    description: "Open the configuration panel widget",
    schema: z.object({}),
    widget: { name: "config-panel", invoking: "Loading…", invoked: "Ready" },
  },
  async () => {
    return widget({
      props: { config, featureFlags },
      output: text("Config loaded"),
    });
  }
);

// ── Tool: mutate config — pushes a resource-update notification ────────────

server.tool(
  {
    name: "update-config",
    description: "Update a config key. Notifies all subscribers of the resource.",
    schema: z.object({
      key: z.string(),
      value: z.string(),
    }),
    widget: { name: "config-panel", invoking: "Updating…", invoked: "Updated" },
  },
  async ({ key, value }, ctx) => {
    config = { ...config, [key]: value };

    // (1) Tell subscribers the resource has changed — this triggers
    //     resources/read on the client without an explicit poll.
    await server.notifyResourceUpdated("config://settings");

    // (2) Optional: arbitrary custom notification for non-resource clients.
    await ctx.sendNotification("custom/config-changed", { key, value });

    return widget({
      props: { config, featureFlags },
      output: text(`Updated ${key} → ${value}`),
    });
  }
);

// ── Tool: mutate the tool list itself ──────────────────────────────────────

server.tool(
  {
    name: "toggle-feature",
    description: "Toggle a feature flag and announce that the tool list changed",
    schema: z.object({
      feature: z.string(),
      enabled: z.boolean(),
    }),
  },
  async ({ feature, enabled }) => {
    featureFlags = { ...featureFlags, [feature]: enabled };

    // If toggling a flag adds/removes tools, this signals clients to refresh.
    await server.sendToolsListChanged();

    return text(`Feature ${feature} ${enabled ? "enabled" : "disabled"}`);
  }
);

// ── Tool: list client roots (if supported) ──────────────────────────────────

server.tool(
  {
    name: "list-roots",
    description: "List the client workspace roots",
    schema: z.object({}),
  },
  async (_, ctx) => {
    try {
      const roots = (await server.listRoots(ctx.session.sessionId)) ?? [];
      return object({ roots });
    } catch (err) {
      return text(
        `Could not list roots: ${(err as Error).message ?? "client does not support roots/list"}`
      );
    }
  }
);

server.listen().then(() => console.log("Resource Watcher running"));
```

## `resources/config-panel/widget.tsx`

```tsx
import { McpUseProvider, useWidget, useCallTool, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

interface Props {
  config: Record<string, string>;
  featureFlags: Record<string, boolean>;
}

export const widgetMetadata: WidgetMetadata = {
  description: "Configuration panel — read settings, update keys, toggle flags",
  props: z.object({
    config: z.record(z.string(), z.string()),
    featureFlags: z.record(z.string(), z.boolean()),
  }),
  metadata: { prefersBorder: true },
};

function Panel() {
  const { props } = useWidget<Props>();
  const { callTool: update, isPending: updating } = useCallTool("update-config");
  const { callTool: toggle } = useCallTool("toggle-feature");

  return (
    <div className="p-4 bg-white dark:bg-gray-950 space-y-4">
      <section>
        <h2 className="text-sm font-semibold mb-2">Settings</h2>
        <ul className="space-y-1">
          {Object.entries(props.config).map(([k, v]) => (
            <li key={k} className="flex justify-between text-sm">
              <span className="text-gray-500">{k}</span>
              <span className="font-mono">{v}</span>
            </li>
          ))}
        </ul>
        <button
          disabled={updating}
          onClick={() => update({ key: "theme", value: props.config.theme === "dark" ? "light" : "dark" })}
          className="mt-2 px-3 py-1.5 rounded bg-blue-500 text-white text-sm disabled:opacity-50"
        >
          Toggle theme
        </button>
      </section>

      <section>
        <h2 className="text-sm font-semibold mb-2">Feature Flags</h2>
        <ul className="space-y-1">
          {Object.entries(props.featureFlags).map(([k, v]) => (
            <li key={k} className="flex items-center justify-between text-sm">
              <span>{k}</span>
              <button
                onClick={() => toggle({ feature: k, enabled: !v })}
                className={`px-2 py-0.5 rounded text-xs ${
                  v ? "bg-emerald-500 text-white" : "bg-gray-200 text-gray-700"
                }`}
              >
                {v ? "ON" : "OFF"}
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

export default function ConfigPanel() {
  return (
    <McpUseProvider autoSize>
      <Panel />
    </McpUseProvider>
  );
}
```

## Run: `npm install && npm run dev`

## Test and primitives

1. Subscribe to `config://settings` in the Inspector, call `show-config`, then call `update-config`.
2. The notifications panel should show `notifications/resources/updated`.
3. Call `toggle-feature`; clients receive `notifications/tools/list_changed`.

- `server.notifyResourceUpdated(uri)` pushes resource-update notifications to subscribers.
- `server.sendToolsListChanged()` tells clients to re-read `tools/list`.
- `server.onRootsChanged(handler)` reacts to `notifications/roots/list_changed`.
- `server.listRoots(sessionId)` sends a server-to-client `roots/list` request.

## See also

- Canonical: `../31-canonical-examples/06-mcp-resource-watcher.md`
- Resources reference: `../06-resources/`
- Notifications reference: `../14-notifications/`
