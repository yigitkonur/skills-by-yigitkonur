# Spy Layers
Use spy layers when tests must assert how a service was called while keeping dependency injection explicit.

## Recording Calls

A spy is just a service implementation that records calls in Effect state.

```typescript
import { expect, it } from "@effect/vitest"
import { Context, Effect, Layer, Ref } from "effect"

class Mailer extends Context.Tag("test/Mailer")<
  Mailer,
  {
    readonly send: (address: string, body: string) => Effect.Effect<void>
    readonly sent: Effect.Effect<ReadonlyArray<string>>
  }
>() {}

const MailerSpy = Layer.effect(
  Mailer,
  Ref.make<ReadonlyArray<string>>([]).pipe(
    Effect.map((calls) => ({
      send: (address, _body) => calls.update((all) => [...all, address]),
      sent: calls.get
    }))
  )
)
```

The spy is still a normal layer. It does not patch imports or depend on global
test state.

## Assert Calls

```typescript
import { expect, it } from "@effect/vitest"
import { Effect } from "effect"

const welcome = (address: string) =>
  Effect.gen(function* () {
    const mailer = yield* Mailer
    yield* mailer.send(address, "Welcome")
  })

it.effect("records sent mail", () =>
  Effect.gen(function* () {
    yield* welcome("ada@example.com")

    const mailer = yield* Mailer
    const sent = yield* mailer.sent

    expect(sent).toEqual(["ada@example.com"])
  }).pipe(Effect.provide(MailerSpy))
)
```

Assertions happen through service methods. The test does not reach into private
variables.

## Count Calls

Use a counter when the arguments do not matter.

```typescript
import { Context, Effect, Layer, Ref } from "effect"

class Notifications extends Context.Tag("test/Notifications")<
  Notifications,
  {
    readonly publish: (message: string) => Effect.Effect<void>
    readonly count: Effect.Effect<number>
  }
>() {}

const NotificationsSpy = Layer.effect(
  Notifications,
  Ref.make(0).pipe(
    Effect.map((count) => ({
      publish: (_message) => count.update((n) => n + 1),
      count: count.get
    }))
  )
)
```

Use arrays for argument assertions and counters for simple interaction counts.

## Model Failures In Spies

Spies can record a call and then fail with a typed error.

```typescript
import { Data, Effect } from "effect"

class MailRejected extends Data.TaggedError("MailRejected")<{
  readonly address: string
}> {}

const rejectingSend = (address: string, _body: string) =>
  Effect.fail(new MailRejected({ address }))
```

This tests both the interaction and the program's typed error path.

## Keep Spies Focused

A spy should answer one test question:

| Question | Spy shape |
|---|---|
| Was it called? | Counter |
| What arguments were used? | Array of records |
| What order happened? | Array with labels |
| Did it fail after recording? | Record then typed failure |

If a spy grows many configuration switches, split it into smaller named layers.

## Ordering Assertions

```typescript
import { Context, Effect, Layer, Ref } from "effect"

class Events extends Context.Tag("test/Events")<
  Events,
  {
    readonly emit: (name: string) => Effect.Effect<void>
    readonly all: Effect.Effect<ReadonlyArray<string>>
  }
>() {}

const EventsSpy = Layer.effect(
  Events,
  Ref.make<ReadonlyArray<string>>([]).pipe(
    Effect.map((events) => ({
      emit: (name) => events.update((all) => [...all, name]),
      all: events.get
    }))
  )
)
```

For concurrent code, avoid assuming order unless the program enforces it. Assert
sets or counts when scheduling is intentionally parallel.

## Source Anchors

Spy layers rely on the same v3 layer tools as other test doubles:
`Layer.effect`, `Ref.make`, `Ref.update`, and `Ref.get`. They compose with
`Effect.provide` and `it.layer` like any other layer.

## Cross-references

See also: [08-test-layers.md](08-test-layers.md), [09-stateful-test-layers.md](09-stateful-test-layers.md), [11-testing-errors.md](11-testing-errors.md), [13-testing-concurrency.md](13-testing-concurrency.md).
