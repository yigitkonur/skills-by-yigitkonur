# Resource Templates

*Read this when exposing parameterized resources via URI templates and completion callbacks.*

A **template** is an RFC 6570 URI Template. Use `server.resourceTemplate()` when the resource is one of many addressable items (per-user, per-id, per-path).

## Registration

```typescript
import { MCPServer } from "mcp-use";

server.resourceTemplate(
  {
    name: "user-profile",
    uriTemplate: "users://{userId}/profile",
    title: "User Profile",
    mimeType: "application/json",
  },
  async (uri, { userId }, ctx) => {
    const id = Array.isArray(userId) ? userId[0] : userId;
    const user = await db.getUser(id);
    if (!user) throw new Error(`User ${id} not found`);
    return {
      contents: [
        { uri: uri.href, mimeType: "application/json", text: JSON.stringify(user) },
      ],
    };
  },
);
```

Return the raw `{ contents: [...] }` envelope — see `01-overview.md`. Deprecated response helpers (`object()`, `text()`, ...) are still accepted as conversion inputs; see `../05-responses/07-deprecated-v1-helpers.md`.

## Handler signature

```typescript
(uri: URL, params: TParams, ctx: RequestContext<TUser, HasOAuth, TEnv>) =>
  | ReadResourceResult
  | CallToolResult
  | Promise<ReadResourceResult | CallToolResult>
```

| Argument | Description |
|---|---|
| `uri` | Resolved `URL` object — `uri.href` gives the full URI string |
| `params` | Object of extracted template variables. Each value is `string \| string[]` — see "Param types" below, not always a plain string |
| `ctx` | `RequestContext<TUser, HasOAuth, TEnv>` — auth (when OAuth is configured), request metadata, abort `signal` |

JavaScript lets you omit trailing parameters your callback doesn't use, so shorter forms compile even though the declared type always includes all three:

```typescript
// URI only
server.resourceTemplate(
  { name: "echo", uriTemplate: "echo://{path}" },
  async (uri) => ({
    contents: [{ uri: uri.href, mimeType: "text/plain", text: `Requested: ${uri.href}` }],
  }),
);

// URI + params (most common)
server.resourceTemplate(
  { name: "user", uriTemplate: "user://{userId}" },
  async (uri, { userId }) => ({
    contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(await fetchUser(userId)) }],
  }),
);

// With ctx for auth (ctx.auth is only populated when OAuth is configured)
server.resourceTemplate(
  { name: "private", uriTemplate: "private://{id}" },
  async (uri, { id }, ctx) => ({
    contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(await getPrivateData(id, ctx.auth?.user)) }],
  }),
);
```

## URI template syntax (RFC 6570)

`uriTemplate` is a full RFC 6570 URI Template, matched by the official SDK's `UriTemplate` class (`@modelcontextprotocol/server`) — mcp-use delegates matching and variable extraction to it, it does not implement its own parser. This is a real spec subset, not just `{var}` placeholders. Supported operators:

| Operator | Expression | Meaning | Regex behavior |
|---|---|---|---|
| _(none)_ | `{var}` | Simple string expansion | Matches one path segment; excludes `/` and `,` |
| `+` | `{+var}` | Reserved expansion | Matches greedily, **including** `/` |
| `#` | `{#var}` | Fragment expansion | Matches greedily, **including** `/` |
| `.` | `{.var}` | Label expansion (`.value`) | Matches after a literal `.` |
| `/` | `{/var}` | Path-segment expansion (`/value`) | Matches after a literal `/` |
| `?` | `{?var}` | Query expansion (`?var=value`) | Matches a query-string key |
| `&` | `{&var}` | Continuation query expansion (`&var=value`) | Matches a query-string key |

Modifiers:
- **Explode** (`{path*}`) — the extracted value may expand to multiple comma-separated segments; the callback receives `string[]` for that variable instead of `string`.
- **Comma-separated variable lists** in one expression are valid: `{x,y}` declares two variables in a single `{}` block.
- A `;` (path-style parameter) operator appears in some RFC 6570 type-level references but is **not implemented** by the runtime `UriTemplate.getOperator()` matcher shipped in beta.66 — do not use `{;var}`; it will not match as expected.

