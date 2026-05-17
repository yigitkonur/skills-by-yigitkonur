# Context Reference
Use `Context.Reference` for a service slot with a runtime default that can still be overridden.

## What It Is

`Context.Reference` is a tag with a `defaultValue`. In v3.21.2 it is present in `Context.ts`, marked `@since 3.11.0` and experimental.

```typescript
import { Context, Effect } from "effect"

class RequestId extends Context.Reference<RequestId>()(
  "app/RequestId",
  { defaultValue: () => "unknown-request" }
) {}

const program = Effect.gen(function* () {
  const requestId = yield* RequestId
  return requestId
})
```

`program` can run without a layer because the reference supplies a default.

## Override At The Edge

The same tag can be overridden with `Effect.provideService`.

```typescript
import { Effect } from "effect"

const withRequest = program.pipe(
  Effect.provideService(RequestId, "req-123")
)
```

This is useful for request metadata, deterministic test values, or defaults that are genuinely safe.

## When It Fits

| Use case | Why it fits |
|---|---|
| Request id fallback | Unknown is safer than failure in generic logs |
| Test seed | Default deterministic seed, override per test |
| Optional tuning parameter | The application has a sane default |
| Lightweight context value | No acquisition or dependency graph needed |

## When It Does Not Fit

Do not use `Context.Reference` to hide required infrastructure.

| Bad fit | Better tool |
|---|---|
| Database connection | `Layer.scoped` |
| API credentials | `Config` plus `Layer.effect` |
| Payment gateway | `Context.Tag` or `Effect.Service` |
| Per-request authenticated user | Explicit tag provided by middleware |

The default should be safe and unsurprising. If absence should fail, use a normal tag.

## Layer Interop

References can still be provided by a layer when you want common wiring.

```typescript
import { Layer } from "effect"

const RequestIdTest = Layer.succeed(RequestId, "test-request")
```

This lets test suites compose a reference with other layers.

## Default Value Discipline

The default value is executed when the reference is read and no explicit value exists in the context. Keep it cheap, deterministic enough for the use case, and free of hidden resource acquisition.

Good default:

```typescript
class RetryLimit extends Context.Reference<RetryLimit>()(
  "app/RetryLimit",
  { defaultValue: () => 3 }
) {}
```

Bad default shape: opening a socket, reading external configuration, or creating a mutable singleton. Those are layer responsibilities.

## Request Scope Pattern

References can model values that have a fallback but are often overridden by middleware.

```typescript
class TenantId extends Context.Reference<TenantId>()(
  "app/TenantId",
  { defaultValue: () => "public" }
) {}

const tenantProgram = program.pipe(
  Effect.provideService(TenantId, "tenant-a")
)
```

If the tenant must always be authenticated, use a normal tag instead. A reference default should not make invalid states look valid.

## Experimental Status

`Context.Reference` is available in v3.21.2, but the source marks it experimental. Use it deliberately and prefer ordinary tags for core infrastructure contracts.

## Readability Rule

Name references after the value they carry, not after the mechanism.

| Clear | Avoid |
|---|---|
| `RequestId` | `RequestIdReference` |
| `RetryLimit` | `DefaultRetryLimit` |
| `TenantId` | `TenantContext` |

Call sites should read like ordinary service access:

```typescript
const tenantProgram = Effect.gen(function* () {
  const tenantId = yield* TenantId
  return tenantId
})
```

The fact that a default exists is a definition detail.

## Cross-references

See also: [services-layers/02-context-tag.md](../services-layers/02-context-tag.md), [services-layers/04-context-vs-effect-service.md](../services-layers/04-context-vs-effect-service.md), [services-layers/06-layer-succeed.md](../services-layers/06-layer-succeed.md), [services-layers/15-effect-provide.md](../services-layers/15-effect-provide.md).
