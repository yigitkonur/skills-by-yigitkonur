# URI Conventions

Resource URIs are the routing layer of the server. A consistent scheme makes the registry navigable, prevents collisions, and produces autocompletable paths.

## Scheme rules

1. URIs must include a scheme — `config://main`, not bare `config`.
2. Use a scheme that is clear inside your server — `config://`, `users://`, `myapp://`.
3. Prefer path segments for template variables — `users://123/posts/45`, not `users://lookup?id=123`.
4. Use kebab-case for multi-word segments — `user-profile`, not `userProfile`.
5. Avoid bare paths like `config.json`; resource registration and examples use absolute URIs with schemes.

| Bad | Good | Why |
|---|---|---|
| `data://get?id=1` | `data://items/1` | Path params match the documented template examples |
| `file:///tmp/foo` | `app://files/foo` | Don't leak filesystem layout |
| `config` | `config://main` | Missing scheme breaks routing |
| `MyApp://Users/{ID}` | `myapp://users/{id}` | Lowercase scheme and segments |

## When to invent a scheme

Use a custom scheme when:
- The resource type is **specific to your domain** (`tickets://`, `runs://`, `incidents://`)
- The same noun could mean different things in two servers (`config://` is fine because routing is per-server)
- You want grouping in client UIs (clients often group by scheme)

Use a **standard** scheme when:
- The resource is genuinely a file, HTTP URL, or git ref — `file://`, `https://`, `git://`
- You're proxying an external system — `github://`, `npm://`, `s3://`

| Scheme | Use for |
|---|---|
| `config://` | Server or app configuration |
| `docs://` | Documentation pages |
| `users://` | User records |
| `db://` | Database rows |
| `api://` | Proxied external APIs |
| `assets://` | Static binary assets (images, audio) |
| `file://` | Local files (when the resource genuinely *is* a file) |
| `https://` | Public web URLs (rare — usually wrap them) |

## Simple placeholders only

`mcp-use@1.26.0` documents simple `{var}` placeholders and extracts one non-slash segment per placeholder.

| Allowed | Not allowed |
|---|---|
| `users://{id}` | `users://{?id}` |
| `docs://{category}/{slug}` | `docs://{+path}` |
| `logs://{date}/{level}` | `logs://{date,level}` |

If a value can contain `/`, encode it before building the URI and decode it in your handler:

```text
Template:  users://{id}
Value:     "user/1"
Resolved:  users://user%2F1
```

Use simple identifier-style variable names (`id`, `userId`, `category`) so params stay ergonomic in handlers.

## Versioning

Bake the version into the scheme or a fixed segment when you need both old and new shapes:

```text
v1: api://v1/users/{id}
v2: api://v2/users/{id}
```

Do not use query params for versioning; they make template matching and completion harder to reason about.

## Discoverability

For a small dynamic set (open files, active sessions), register a template and call `sendResourcesListChanged()` when the exposed resource set changes. For a large set (10,000 users), don't enumerate everything — let the client request specific URIs and rely on autocomplete completions.

See `03-resource-templates.md` for completion callbacks and `06-subscriptions.md` for change notifications.

## Anti-patterns

```typescript
// Query parameters
uriTemplate: "users://get?id={id}"               // avoid
uriTemplate: "users://{id}"                      // right

// Mixed case
uriTemplate: "Users://{ID}"                      // wrong
uriTemplate: "users://{id}"                      // right

// Static URI for variable data
server.resource({ uri: "users://me" }, ...)      // wrong if data varies
server.resourceTemplate({ uriTemplate: "users://{id}" }, ...) // right

// No scheme
uriTemplate: "config"                            // wrong
uriTemplate: "config://main"                     // right
```