| Template | Example URI | Extracted params |
|---|---|---|
| `db://users/{id}` | `db://users/123` | `{ id: "123" }` |
| `docs://{category}/{id}` | `docs://api/auth` | `{ category: "api", id: "auth" }` |
| `logs://{date}/{level}` | `logs://2023-01-01/error` | `{ date: "2023-01-01", level: "error" }` |
| `files://{+path}` | `files://a/b/c.txt` | `{ path: "a/b/c.txt" }` (`+` captures `/`) |
| `search://{?q,limit}` | `search://?q=x&limit=10` | `{ q: "x", limit: "10" }` |

- A plain `{path}` (no operator) does **not** capture `/` — use `{+path}` when you need a multi-segment capture.
- Validate semantic constraints (format, allowed values, existence) yourself after extraction; the template only matches shape, not content.

For broader scheme guidance, see `05-uri-conventions.md`.

## Param types

`InferTemplateParams` types every declared variable as `string | string[]`, never a bare `string`, because an exploded (`{var*}`) or comma-joined match can expand to multiple values at runtime:

```typescript
async (uri, { userId }) => {
  const id = Array.isArray(userId) ? userId[0] : userId; // narrow before use
  ...
}
```

## Parameter validation

Template params arrive as strings (or string arrays) — validate them before use, especially for filesystem or DB lookups:

```typescript
server.resourceTemplate(
  { name: "log-file", uriTemplate: "logs://{date}/{file}", mimeType: "text/plain" },
  async (uri, { date, file }) => {
    const d = Array.isArray(date) ? date[0] : date;
    const f = Array.isArray(file) ? file[0] : file;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) throw new Error("Invalid date");
    if (!/^[a-z0-9-]+\.log$/.test(f)) throw new Error("Invalid file");
    const path = join(process.cwd(), "logs", d, f);
    return {
      contents: [{ uri: uri.href, mimeType: "text/plain", text: await readFile(path, "utf-8") }],
    };
  },
);
```

## Autocomplete for template variables

Provide URI variable suggestions via a top-level `complete` field on the definition object — **not** nested under `callbacks`. The server filters list-based completions case-insensitively by prefix; the SDK caps wire results at 100 values and derives `total`/`hasMore` from the returned array.

**List-based** — static array:

```typescript
server.resourceTemplate(
  {
    name: "user",
    uriTemplate: "users://{userId}",
    complete: {
      userId: ["user-1", "user-2", "user-3"],
    },
  },
  async (uri, { userId }) => ({
    contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(await db.getUser(userId)) }],
  }),
);
```

**Callback-based** — dynamic, with access to other already-resolved param values via the official completion context (`context?.arguments?.<field>`); may be sync or async:

```typescript
server.resourceTemplate(
  {
    name: "document",
    uriTemplate: "docs://{category}/{docId}",
    complete: {
      category: (value) => categories.filter((c) => c.startsWith(value)),
      docId: async (value, context) => {
        const category = context?.arguments?.category ?? "";
        const hits = await docs.search(category, value);
        return hits.map((d) => d.id);
      },
    },
  },
  async (uri, { category, docId }) => ({
    contents: [{ uri: uri.href, mimeType: "text/plain", text: await loadDoc(category, docId) }],
  }),
);
```

For prompt argument completion, see `../07-prompts/04-completable-arguments.md`.

## Pagination

Resources return a single payload. For large datasets, paginate via the URI:

```typescript
server.resourceTemplate(
  { name: "users-page", uriTemplate: "users://page/{page}", mimeType: "application/json" },
  async (uri, { page }) => {
    const n = parseInt(Array.isArray(page) ? page[0] : page, 10);
    const users = await db.users.findMany({ skip: (n - 1) * 20, take: 20 });
    return {
      contents: [{
        uri: uri.href,
        mimeType: "application/json",
        text: JSON.stringify({
          data: users,
          next: `users://page/${n + 1}`,
          prev: n > 1 ? `users://page/${n - 1}` : null,
        }),
      }],
    };
  },
);
```

## Annotations

Same `annotations` field as static resources — see `02-static-resources.md`.
