# Resources Overview

*Read this when deciding whether and how to expose resources from a v2 server.*

A **resource** is read-only data the agent can fetch by URI — config files, database records, documents, logs, binary assets. Resources have no side effects. For mutating actions, use a tool.

## When to use a resource

| You expose | Primitive |
|---|---|
| Read-only data the LLM should consult | Resource |
| An action with side effects | Tool |
| A reusable instruction template | Prompt |

If the data varies per request (per-user, per-id), use a **template**. Otherwise use a **static** resource.

## API

```typescript
import { MCPServer } from "mcp-use";

const server = new MCPServer({ name: "app", version: "1.0.0" });

// Static — fixed URI
server.resource(
  {
    name: "config",
    uri: "config://app",
    title: "Application Config",
    description: "Current application configuration",
    mimeType: "application/json",
  },
  async (uri) => ({
    contents: [
      {
        uri: uri.href,
        mimeType: "application/json",
        text: JSON.stringify({ env: "production", version: "1.0.0" }),
      },
    ],
  })
);

// Template — RFC 6570 URI template
server.resourceTemplate(
  {
    name: "user-profile",
    uriTemplate: "users://{userId}/profile",
    mimeType: "application/json",
  },
  async (uri, { userId }, ctx) => ({
    contents: [
      {
        uri: uri.href,
        mimeType: "application/json",
        text: JSON.stringify(await db.getUser(userId)),
      },
    ],
  })
);
```

Return the raw `{ contents: [...] }` envelope (`ReadResourceResult`). Each entry carries its own `uri` and `mimeType`, plus either `text` or a base64 `blob`. Deprecated helper-shaped returns (`text()`, `object()`, ...) are still converted automatically — see `../05-responses/07-deprecated-v1-helpers.md`.

## Protocol surface

| Surface | Purpose |
|---|---|
| `resources/list` | Enumerate static resources |
| `resources/templates/list` | Enumerate registered templates |
| `resources/read` | Fetch the content of one URI (static or template match) |
| `subscriptions/listen` | v2's stateless per-request listener for change notifications — see `06-subscriptions-listen.md` |
| `notifications/resources/updated` | Server-pushed notification of content change (`server.notifyResourceUpdated(uri)`) |
| `notifications/resources/list_changed` | Server-pushed notification of registry change (`server.notifyResourcesChanged()`) |

mcp-use still advertises a `resources.subscribe: true` server capability, and the underlying SDK still defines `resources/subscribe`/`resources/unsubscribe` request schemas — but neither is reachable against a v2 mcp-use server: the modern (`2026-07-28`) method registry never includes them, and no handler for them is ever installed even on a legacy-negotiated connection, so both are rejected with `-32601 Method Not Found`. The `subscribe` capability bit signals "ask for resource updates via `subscriptions/listen`'s `resourceSubscriptions` filter," not "the legacy request works." See `06-subscriptions-listen.md` for the full trace and what actually ships.

## Definition fields

| Field | Required | Notes |
|---|---|---|
| `name` | yes | Unique identifier within the server |
| `uri` (static) | yes | Fixed string, must include a scheme |
| `uriTemplate` (template) | yes | RFC 6570 URI template — see `03-resource-templates.md` |
| `title` | no | Human display label; falls back to `name` |
| `description` | no | Shown to clients in resource pickers |
| `mimeType` | no | Advertised in `resources/list` / `resources/templates/list`; content entries carry their own `mimeType` on the wire — set it in the callback's result too |
| `annotations` | no | `audience`, `priority`, `lastModified` — see `02-static-resources.md` |
| `_meta` | no | Extension metadata on the `resources/list` descriptor; not copied into `resources/read` content — return it per-entry from the callback |
| `complete` (template only) | no | Top-level map, URI variable autocompletion — see `03-resource-templates.md` |

## Cluster map

| File | Topic |
|---|---|
| `02-static-resources.md` | Fixed-URI resources, raw envelopes, annotations |
| `03-resource-templates.md` | RFC 6570 URI templates, parameter handlers, completion |
| `04-binary-and-image.md` | Image, audio, PDF, generic binary payloads |
| `05-uri-conventions.md` | Scheme design, template rules, anti-patterns |
| `06-subscriptions-listen.md` | Stateless subscription lifecycle, `notifyResourceUpdated`, registry changes |
| `canonical-anchor.md` | One complete, runnable v2 resource server (static, template, binary, subscriptions) |

**Canonical doc:** https://docs.mcp-use.com/v2/typescript/server/resources
