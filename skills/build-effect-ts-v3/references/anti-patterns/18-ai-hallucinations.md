# AI Hallucination Correction Table
Use this table to replace common assistant-generated Effect mistakes with verified v3 patterns before editing application code.

## Symptom — Bad Code
```typescript
import { Effect } from "effect"

declare const fetchUser: (id: string) => Effect.Effect<{ readonly id: string }, Error>

const program = Effect.gen(function* () {
  const user = yield fetchUser("u-1")
  return user
})
```

## Why Bad
Effect has a broad surface area, so assistant output often blends ordinary TypeScript, old examples, and APIs from neighboring packages.
The most common hallucinations cluster around generators, runtime boundaries, layers, schema decoding, Option, and error recovery.
Do not accept an unfamiliar API until the v3 source or official docs confirm it.

## Fix — Correct Pattern
Use this wrong-to-right map as a first pass, then verify the final code against the positive reference.

## Wrong to Right Table
| Wrong assistant output | Correct v3 pattern | Check reference |
|---|---|---|
| `yield effect` inside `Effect.gen` | `yield* effect` | Generator delegation |
| `return Effect.fail(error)` in a branch | `return yield* Effect.fail(error)` | Control flow |
| Throwing a domain error | `Effect.fail(new TaggedDomainError(...))` | Typed failures |
| Running each step with runtime calls | Compose and run once at the edge | Runtime boundary |
| Service returns Promise after running Effect | Service returns Effect | Service design |
| Large `Effect.all(items.map(fn))` | `Effect.all(items.map(fn), { concurrency: n })` | Parallelism |
| `Promise.all` in workflow | `Effect.all` or `Effect.forEach` | Concurrency |
| Direct environment lookup | `Config.string` or `Config.redacted` | Config |
| Raw secret in log message | Redacted config plus structured Effect log | Secrets |
| `Effect.sync(() => asyncWork())` | `Effect.tryPromise` | Constructor |
| `Effect.succeed(promise)` | `Effect.promise` or `Effect.tryPromise` | Constructor |
| `Effect.promise` around rejecting API | `Effect.tryPromise` with catch mapper | Error channel |
| `Option.getOrThrow(option)` | `Option.match` | Option |
| Nullable domain field | `Option.Option<A>` in domain | Domain |
| Generic `Error` failure | Tagged domain error | Errors |
| One catch-all for known failures | `catchTag` or `catchTags` | Recovery |
| String matching on error message | Match on `_tag` | Recovery |
| Cast away requirements | Provide the required layer | Requirements |
| Cast away failures | Handle or expose the failure | Errors |
| Decode then broad cast | `Schema.decodeUnknown` or `Schema.decodeUnknownSync` | Schema |
| Legacy schema package import | `import { Schema } from "effect"` | Imports |
| Deep core module import by default | Barrel import from `effect` | Imports |
| Inline live layer in handler | Named layer constant | Layers |
| Expecting provider output after provide | Use `Layer.provideMerge` | Layers |
| Merging dependent layers | Use provide or provideMerge | Layers |
| Manual finalizer in Promise callback | `Effect.acquireRelease` with scope | Resources |
| Fork and forget in request path | Join or scope the fiber deliberately | Concurrency |
| Manual retry loop | `Effect.retry` with Schedule | Scheduling |
| Raw timer Promise sleep | `Effect.sleep` | Scheduling |
| Direct diagnostic output | Effect logging APIs | Observability |

## Source Verification Rule
Search `/tmp/effect-corpus/source/effect/packages/effect/src/Module.ts` first, then cached official docs, then community skills. If only a community skill mentions an API, do not use it until source confirms it.

## Cross-references
See also: [core generators](../core/05-generators.md), [layer composition gotchas](../services-layers/12-layer-composition-gotchas.md), [schema decoding](../schema/10-decoding.md), [v3 syntax quarantine](19-v4-syntax-do-not-use.md).
