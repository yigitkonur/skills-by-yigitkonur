# Stateful Test Layers
Use `Layer.effect` with `Ref` when a test double needs isolated mutable state.

## Why State Belongs In The Layer

A stateful fake should allocate its state when the layer is built. That makes
the sharing boundary explicit.

```typescript
import { expect, it } from "@effect/vitest"
import { Context, Effect, Layer, Option, Ref } from "effect"

type User = {
  readonly id: string
  readonly name: string
}

class UserRepo extends Context.Tag("test/UserRepo")<
  UserRepo,
  {
    readonly find: (id: string) => Effect.Effect<Option.Option<User>>
    readonly save: (user: User) => Effect.Effect<void>
  }
>() {}

const UserRepoStateful = Layer.effect(
  UserRepo,
  Ref.make(new Map<string, User>()).pipe(
    Effect.map((store) => ({
      find: (id) =>
        store.get.pipe(
          Effect.map((map) => Option.fromNullable(map.get(id)))
        ),
      save: (user) =>
        store.update((map) => new Map(map).set(user.id, user))
    }))
  )
)
```

The `Ref` is constructed inside the layer, not in a top-level variable.

## Use It In A Test

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Option } from "effect"

it.effect("saves and finds users", () =>
  Effect.gen(function* () {
    const repo = yield* UserRepo

    yield* repo.save({ id: "u1", name: "Ada" })
    const user = yield* repo.find("u1")

    expect(Option.isSome(user)).toBe(true)
    if (Option.isSome(user)) {
      expect(user.value.name).toBe("Ada")
    }
  }).pipe(Effect.provide(UserRepoStateful))
)
```

Providing the layer inside the test body gives this test its own store. Using
`it.layer(UserRepoStateful)` would share the store across the suite.

## Fresh State Per Test

Prefer per-test provision for stateful unit tests:

```typescript
import { expect, it } from "@effect/vitest"
import { Effect } from "effect"

it.effect("starts empty", () =>
  Effect.gen(function* () {
    const repo = yield* UserRepo
    const missing = yield* repo.find("u1")

    expect(Option.isNone(missing)).toBe(true)
  }).pipe(Effect.provide(UserRepoStateful))
)
```

Every run of `Effect.provide(UserRepoStateful)` constructs a fresh layer for
that test execution.

## Shared State Per Suite

Use `it.layer` only when shared state is intentional.

```typescript
import { expect, it } from "@effect/vitest"
import { Effect } from "effect"

it.layer(UserRepoStateful)("shared user repo", (it) => {
  it.effect("writes shared data", () =>
    Effect.gen(function* () {
      const repo = yield* UserRepo
      yield* repo.save({ id: "shared", name: "Lin" })
      expect(true).toBe(true)
    })
  )
})
```

Shared state can be useful for integration-style suites, but it makes test
ordering more important. Keep unit tests isolated unless sharing is the point.

## Model Failures Too

Stateful fakes can still return typed failures.

```typescript
import { Data, Effect } from "effect"

class DuplicateUser extends Data.TaggedError("DuplicateUser")<{
  readonly id: string
}> {}

const saveUnique = (user: User) =>
  Effect.gen(function* () {
    const repo = yield* UserRepo
    const existing = yield* repo.find(user.id)

    if (Option.isSome(existing)) {
      return yield* Effect.fail(new DuplicateUser({ id: user.id }))
    }

    yield* repo.save(user)
  })
```

Do not throw from the fake. Preserve typed failures so tests exercise the same
error handling path as production.

## Keep State Observable When Needed

If the test needs to inspect internal state, expose a service method for it.

```typescript
import { Context, Effect, Layer, Ref } from "effect"

class Counter extends Context.Tag("test/Counter")<
  Counter,
  {
    readonly increment: Effect.Effect<number>
    readonly snapshot: Effect.Effect<number>
  }
>() {}

const CounterTest = Layer.effect(
  Counter,
  Ref.make(0).pipe(
    Effect.map((ref) => ({
      increment: Ref.updateAndGet(ref, (n) => n + 1),
      snapshot: ref.get
    }))
  )
)
```

Observation methods are preferable to reaching around the service tag with
external mutable variables.

## Source Anchors

`Layer.effect` constructs a service through an Effect. `Ref.make`,
`Ref.update`, `Ref.updateAndGet`, and `Ref.get` are v3 tools for deterministic
in-memory mutable state in tests.

## Cross-references

See also: [05-it-layer.md](05-it-layer.md), [08-test-layers.md](08-test-layers.md), [10-spy-layers.md](10-spy-layers.md), [13-testing-concurrency.md](13-testing-concurrency.md).
