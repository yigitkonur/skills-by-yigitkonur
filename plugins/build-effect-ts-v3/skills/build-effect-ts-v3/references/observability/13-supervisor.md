# Supervisor
Use supervisors to observe fiber lifecycles when logs, metrics, and spans need runtime-level fiber information.

## Core APIs

| API | Use for |
|---|---|
| `Supervisor.track` | track child runtime fibers |
| `Supervisor.fibersIn(ref)` | track fibers in a provided mutable ref |
| `Supervisor.fromEffect(effect)` | expose an effectful supervisor value |
| `Supervisor.addSupervisor(supervisor)` | install a supervisor as a layer |
| `Effect.supervised(supervisor)` | supervise child fibers in one effect |
| `Supervisor.AbstractSupervisor` | implement custom lifecycle hooks |

Supervisors are lower-level than logs, metrics, and traces. Use them when fiber
lifecycle itself is the thing to observe.

## Track Child Fibers

```typescript
import { Effect, Fiber, Supervisor } from "effect"

const program = Effect.gen(function* () {
  const supervisor = yield* Supervisor.track

  yield* Effect.sleep("1 second").pipe(
    Effect.fork,
    Effect.supervised(supervisor)
  )

  const fibers = yield* supervisor.value
  yield* Effect.logInfo("tracked fibers", {
    count: fibers.length
  })

  yield* Effect.forEach(fibers, Fiber.interrupt, { concurrency: 4 })
})
```

Use this for diagnostics, not as the normal way to manage child fibers.

## Install with a Layer

```typescript
import { Layer, Supervisor } from "effect"

declare const supervisor: Supervisor.Supervisor<unknown>

const SupervisorLive = Supervisor.addSupervisor(supervisor)
```

Layer installation makes supervision part of runtime wiring, similar to logger
and tracer policy.

## Custom Supervisor

Extend `Supervisor.AbstractSupervisor` for lifecycle hooks.

```typescript
import { Context, Effect, Exit, Fiber, Option, Supervisor } from "effect"

class CountingSupervisor extends Supervisor.AbstractSupervisor<number> {
  private started = 0
  private ended = 0

  readonly value = Effect.sync(() => this.started - this.ended)

  onStart<A, E, R>(
    _context: Context.Context<R>,
    _effect: Effect.Effect<A, E, R>,
    _parent: Option.Option<Fiber.RuntimeFiber<unknown, unknown>>,
    _fiber: Fiber.RuntimeFiber<A, E>
  ): void {
    this.started = this.started + 1
  }

  onEnd<A, E>(
    _value: Exit.Exit<A, E>,
    _fiber: Fiber.RuntimeFiber<A, E>
  ): void {
    this.ended = this.ended + 1
  }
}
```

Custom supervisors should stay small. If the hook needs effectful export, write
to a safe in-memory structure and expose the data through `value`.

## Metrics from Supervisor Values

```typescript
import { Effect, Metric, Supervisor } from "effect"

const activeFibers = Metric.gauge("active_fibers", {
  description: "Currently supervised fibers"
})

const reportActiveFibers = Effect.gen(function* () {
  const supervisor = yield* Supervisor.track
  const fibers = yield* supervisor.value
  yield* Metric.set(activeFibers, fibers.length)
})
```

For continuous reporting, run a scheduled reporter in the application runtime.

## When to Use Supervisors

Use supervisors for:

- observing child fiber counts
- diagnosing leaked or stuck fibers
- runtime-level dashboards
- test assertions about forked work
- integrating fiber lifecycle with platform observability

Do not use supervisors for normal business workflow state. Domain state belongs
in services, refs, queues, streams, or durable stores.

## Supervisor vs Tracing

| Need | Use |
|---|---|
| operation timing | span |
| child fiber count | supervisor |
| request context | log annotation or span attribute |
| lifecycle debugging | supervisor |
| distributed call graph | tracing |

Supervisors observe fibers. Tracers observe operations.

## Anti-patterns

- Using supervisors to coordinate normal domain logic.
- Performing blocking export work directly inside supervisor hooks.
- Treating supervised fiber arrays as a durable registry.
- Installing custom supervisors in library code.
- Replacing spans with fiber lifecycle events.

## Review Checklist

- Supervisor use is justified by fiber lifecycle observability.
- Application code installs supervisors through layers or narrow `Effect.supervised` regions.
- Custom hooks are synchronous and small.
- Metrics derived from supervisor values are reported by effects.
- Tracing still describes operation structure.

## Cross-references

See also: [tracing basics](06-tracing-basics.md), [span scoped](07-span-scoped.md), [counter and gauge metrics](08-metrics-counter-gauge.md), [OpenTelemetry setup](11-opentelemetry-setup.md).
