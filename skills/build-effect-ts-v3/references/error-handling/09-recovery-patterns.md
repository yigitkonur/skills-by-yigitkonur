# Recovery Patterns
Use these operators to recover with fallback effects, replacement values, replacement errors, or the first successful branch.

## orElse

`Effect.orElse` runs a fallback effect when the first effect fails:

```typescript
import { Data, Effect } from "effect"

class PrimaryUnavailable extends Data.TaggedError("PrimaryUnavailable")<{}> {}
class ReplicaUnavailable extends Data.TaggedError("ReplicaUnavailable")<{}> {}

const primary = Effect.fail(new PrimaryUnavailable({}))
const replica = Effect.fail(new ReplicaUnavailable({}))

const read = primary.pipe(
  Effect.orElse(() => replica)
)
```

Use `orElse` when the fallback is an effect and may have its own error or context requirements.

## orElseSucceed

`Effect.orElseSucceed` replaces any failure with a success value:

```typescript
import { Data, Effect } from "effect"

class PreferencesUnavailable extends Data.TaggedError(
  "PreferencesUnavailable"
)<{}> {}

const loadPreferences = Effect.fail(new PreferencesUnavailable({}))

const withDefaults = loadPreferences.pipe(
  Effect.orElseSucceed(() => ({ theme: "system" as const }))
)
```

Use it only when the default is correct for every remaining failure.

## orElseFail

`Effect.orElseFail` replaces any failure with a new failure:

```typescript
import { Data, Effect } from "effect"

class SqlUnavailable extends Data.TaggedError("SqlUnavailable")<{}> {}
class UserRepositoryUnavailable extends Data.TaggedError(
  "UserRepositoryUnavailable"
)<{}> {}

const query = Effect.fail(new SqlUnavailable({}))

const repositoryFailure = query.pipe(
  Effect.orElseFail(() => new UserRepositoryUnavailable({}))
)
```

Use it when all remaining lower-level errors map to one higher-level error and no effectful work is needed.

## firstSuccessOf

`Effect.firstSuccessOf` tries effects until one succeeds. If none succeed, the returned effect fails with the error type of the inputs.

```typescript
import { Data, Effect } from "effect"

class ReadUnavailable extends Data.TaggedError("ReadUnavailable")<{
  readonly source: string
}> {}

const primary = Effect.fail(new ReadUnavailable({ source: "primary" }))
const replica = Effect.succeed("value-from-replica")

const read = Effect.firstSuccessOf([primary, replica])
```

Use it for ordered fallback lists: primary, replica, cache, static default provider. Do not use it when failures need distinct handling before trying the next branch.

## catchTag plus retry policy

Recovery often needs tag-specific retry decisions:

```typescript
import { Data, Effect } from "effect"

class RateLimited extends Data.TaggedError("RateLimited")<{
  readonly retryAfterSeconds: number
}> {}

class Unauthorized extends Data.TaggedError("Unauthorized")<{}> {}

const request = Effect.fail(new RateLimited({ retryAfterSeconds: 2 })) as Effect.Effect<
  string,
  RateLimited | Unauthorized
>

const recovered = request.pipe(
  Effect.catchTag("RateLimited", (error) =>
    Effect.sleep(`${error.retryAfterSeconds} seconds`).pipe(
      Effect.as("retry-scheduled")
    )
  )
)
```

`Unauthorized` remains in the error channel because it has a different policy.

## Fallback policy table

| Operator | Reads original error? | Fallback can fail? | Use when |
|---|---:|---:|---|
| `orElse` | No | Yes | fallback is another effect |
| `orElseSucceed` | No | No | one default is valid for all failures |
| `orElseFail` | No | Yes | collapse remaining failures into one error |
| `catchTag` | Yes, narrowed | Yes | one tag has a specific policy |
| `catchTags` | Yes, narrowed by tag | Yes | multiple tags need dispatch |
| `catchAll` | Yes, broad | Yes | all remaining failures share one policy |

The broader the operator, the stronger the proof you need that one policy is correct.

## Avoid recovery that lies

Do not turn an authorization failure into an empty list just because the UI wants a value. Model the failure and let the boundary choose the response.

Do not turn all database failures into `NotFound`. Unavailability and absence are different recovery paths.

Do not retry validation failures. They are deterministic until input changes.

## Recovery placement

Place recovery where the policy is known:

- data access layer: cache fallback, replica fallback
- domain service: business default, compensating action
- API adapter: protocol status mapping
- runtime boundary: defect reporting and process policy

If the current layer cannot explain why a fallback is correct, let the typed failure continue upward.

## Combining with typed handlers

Fallback operators compose well after precise handlers:

```typescript
import { Data, Effect } from "effect"

class CacheMiss extends Data.TaggedError("CacheMiss")<{}> {}
class StoreUnavailable extends Data.TaggedError("StoreUnavailable")<{}> {}

const cached = Effect.fail(new CacheMiss({})) as Effect.Effect<
  string,
  CacheMiss | StoreUnavailable
>

const primary = Effect.succeed("fresh")

const read = cached.pipe(
  Effect.catchTag("CacheMiss", () => primary),
  Effect.orElseSucceed(() => "static")
)
```

Here the cache policy is handled first. The final static fallback is broad, but only after the remaining failure set has been intentionally reduced.

## Retry placement

Retry belongs before broad fallback when the failure category is transient. A fallback that runs first can hide the transient signal and prevent the retry policy from running.

Use tagged fields such as `retryAfterSeconds`, `operation`, or `source` to keep retry decisions explicit.

## Cross-references

See also: [04-catch-tag.md](04-catch-tag.md), [05-catch-tags.md](05-catch-tags.md), [06-catch-all.md](06-catch-all.md), [10-error-accumulation.md](10-error-accumulation.md), [12-error-taxonomy.md](12-error-taxonomy.md).
