# Defining Endpoints
Define HTTP methods, paths, payload schemas, response schemas, and typed route names with `HttpApiEndpoint`.

## Constructor Shape

Every endpoint has a stable name, method, and path.

```typescript
import { HttpApiEndpoint } from "@effect/platform"

const listUsers = HttpApiEndpoint.get("listUsers", "/users")
const createUser = HttpApiEndpoint.post("createUser", "/users")
const updateUser = HttpApiEndpoint.patch("updateUser", "/users/:id")
const deleteUser = HttpApiEndpoint.del("deleteUser", "/users/:id")
```

The first argument is the endpoint name. It becomes the handler key and the
derived client method name. Keep it stable and semantic.

| Constructor | HTTP method |
|---|---|
| `HttpApiEndpoint.get` | `GET` |
| `HttpApiEndpoint.post` | `POST` |
| `HttpApiEndpoint.put` | `PUT` |
| `HttpApiEndpoint.patch` | `PATCH` |
| `HttpApiEndpoint.del` | `DELETE` |
| `HttpApiEndpoint.head` | `HEAD` |
| `HttpApiEndpoint.options` | `OPTIONS` |

## Prefer Template Paths For Typed Params

Plain `"/users/:id"` paths route correctly, but template-string paths with
`HttpApiSchema.param` also produce typed handler `path` fields.

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

const userId = HttpApiSchema.param("id", Schema.NumberFromString)

const getUser = HttpApiEndpoint.get("getUser")`/users/${userId}`
```

The handler for `getUser` receives `{ path: { id: number } }`.

## Success Schemas

Use `addSuccess` to declare the encoded success response. The default success
schema is `HttpApiSchema.NoContent`.

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

class User extends Schema.Class<User>("User")({
  id: Schema.Int,
  name: Schema.String
}) {}

const getUser = HttpApiEndpoint.get("getUser", "/users/current")
  .addSuccess(User)

const createUser = HttpApiEndpoint.post("createUser", "/users")
  .setPayload(Schema.Struct({ name: Schema.String }))
  .addSuccess(User, { status: 201 })

const deleteUser = HttpApiEndpoint.del("deleteUser", "/users/current")
  .addSuccess(HttpApiSchema.NoContent)
```

If no status annotation is supplied, non-void success defaults to `200`.
`Schema.Void`/`NoContent` defaults to `204`.

## Method And Payload Rules

`setPayload` is method-aware. Methods without bodies, such as `GET`, require
payload schemas encodable as URL search parameters. For JSON request bodies,
use body methods such as `POST`, `PUT`, or `PATCH`.

```typescript
import { HttpApiEndpoint } from "@effect/platform"
import { Schema } from "effect"

const searchUsers = HttpApiEndpoint.get("searchUsers", "/users")
  .setUrlParams(Schema.Struct({
    query: Schema.String,
    page: Schema.NumberFromString
  }))

const replaceUser = HttpApiEndpoint.put("replaceUser", "/users/current")
  .setPayload(Schema.Struct({
    name: Schema.String
  }))
```

Do not model a JSON body on a `GET`; use query parameters or switch to a body
method.

## Endpoint Errors

Declare expected failures with `addError`. The schema determines both the typed
failure and the encoded response.

```typescript
import { HttpApiEndpoint, HttpApiError } from "@effect/platform"
import { Schema } from "effect"

class User extends Schema.Class<User>("User")({
  id: Schema.Int,
  name: Schema.String
}) {}

const getUser = HttpApiEndpoint.get("getUser", "/users/current")
  .addSuccess(User)
  .addError(HttpApiError.Unauthorized)
  .addError(HttpApiError.NotFound)
```

When the handler fails with one of those declared errors, the server encodes it
using the endpoint error schema.

## Full Endpoint Example

```typescript
import { HttpApiEndpoint, HttpApiError, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

class User extends Schema.Class<User>("User")({
  id: Schema.Int,
  name: Schema.String,
  email: Schema.String
}) {}

class UpdateUser extends Schema.Class<UpdateUser>("UpdateUser")({
  name: Schema.optional(Schema.String),
  email: Schema.optional(Schema.String)
}) {}

const id = HttpApiSchema.param("id", Schema.NumberFromString)

const updateUser = HttpApiEndpoint.patch("updateUser")`/users/${id}`
  .setPayload(UpdateUser)
  .setHeaders(Schema.Struct({
    "x-request-id": Schema.String
  }))
  .addSuccess(User)
  .addError(HttpApiError.Unauthorized)
  .addError(HttpApiError.NotFound)
```

The handler receives:

```typescript
{
  readonly path: { readonly id: number }
  readonly payload: UpdateUser
  readonly headers: { readonly "x-request-id": string }
  readonly request: HttpServerRequest
}
```

The derived client must pass the same fields.

## Naming Rules

Endpoint names are part of the API surface:

- use verbs: `listUsers`, `getUser`, `createUser`
- avoid route-shaped names: `getSlashUsersById`
- avoid version suffixes unless they are part of the public contract
- keep names unique inside a group

The group and endpoint names become client accessors:

```typescript
const user = yield* client.users.getUser({ path: { id: 1 } })
```

## Anti-patterns

Do not define endpoint schemas only inside handlers. That loses typed client
derivation and Swagger generation.

Do not hand-parse `request.url` when `setUrlParams` or template params can
decode the same value.

Do not return arbitrary JSON shapes from handlers without matching
`addSuccess`; the server encodes through the success schema.

## Cross-references

See also: [03-path-params.md](03-path-params.md), [04-query-and-payload.md](04-query-and-payload.md), [08-error-responses.md](08-error-responses.md), [07-handlers.md](07-handlers.md)
