# Atom.make
Use `Atom.make` for plain writable state, synchronous derived state, effectful queries, and stream-backed latest-value state.

## Core Rule

`Atom.make` is overloaded.
The argument you pass determines the atom shape.

| Input | Output shape |
|---|---|
| value | writable atom of that value |
| `(get) => value` | readonly derived atom |
| `Effect<A, E, Scope | AtomRegistry>` | readonly `Result.Result<A, E>` atom |
| `(get) => Effect<A, E, Scope | AtomRegistry>` | effectful derived result atom |
| `Stream<A, E, AtomRegistry>` | readonly latest-value result atom |

Keep examples simple.
Use runtime atoms for service requirements beyond the atom runtime and registry.

## Writable State

Plain values create writable atoms.
The setter accepts a replacement value or an updater function through React
hooks.

```typescript
import { Atom } from "@effect-atom/atom-react"

type Filter = "all" | "open" | "done"

export const filterAtom = Atom.make<Filter>("all").pipe(
  Atom.keepAlive
)
```

Use this for state that has no Effect execution path.
If the state is shared beyond one screen, keep it alive.

## Derived State With get

The `get` function reads other atoms and tracks dependencies.
When a dependency changes, the derived atom recomputes.

```typescript
import { Atom } from "@effect-atom/atom-react"

type Todo = {
  readonly id: string
  readonly title: string
  readonly done: boolean
}

export const todosAtom = Atom.make<ReadonlyArray<Todo>>([]).pipe(
  Atom.keepAlive
)

export const openTodosAtom = Atom.make((get) =>
  get(todosAtom).filter((todo) => !todo.done)
)

export const openCountAtom = Atom.make((get) =>
  get(openTodosAtom).length
)
```

Derived atoms should stay pure.
Put event listeners, timers, and resource cleanup in side-effect atoms with
finalizers.

## Derived State With Atom.map

Use `Atom.map` for a single dependency and simple transformation.

```typescript
import { Atom } from "@effect-atom/atom-react"

const countAtom = Atom.make(0).pipe(Atom.keepAlive)

export const doubledCountAtom = Atom.map(
  countAtom,
  (count) => count * 2
)
```

Use `Atom.make((get) => ...)` when multiple dependencies are read or the
derivation needs branching.

## Effectful Atom

Passing an `Effect` creates a result atom.
The atom runtime runs the effect when the atom is mounted.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect } from "effect"

export const currentTimeAtom = Atom.make(
  Effect.sync(() => new Date())
)
```

A component reading this atom receives `Result.Result<Date>`, not `Date`.
Render initial, failure, and success states explicitly.

## Effectful Derived Atom

Use the function overload when the effect depends on other atoms.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect } from "effect"

const userIdAtom = Atom.make("u-1").pipe(Atom.keepAlive)

const greetingAtom = Atom.make((get) =>
  Effect.succeed(`hello:${get(userIdAtom)}`)
)
```

This rebuilds when `userIdAtom` changes.
If the effect has external service requirements, prefer `runtime.atom`.

## Reading Result Atoms Inside Effects

Effect Atom context supports reading a result atom from inside another effect.
Use this when a derived effect needs a successful value from another result
atom.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect } from "effect"

const baseAtom = Atom.make(Effect.succeed(40))

const plusTwoAtom = Atom.make(
  Effect.fnUntraced(function* (get: Atom.Context) {
    const value = yield* get.result(baseAtom)
    return value + 2
  })
)
```

The dependency remains in the atom graph.
The failure channel stays typed by Effect.

## Initial Values

Effect and stream atoms can receive an initial success value.
Use it when stale-but-usable data is better than a blank initial state.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect } from "effect"

const profileAtom = Atom.make(
  Effect.succeed({ id: "u-1", name: "Ada" }),
  { initialValue: { id: "pending", name: "Loading" } }
)
```

Initial values are not a substitute for loading UI.
They are a previous usable value for the result.

## Service-Dependent Queries

Use `Atom.runtime(layer)` when the effect needs a service.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect } from "effect"

class ClockService extends Effect.Service<ClockService>()("app/Clock", {
  succeed: {
    now: Effect.sync(() => new Date())
  }
}) {}

const runtime = Atom.runtime(ClockService.Default)

export const nowAtom = runtime.atom(
  Effect.gen(function* () {
    const clock = yield* ClockService
    return yield* clock.now
  })
)
```

The runtime atom builds and memoizes the service layer under Atom ownership.

## Do Not Create Atoms In Components

This pattern creates a new atom identity during render:

```typescript
import { Atom, useAtomValue } from "@effect-atom/atom-react"

export function BadCounter() {
  const countAtom = Atom.make(0)
  return useAtomValue(countAtom)
}
```

Move the atom to module scope or use an `Atom.family` keyed outside the render
loop.

## Selection Checklist

- Value atom for simple writable state.
- `Atom.map` for one-source mapping.
- `Atom.make((get) => ...)` for multi-source synchronous derivation.
- `Atom.make(effect)` for pure Effect queries.
- `runtime.atom(effect)` when services are required.
- `Atom.keepAlive` for global state.
- `Result.builder` or `Result.match` for effectful atom values.

## Cross-references

See also: [01 Overview](01-overview.md), [03 Atom Families](03-atom-families.md), [05 React Hooks](05-react-hooks.md), [06 Result Builder](06-result-builder.md), [11 Runtime Bridge](11-effect-runtime-bridge.md).
