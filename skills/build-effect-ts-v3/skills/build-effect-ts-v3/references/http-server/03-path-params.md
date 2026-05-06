# Path Parameters
Use `HttpApiSchema.param` with template-string endpoints to decode route parameters into typed handler fields.

## Basic Pattern

Path params are declared in the endpoint path template.

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

const id = HttpApiSchema.param("id", Schema.NumberFromString)

const getUser = HttpApiEndpoint.get("getUser")`/users/${id}`
```

The route path becomes `/users/:id`. The handler sees a decoded number:

```typescript
handlers.handle("getUser", ({ path }) =>
  Effect.succeed({ id: path.id })
)
```

## Why `NumberFromString`

Route parameters arrive as strings. Use schemas that can decode from strings
for non-string values.

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

const orgId = HttpApiSchema.param("orgId", Schema.UUID)
const userId = HttpApiSchema.param("userId", Schema.NumberFromString)

const getOrgUser =
  HttpApiEndpoint.get("getOrgUser")`/orgs/${orgId}/users/${userId}`
```

`Schema.Number` is not the right schema for URL path params because the encoded
input must be string-compatible. `Schema.NumberFromString` documents and
performs the conversion.

## Optional Segments

The template constructor supports optional path parameters through optional
property signatures. Use them sparingly because optional path segments can make
routes harder to reason about.

```typescript
import { HttpApiEndpoint } from "@effect/platform"
import { Schema } from "effect"

const maybeSlug = Schema.optional(Schema.String)

const route = HttpApiEndpoint.get("readPage")`/pages/${maybeSlug}`
```

When a parameter is optional, the generated route segment uses an optional
marker internally.

## Multiple Parameters

Use separate `param` calls when the route has multiple named values.

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

const projectId = HttpApiSchema.param("projectId", Schema.UUID)
const taskId = HttpApiSchema.param("taskId", Schema.NumberFromString)

const getTask =
  HttpApiEndpoint.get("getTask")`/projects/${projectId}/tasks/${taskId}`
```

Handler type:

```typescript
{
  readonly path: {
    readonly projectId: string
    readonly taskId: number
  }
}
```

## Validating Param Domains

Path schemas can be refined just like other schemas.

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

const positiveId = HttpApiSchema.param(
  "id",
  Schema.NumberFromString.pipe(Schema.positive())
)

const getInvoice = HttpApiEndpoint.get("getInvoice")`/invoices/${positiveId}`
```

Invalid params fail before the handler and are represented as
`HttpApiDecodeError` with a `400` response.

## Plain Path Strings

This route matches, but does not create a typed `path` field:

```typescript
import { HttpApiEndpoint } from "@effect/platform"

const getUser = HttpApiEndpoint.get("getUser", "/users/:id")
```

Prefer the template form when the handler or client needs typed params:

```typescript
import { HttpApiEndpoint, HttpApiSchema } from "@effect/platform"
import { Schema } from "effect"

const id = HttpApiSchema.param("id", Schema.NumberFromString)
const getUser = HttpApiEndpoint.get("getUser")`/users/${id}`
```

## Handler Example

```typescript
import { HttpApiBuilder, HttpApiEndpoint, HttpApiGroup, HttpApi, HttpApiSchema } from "@effect/platform"
import { Effect, Schema } from "effect"

class User extends Schema.Class<User>("User")({
  id: Schema.Int,
  name: Schema.String
}) {}

const id = HttpApiSchema.param("id", Schema.NumberFromString)

const users = HttpApiGroup.make("users").add(
  HttpApiEndpoint.get("getUser")`/users/${id}`.addSuccess(User)
)

class Api extends HttpApi.make("api").add(users) {}

const UsersLive = HttpApiBuilder.group(Api, "users", (handlers) =>
  handlers.handle("getUser", ({ path }) =>
    Effect.succeed(new User({ id: path.id, name: "Ada" }))
  )
)
```

The handler does not need to parse `id`; it is already a number.

## Cross-references

See also: [02-defining-endpoints.md](02-defining-endpoints.md), [04-query-and-payload.md](04-query-and-payload.md), [07-handlers.md](07-handlers.md), [08-error-responses.md](08-error-responses.md)
