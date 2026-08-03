# Canonical Example: Resource Server with Templates and Subscriptions

*Read this for one complete, runnable v2 resource example other files reference.*

This example shows the v2 resource pattern in one place: a static resource, a resource template with completion, a binary resource, and content-change notifications.

```typescript
import { MCPServer } from "mcp-use";
import { z } from "zod";
import { readFile } from "node:fs/promises";

const server = new MCPServer({
  name: "resource-watcher",
  version: "1.0.0",
});

// --- Static resource ---
let config = { theme: "light", featureFlags: { betaWidgets: false } };

server.resource(
  {
    name: "settings",
    uri: "config://settings",
    title: "Application Settings",
    mimeType: "application/json",
  },
  async (uri) => ({
    contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(config) }],
  })
);

// --- Resource template with completion ---
const documents: Record<string, { title: string; body: string }> = {
  "readme": { title: "README", body: "# Welcome" },
  "changelog": { title: "Changelog", body: "## v1.0.0" },
};

server.resourceTemplate(
  {
    name: "document",
    uriTemplate: "docs://{docId}",
    mimeType: "text/markdown",
    complete: {
      docId: (value) => Object.keys(documents).filter((id) => id.startsWith(value)),
    },
  },
  async (uri, { docId }) => {
    const id = Array.isArray(docId) ? docId[0] : docId;
    const doc = documents[id];
    if (!doc) throw new Error(`Document not found: ${id}`);
    return {
      contents: [{ uri: uri.href, mimeType: "text/markdown", text: doc.body }],
    };
  }
);

// --- Binary resource ---
server.resource(
  { name: "logo", uri: "assets://logo.png", mimeType: "image/png" },
  async (uri) => {
    const buffer = await readFile("./assets/logo.png");
    return {
      contents: [{ uri: uri.href, mimeType: "image/png", blob: buffer.toString("base64") }],
    };
  }
);

// --- Tool that mutates state and notifies listeners ---
server.tool(
  {
    name: "update-config",
    description: "Update a config field and notify listeners",
    inputSchema: z.object({
      key: z.enum(["theme"]),
      value: z.string(),
    }),
  },
  async ({ key, value }, ctx) => {
    config = { ...config, [key]: value };

    // Cross-request: active subscriptions/listen clients refresh their cache
    await server.notifyResourceUpdated("config://settings");

    // Request-scoped: delivered on this call's own response stream
    await ctx.sendNotification("com.example/config-changed", { key, value });

    return {
      content: [{ type: "text", text: `Updated "${key}" to "${value}"` }],
    };
  }
);

// --- Tool that adds content behind the existing template ---
server.tool(
  {
    name: "add-document",
    description: "Add a document served by the existing template",
    inputSchema: z.object({ id: z.string(), title: z.string(), body: z.string() }),
  },
  async ({ id, title, body }) => {
    documents[id] = { title, body };

    // The template descriptor is unchanged, so there is no resources-list notification.
    // Notify a concrete index URI here only if your server exposes and updates one.
    return { content: [{ type: "text", text: `Added docs://${id}` }] };
  }
);

await server.listen(3000);
```

## Key patterns here

1. **Definition-first registration** — `server.resource(definition, callback)`, `server.resourceTemplate(definition, callback)`.
2. **Raw envelopes only** — every callback returns `{ contents: [...] }` directly; no deprecated `object()`/`text()` helpers.
3. **Binary via `blob`** — the logo resource uses a base64 `blob` field, not the deprecated `image()` helper.
4. **Top-level `complete`** — the template's completion map sits directly on the definition object, not nested under `callbacks`.
5. **`string | string[]` params** — `docId` is narrowed with `Array.isArray()` before use, since RFC 6570 exploded/multi-value matches can produce an array.
6. **Notify only real changes** — content added behind an existing template does not change `resources/list`; use `notifyResourceUpdated()` only when a concrete exposed URI changes.

## Cross-cluster references

- `06-subscriptions-listen.md` — subscription lifecycle and notification rules
- `03-resource-templates.md` — `uriTemplate` syntax and completion providers
- `../14-notifications/` — request-scoped vs. cross-request notification patterns
- `../17-advanced/` — proxy gateways and other server-composition patterns

Copy and adapt this shape for your server.
