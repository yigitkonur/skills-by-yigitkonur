# Providing Services
Provide Effect services to CLI handlers with `Command.provide`, `provideEffect`, `provideSync`, and `transformHandler`.

## Handler Requirements

Command handlers are ordinary Effect programs. If a handler yields a service,
the command's requirement channel records that service until you provide it.

```typescript
import { Args, Command } from "@effect/cli"
import { Effect } from "effect"

class Greeter extends Effect.Tag("Greeter")<
  Greeter,
  { readonly greet: (name: string) => Effect.Effect<void> }
>() {}

const command = Command.make("hello", {
  name: Args.text({ name: "name" })
}, ({ name }) =>
  Effect.gen(function*() {
    const greeter = yield* Greeter
    yield* greeter.greet(name)
  })
)
```

This command cannot run until `Greeter` is provided.

## Command.provide

Use `Command.provide` for a normal layer:

```typescript
import { Args, Command } from "@effect/cli"
import { Effect, Layer } from "effect"

class Greeter extends Effect.Tag("Greeter")<
  Greeter,
  { readonly greet: (name: string) => Effect.Effect<void> }
>() {}

const GreeterLive = Layer.succeed(Greeter, {
  greet: (name) => Effect.logInfo(`Hello ${name}`)
})

const command = Command.make("hello", {
  name: Args.text({ name: "name" })
}, ({ name }) =>
  Effect.gen(function*() {
    const greeter = yield* Greeter
    yield* greeter.greet(name)
  })
).pipe(
  Command.provide(GreeterLive)
)
```

This keeps service construction outside the handler.

## Config-Dependent Layers

`Command.provide` can accept a function from parsed command config to a layer:

```typescript
import { Command, Options } from "@effect/cli"
import { Effect, Layer } from "effect"

class Reporter extends Effect.Tag("Reporter")<
  Reporter,
  { readonly report: (message: string) => Effect.Effect<void> }
>() {}

const command = Command.make("check", {
  prefix: Options.text("prefix").pipe(Options.withDefault("check"))
}, ({ prefix }) =>
  Effect.gen(function*() {
    const reporter = yield* Reporter
    yield* reporter.report("started")
  })
).pipe(
  Command.provide(({ prefix }) =>
    Layer.succeed(Reporter, {
      report: (message) => Effect.logInfo(`${prefix}: ${message}`)
    })
  )
)
```

Use this when CLI options select service configuration.

## provideEffect And provideSync

Use `provideEffect` when the service is computed effectfully:

```typescript
const commandWithEffect = command.pipe(
  Command.provideEffect(Reporter, Effect.succeed({
    report: Effect.logInfo
  }))
)
```

Use `provideSync` for an already-built service:

```typescript
const commandWithSync = command.pipe(
  Command.provideSync(Reporter, {
    report: Effect.logInfo
  })
)
```

Both combinators can also receive config-dependent functions.

## provideEffectDiscard

Use `provideEffectDiscard` for startup work that does not provide a service:

```typescript
const commandWithStartup = command.pipe(
  Command.provideEffectDiscard(({ prefix }) =>
    Effect.logInfo(`starting ${prefix}`)
  )
)
```

This is useful for telemetry startup, validation, or warm-up work.

## transformHandler

`Command.transformHandler` wraps the command handler effect:

```typescript
const observed = command.pipe(
  Command.transformHandler((effect, config) =>
    Effect.logInfo(`begin ${config.prefix}`).pipe(
      Effect.zipRight(effect),
      Effect.zipRight(Effect.logInfo(`end ${config.prefix}`))
    )
  )
)
```

Use it for cross-cutting behavior that should apply around the handler, such as
timing, structured logging, or request-scoped service injection.

## Node Context

Application-level platform services still belong at the runtime edge:

```typescript
import { NodeContext, NodeRuntime } from "@effect/platform-node"
import { Effect } from "effect"

Effect.suspend(() => cli(process.argv)).pipe(
  Effect.provide(NodeContext.layer),
  NodeRuntime.runMain
)
```

Command-provided services should be domain services. `NodeContext.layer` should
remain near `NodeRuntime.runMain`.

## Cross-references

See also: [02 Command](02-command.md), [08 Subcommands](08-subcommands.md), [10 Config Files](10-config-files.md), [11 Fallbacks](11-fallbacks.md)
