# Resources Overview

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
import { object, text } from "mcp-use/server";

// Static — fixed URI
server.resource(
  {
    name: "config",
    uri: "config://app",
    title: "Application Config",
    description: "Current application configuration",
    mimeType: "application/json",
  },
  async () => object({ env: "production", version: "1.0.0" })
);

// Template — URI with {param} placeholders
server.resourceTemplate(
  {
    name: "user-profile",
    uriTemplate: "users://{userId}/profile",
    mimeType: "application/json",
  },
  async (uri, { userId }) => object(await db.getUser(userId))
);
```

## Protocol and helpers

| Surface | Purpose |
|---|---|
| `resources/list` | Enumerate static resources |
| `resources/read` | Fetch the content of one URI |
| `listResourceTemplates()` | Client helper that enumerates templates separately |
| `resources/subscribe` | Subscribe a client to a URI for updates |
| `notifications/resources/updated` | Server-pushed notification of content change |
| `notifications/resources/list_changed` | Server-pushed notification of registry change |

## Definition fields

| Field | Required | Notes |
|---|---|---|
| `name` | yes | Unique identifier within the server |
| `uri` (static) | yes | Fixed string, must include a scheme |
| `uriTemplate` (template) | yes | Simple template with `{var}` placeholders |
| `title` | no | Human display label; falls back to `name` |
| `description` | no | Shown to clients in resource pickers |
| `mimeType` | no | Hint for client rendering |
| `annotations` | no | `audience`, `priority`, `lastModified` — see `02-static-resources.md` |
| `callbacks.complete` | no | URI variable autocompletion — see `03-resource-templates.md` |

## Cluster map

| File | Topic |
|---|---|
| `02-static-resources.md` | Fixed-URI resources, response helpers, annotations |
| `03-resource-templates.md` | URI templates, parameter handlers, completion |
| `04-binary-and-image.md` | Image, audio, PDF, generic binary payloads |
| `05-uri-conventions.md` | Scheme design, simple template rules, anti-patterns |
| `06-subscriptions.md` | Subscription lifecycle, `notifyResourceUpdated`, registry changes |
| `canonical-anchor.md` | `mcp-use/mcp-resource-watcher` reference repo |

**Canonical doc:** https://manufact.com/docs/typescript/server/resources
