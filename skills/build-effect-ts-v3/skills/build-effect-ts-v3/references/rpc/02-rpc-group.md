# RPC Groups
Use this when declaring an RPC contract with `Rpc.make` and `RpcGroup.make`.

`RpcGroup` is the contract container for `@effect/rpc`. A group is not just a
list of names. It is a typed registry of RPC definitions, including payload
schema, success schema, error schema, middleware, annotations, and prefixes.

The server and client should import the same group. Do not duplicate the contract
in a client file, server file, or transport-specific file.

## Minimal group

```typescript
import { Rpc, RpcGroup } from "@effect/rpc"
import { Schema } from "effect"

class Todo extends Schema.Class<Todo>("Todo")({
  id: Schema.String,
  title: Schema.String,
  completed: Schema.Boolean
}) {}

class TodoNotFound extends Schema.TaggedError<TodoNotFound>()("TodoNotFound", {
  id: Schema.String
}) {}

export class TodoApi extends RpcGroup.make(
  Rpc.make("Todos.Get", {
    payload: { id: Schema.String },
    success: Todo,
    error: TodoNotFound
  }),
  Rpc.make("Todos.Create", {
    payload: { title: Schema.String },
    success: Todo,
    error: Schema.Never
  })
) {}
```

The class form gives the group a stable exported value and type.

## `Rpc.make`

`Rpc.make(tag, options)` creates one remote method. In v3 its relevant options
are:

| Option | Purpose |
|---|---|
| `payload` | Request schema or struct fields. |
| `success` | Successful response schema. |
| `error` | Expected failure schema. |
| `stream` | Converts the success schema into a streaming success. |
| `defect` | Custom defect schema for encoded exits. |
| `primaryKey` | Builds a payload class with a primary key for caching/dedup. |

Always write all three logical slots in examples, even when the value is
`Schema.Never`. That keeps the RPC contract inspectable.

```typescript
const HealthCheck = Rpc.make("Health.Check", {
  payload: Schema.Void,
  success: Schema.Literal("ok"),
  error: Schema.Never
})
```

## Payload schemas

Payload can be a full schema:

```typescript
class SearchPayload extends Schema.Class<SearchPayload>("SearchPayload")({
  query: Schema.String,
  limit: Schema.Number.pipe(Schema.between(1, 100))
}) {}

const Search = Rpc.make("Search", {
  payload: SearchPayload,
  success: Schema.Array(Schema.String),
  error: Schema.Never
})
```

Payload can also be struct fields. `Rpc.make` wraps those fields in
`Schema.Struct`:

```typescript
const SearchByFields = Rpc.make("SearchByFields", {
  payload: {
    query: Schema.String,
    limit: Schema.Number
  },
  success: Schema.Array(Schema.String),
  error: Schema.Never
})
```

Use schema classes for shared payloads and field objects for small request
bodies that belong only to the RPC.

## Success and error schemas

Success should be the value the client wants after transport and schema decoding.
Error should be typed expected failure, not defects or infrastructure failures.

```typescript
class ValidationError extends Schema.TaggedError<ValidationError>()(
  "ValidationError",
  { field: Schema.String, message: Schema.String }
) {}

const RenameTodo = Rpc.make("Todos.Rename", {
  payload: {
    id: Schema.String,
    title: Schema.String
  },
  success: Todo,
  error: ValidationError
})
```

Transport failures still appear as client-side failures from `RpcClient.make`;
they are not part of the domain error schema.

## Dotted tags and client shape

RPC tags are strings. Dotted tags create a grouped client object:

```typescript
export class TodoApi extends RpcGroup.make(
  Rpc.make("Todos.Get", {
    payload: { id: Schema.String },
    success: Todo,
    error: TodoNotFound
  }),
  Rpc.make("Admin.Reindex", {
    payload: Schema.Void,
    success: Schema.Void,
    error: Schema.Never
  })
) {}
```

The inferred client has `client.Todos.Get(...)` and
`client.Admin.Reindex(...)`. Tags without a dot become direct methods on the
client.

## Add, merge, and prefix

`RpcGroup.make` accepts one or more RPCs. Existing groups can be extended:

```typescript
const TodoReads = RpcGroup.make(
  Rpc.make("Get", {
    payload: { id: Schema.String },
    success: Todo,
    error: TodoNotFound
  })
)

const TodoWrites = RpcGroup.make(
  Rpc.make("Create", {
    payload: { title: Schema.String },
    success: Todo,
    error: Schema.Never
  })
)

export class TodoApi extends TodoReads
  .merge(TodoWrites)
  .prefix("Todos.") {}
```

Prefer direct `RpcGroup.make` for small APIs. Use `merge` and `prefix` when a
large API has independently owned subdomains.

## From tagged requests

`Rpc.fromTaggedRequest` builds an RPC from a schema that already carries `_tag`,
`success`, and `failure`. Use it when an existing Effect request model is the
source of truth.

```typescript
class GetTodo extends Schema.TaggedRequest<GetTodo>()("GetTodo", {
  failure: TodoNotFound,
  success: Todo,
  payload: { id: Schema.String }
}) {}

export class TodoApi extends RpcGroup.make(
  Rpc.fromTaggedRequest(GetTodo)
) {}
```

If the project is already using `Schema.TaggedRequest`, this avoids maintaining
two request declarations.

## Implementing handlers from a group

`group.toLayer` requires one handler per RPC tag:

```typescript
import { Effect } from "effect"

const TodoHandlers = TodoApi.toLayer({
  "Todos.Get": ({ id }) =>
    id === "1"
      ? Effect.succeed(new Todo({ id, title: "Write docs", completed: false }))
      : Effect.fail(new TodoNotFound({ id })),
  "Todos.Create": ({ title }) =>
    Effect.succeed(new Todo({ id: "2", title, completed: false }))
})
```

Handler keys use the RPC tag, not the dotted client path. The client path is
derived later.

## Implementing one handler

`toLayerHandler` is useful when handlers live in separate modules:

```typescript
const GetTodoLive = TodoApi.toLayerHandler("Todos.Get", ({ id }) =>
  id === "1"
    ? Effect.succeed(new Todo({ id, title: "Write docs", completed: false }))
    : Effect.fail(new TodoNotFound({ id }))
)
```

The resulting layer provides only `Rpc.Handler<"Todos.Get">`. Merge handler
layers before providing them to the server.

## Annotations

Groups and RPCs can carry annotations:

- `group.annotate(tag, value)` annotates the group.
- `group.annotateRpcs(tag, value)` annotates RPCs already in the group.
- `rpc.annotate(tag, value)` annotates one RPC.

Annotations are metadata for middleware, tracing, or framework integration.
They do not replace schemas.

## Group checklist

Before serving a group, verify stable tags, explicit payload/success/error
schemas, modeled domain errors, intentional dotted tag shape, and middleware
declarations before handlers are written.

## Cross-references

See also: [01-overview.md](01-overview.md), [03-rpc-server.md](03-rpc-server.md), [05-rpc-middleware.md](05-rpc-middleware.md), [06-rpc-streaming.md](06-rpc-streaming.md)
