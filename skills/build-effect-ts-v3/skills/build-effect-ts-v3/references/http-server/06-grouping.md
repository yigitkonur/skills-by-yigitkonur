# Grouping
Use `HttpApiGroup.make().add()` to organize endpoints into typed resource groups.

## Group Shape

A group has an identifier and a set of endpoints.

```typescript
import { HttpApiEndpoint, HttpApiGroup } from "@effect/platform"
import { Schema } from "effect"

class User extends Schema.Class<User>("User")({
  id: Schema.Int,
  name: Schema.String
}) {}

const users = HttpApiGroup.make("users")
  .add(HttpApiEndpoint.get("listUsers", "/users").addSuccess(Schema.Array(User)))
  .add(HttpApiEndpoint.post("createUser", "/users").addSuccess(User))
```

The identifier `"users"` becomes:

- the `HttpApiBuilder.group(Api, "users", ...)` implementation key
- the derived client namespace `client.users`
- the OpenAPI tag unless overridden by annotations

## Add Groups To An API

```typescript
import { HttpApi, HttpApiEndpoint, HttpApiGroup } from "@effect/platform"
import { Schema } from "effect"

const health = HttpApiGroup.make("health").add(
  HttpApiEndpoint.get("healthz", "/healthz").addSuccess(Schema.Void)
)

const users = HttpApiGroup.make("users").add(
  HttpApiEndpoint.get("listUsers", "/users")
    .addSuccess(Schema.Array(Schema.String))
)

class Api extends HttpApi.make("api")
  .add(health)
  .add(users)
{}
```

Each group can be implemented independently and then provided to the top-level
API layer.

## Prefixing Groups

Use `prefix` to avoid repeating a base path.

```typescript
import { HttpApiEndpoint, HttpApiGroup } from "@effect/platform"
import { Schema } from "effect"

const users = HttpApiGroup.make("users")
  .add(HttpApiEndpoint.get("listUsers", "/").addSuccess(Schema.Array(Schema.String)))
  .add(HttpApiEndpoint.get("getUser", "/:id").addSuccess(Schema.String))
  .prefix("/users")
```

`prefix` applies to endpoints that already exist when it is called. Add the
prefix after all endpoint `.add(...)` calls for predictable results.

## Group-Level Errors

Use `addError` when every endpoint in a group can fail the same way.

```typescript
import { HttpApiError, HttpApiGroup } from "@effect/platform"

const securedUsers = users.addError(HttpApiError.Unauthorized)
```

Endpoint-level errors are still useful for endpoint-specific failures.

## Group-Level Middleware

Attach middleware to a whole group when every endpoint needs it.

```typescript
const securedUsers = users.middleware(Authorization)
```

Use group-level middleware for resource-wide auth or tenancy. Use endpoint-level
middleware for one-off checks.

## Endpoint Middleware In A Group

`middlewareEndpoints` applies a middleware to endpoints already in the group.
Endpoints added after the call are not affected, so place it after the endpoint
set is complete.

```typescript
const users = HttpApiGroup.make("users")
  .add(listUsers)
  .add(getUser)
  .middlewareEndpoints(Authorization)
```

Prefer `group.middleware(Authorization)` when every current and future endpoint
in the group should require it.

## Top-Level Groups

`HttpApiGroup.make("root", { topLevel: true })` creates routes without using
the group identifier as a logical namespace in OpenAPI.

```typescript
import { HttpApiEndpoint, HttpApiGroup, HttpApiSchema } from "@effect/platform"

const root = HttpApiGroup.make("root", { topLevel: true }).add(
  HttpApiEndpoint.get("healthz", "/healthz")
    .addSuccess(HttpApiSchema.NoContent)
)
```

Use this for root-level routes such as health checks that still belong in the
typed API.

## Typed Client Cross-Link

`HttpApiClient.make(api)` derives a client from the same `HttpApi` value used
by the server. That gives typed end-to-end behavior without a separate client
route table.

See [../http-client/05-derived-client.md](../http-client/05-derived-client.md)
for the client side of the same contract.

## Group Naming

Group names are public API names for generated clients. Use stable nouns such as
`"users"`, `"billing"`, or `"projects"`. Avoid deployment or implementation
terms like `"routes"` or `"controllers"`.

## Cross-references

See also: [01-overview.md](01-overview.md), [07-handlers.md](07-handlers.md), [08-error-responses.md](08-error-responses.md), [09-middleware.md](09-middleware.md)
