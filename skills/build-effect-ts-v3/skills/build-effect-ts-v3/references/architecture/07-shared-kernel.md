# Shared Kernel
Share stable schemas, branded ids, and public errors deliberately; keep adapters and runtime wiring out of the shared package.

## What The Shared Kernel Is

A shared kernel is the small domain contract multiple packages agree to use.
In Effect v3 it usually contains:

- branded ids;
- schema classes and request or response schemas;
- public tagged errors;
- pure domain helpers;
- protocol-neutral constants.

It should not contain SQL clients, HTTP handlers, CLI commands, runtime launch,
or production layer composition.

## Good Shared Kernel Layout

```text
packages/domain/src/
  ids.ts
  User.ts
  Account.ts
  public-errors.ts
  requests.ts
  responses.ts
```

Then each adapter imports the same contracts:

```text
packages/http-server      -> packages/domain
packages/cli              -> packages/domain
packages/sql-adapter      -> packages/domain
packages/application      -> packages/domain
```

The domain package does not import any of those packages.

## Branded Ids

```typescript
import { Schema } from "effect"

export const AccountId = Schema.String.pipe(Schema.brand("AccountId"))
export type AccountId = typeof AccountId.Type

export const UserId = Schema.String.pipe(Schema.brand("UserId"))
export type UserId = typeof UserId.Type
```

Brands prevent accidental cross-wiring between ids that share a primitive
representation.

## Stable Entity Schemas

```typescript
import { Option, Schema } from "effect"

export const Email = Schema.NonEmptyTrimmedString.pipe(Schema.brand("Email"))
export type Email = typeof Email.Type

export class User extends Schema.Class<User>("User")({
  id: UserId,
  accountId: AccountId,
  email: Email,
  displayName: Schema.Option(Schema.NonEmptyTrimmedString)
}) {}
```

If persistence needs extra fields, create adapter-local row schemas instead of
polluting the shared entity.

## Boundary Request And Response Schemas

```typescript
import { Schema } from "effect"

export class RegisterUserRequest
  extends Schema.Class<RegisterUserRequest>("RegisterUserRequest")({
    accountId: AccountId,
    email: Email
  })
{}

export class UserResponse extends Schema.Class<UserResponse>("UserResponse")({
  id: UserId,
  email: Email
}) {}
```

HTTP and CLI adapters can decode into the same request schema. Use cases can
accept either the schema type or a narrower domain command type.

## Shared Public Errors

```typescript
import { Schema } from "effect"

export class PublicNotFound extends Schema.TaggedError<PublicNotFound>()(
  "PublicNotFound",
  { resource: Schema.String }
) {}

export class PublicConflict extends Schema.TaggedError<PublicConflict>()(
  "PublicConflict",
  { message: Schema.String }
) {}
```

Share public errors only when multiple adapters expose the same contract. Keep
adapter-only details near the adapter.

## What Not To Share

Do not put these in the shared kernel:

- `SqlClient.SqlClient` usage;
- `NodeRuntime.runMain`;
- `HttpApiBuilder.serve`;
- `Layer.launch`;
- concrete repository layers;
- test-only layers;
- feature-specific orchestration that changes often.

Those belong in application, adapter, platform, or test packages.

## Versioning Pressure

The shared kernel is expensive to change because every adapter consumes it.
Prefer additive changes:

- add a new field with a schema-level default only when the boundary supports it;
- add a new public error without removing the old one immediately;
- add a new request schema version when external clients depend on the old one;
- keep row schemas adapter-local so migrations do not force public schema churn.

## Cross-Package Imports

A healthy monorepo dependency graph looks like this:

```text
domain
  ↑
application
  ↑        ↑
sql-adapter http-server cli worker
```

The app may have multiple composition roots. Each root wires the same
application ports to different adapters.

## Shared Kernel Tests

Test decoders and error constructors without platform layers:

```typescript
import { Effect, Schema } from "effect"

export const decodeUserResponse = (input: unknown) =>
  Schema.decodeUnknown(UserResponse)(input)

export const verifyUserResponse = Effect.gen(function* () {
  const response = yield* decodeUserResponse({
    id: "user-1",
    email: "a@example.com"
  })
  return response.id
})
```

Adapter tests should verify that SQL rows, HTTP payloads, or CLI args decode
into this shared contract.

## Cross-references

See also: [domain-driven-design.md](02-domain-driven-design.md), [error-boundary-design.md](06-error-boundary-design.md), [../schema/03-schema-class.md](../schema/03-schema-class.md), [../schema/06-branded-types.md](../schema/06-branded-types.md), [../http-server/02-defining-endpoints.md](../http-server/02-defining-endpoints.md).
