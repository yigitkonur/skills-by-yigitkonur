# Resource Templates

A **template** is a URI pattern with `{param}` placeholders. Use `server.resourceTemplate()` when the resource is one of many addressable items (per-user, per-id, per-path).

## Registration

```typescript
import { object } from "mcp-use/server";

server.resourceTemplate(
  {
    name: "user-profile",
    uriTemplate: "users://{userId}/profile",
    title: "User Profile",
    mimeType: "application/json",
  },
  async (uri, { userId }) => {
    const user = await db.getUser(userId);
    if (!user) throw new Error(`User ${userId} not found`);
    return object(user);
  },
);
```

## Handler signature

```typescript
async (uri: URL, params: Record<string, string>, ctx?: EnhancedResourceContext) => Response
```

| Argument | Description |
|---|---|
| `uri` | Resolved `URL` object — `uri.toString()` gives the full URI |
| `params` | Object of extracted template variables, all strings |
| `ctx` | Optional. Auth, request metadata, client capability helpers |

Use the simplest signature that meets your needs:

```typescript
// URI only
server.resourceTemplate(
  { name: "echo", uriTemplate: "echo://{path}" },
  async (uri) => text(`Requested: ${uri.toString()}`),
);

// URI + params (most common)
server.resourceTemplate(
  { name: "user", uriTemplate: "user://{userId}" },
  async (uri, { userId }) => object(await fetchUser(userId)),
);

// With ctx for auth
server.resourceTemplate(
  { name: "private", uriTemplate: "private://{id}" },
  async (uri, { id }, ctx) => object(await getPrivateData(id, ctx.auth)),
);
```

## URI template rules

Canonical `mcp-use` examples use simple `{var}` placeholders, such as `db://users/{id}`. In `mcp-use@1.26.0`, `parseTemplateUri()` extracts one non-slash URI segment per placeholder.

| Template | URI | Extracted params |
|---|---|---|
| `db://users/{id}` | `db://users/123` | `{ id: "123" }` |
| `docs://{category}/{id}` | `docs://api/auth` | `{ category: "api", id: "auth" }` |
| `logs://{date}/{level}` | `logs://2023-01-01/error` | `{ date: "2023-01-01", level: "error" }` |

- Do not rely on wildcard/path captures; `{path}` does not capture `/`.
- Do not document `{?query}`, `{*path}`, or other RFC 6570 operators for `mcp-use@1.26.0`; the package docs only show simple placeholders.
- Validate semantic constraints yourself after extraction.

For broader scheme guidance, see `05-uri-conventions.md`.

## Parameter validation

Template params arrive as strings — validate them before use, especially for filesystem or DB lookups:

```typescript
server.resourceTemplate(
  { name: "log-file", uriTemplate: "logs://{date}/{file}", mimeType: "text/plain" },
  async (uri, { date, file }) => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new Error("Invalid date");
    if (!/^[a-z0-9-]+\.log$/.test(file)) throw new Error("Invalid file");
    const path = join(process.cwd(), "logs", date, file);
    return text(await readFile(path, "utf-8"));
  },
);
```

## Autocomplete for template variables

Provide URI variable suggestions via `callbacks.complete`. The server filters list-based completions case-insensitively by prefix.

**List-based** — static array:

```typescript
server.resourceTemplate(
  {
    name: "user",
    uriTemplate: "users://{userId}",
    callbacks: {
      complete: {
        userId: ["user-1", "user-2", "user-3"],
      },
    },
  },
  async (uri, { userId }) => object(await db.getUser(userId)),
);
```

**Callback-based** — dynamic, with access to other already-resolved param values:

```typescript
server.resourceTemplate(
  {
    name: "document",
    uriTemplate: "docs://{category}/{docId}",
    callbacks: {
      complete: {
        category: async (value) => categories.filter((c) => c.startsWith(value)),
        docId: async (value, context) => {
          const category = context?.arguments?.category;
          const hits = await docs.search(category, value);
          return hits.map((d) => d.id);
        },
      },
    },
  },
  async (uri, { category, docId }) => text(await loadDoc(category, docId)),
);
```

For prompt argument completion, see `../07-prompts/04-completable-arguments.md`.

## Pagination

Resources return a single payload. For large datasets, paginate via the URI:

```typescript
server.resourceTemplate(
  { name: "users-page", uriTemplate: "users://page/{page}", mimeType: "application/json" },
  async (uri, { page }) => {
    const n = parseInt(page);
    const users = await db.users.findMany({ skip: (n - 1) * 20, take: 20 });
    return object({
      data: users,
      next: `users://page/${n + 1}`,
      prev: n > 1 ? `users://page/${n - 1}` : null,
    });
  },
);
```

## Annotations

Same `annotations` field as static resources — see `02-static-resources.md`.
