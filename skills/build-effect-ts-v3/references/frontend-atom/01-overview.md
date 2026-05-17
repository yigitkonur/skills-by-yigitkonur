# Frontend Atom Overview
Use Effect Atom when React state must stay reactive while preserving Effect services, typed failures, interruption, and runtime ownership.

## What Effect Atom Solves

`@effect-atom/atom-react` is the React binding for the Effect Atom packages.
It gives React components a small hook surface over Effect-native atoms.

The model is close to Jotai in ergonomics:

- atoms are values defined outside components
- components read atoms with hooks
- writes go through setters
- derived atoms recompute from dependencies
- effectful atoms expose `Result.Result<A, E>`
- runtime atoms provide services through a `Layer`

The important difference is that the asynchronous path remains Effect.
An atom can run an `Effect`, a `Stream`, or a function that reads other atoms.
The runtime owns cancellation, scopes, typed errors, and service requirements.

## Package Shape

React apps normally import from `@effect-atom/atom-react`.
That package re-exports the core Atom modules and adds React hooks.

```typescript
import {
  Atom,
  Result,
  useAtom,
  useAtomMount,
  useAtomSet,
  useAtomValue
} from "@effect-atom/atom-react"
import { Effect } from "effect"
```

Use the package barrel in application examples unless an existing codebase
already standardizes on lower-level package entry points.

## Version Notes

The source metadata on main lists:

| Package | Version in source | Peer constraints |
|---|---:|---|
| `@effect-atom/atom` | `0.5.3` | `effect` `^3.19.15` |
| `@effect-atom/atom-react` | `0.5.0` | `effect` `^3.19`, `react` `>=18 <20` |

The mission target is still Effect v3.
Do not mix in v4-only Effect APIs when writing Atom examples.

## Lifecycle

By default, atoms are disposable.
If no component or registry mount is using an atom, its value can be reset and
resources can be finalized.

That default is useful for screen-local effects and wrong for shared app state.

For long-lived global state, always pipe through `Atom.keepAlive`.

```typescript
import { Atom } from "@effect-atom/atom-react"

const themeAtom = Atom.make<"light" | "dark">("dark").pipe(
  Atom.keepAlive
)
```

## Define Atoms Outside Components

Atoms are identity-based.
If a component creates an atom during render, each render can create a new
identity and lose subscriptions, cached values, and family reuse.

Define atoms at module scope or inside a stable factory that is not called by
React render.

```typescript
import { Atom, useAtomSet, useAtomValue } from "@effect-atom/atom-react"

const countAtom = Atom.make(0).pipe(Atom.keepAlive)

export function Counter() {
  const count = useAtomValue(countAtom)
  const setCount = useAtomSet(countAtom)

  return {
    count,
    increment: () => setCount((current) => current + 1)
  }
}
```

The component uses the atom.
It does not construct it.

## Result Values

Effectful atoms return a `Result.Result`.
A result represents:

- `Initial`: no success value yet
- `Success`: latest successful value
- `Failure`: typed failure cause, possibly with previous success
- `waiting`: background work is still in flight

Render result atoms with `Result.builder` when the UI needs a clear state map.

```typescript
import { Atom, Result, useAtomValue } from "@effect-atom/atom-react"
import { Effect } from "effect"

const greetingAtom = Atom.make(
  Effect.succeed("ready")
).pipe(Atom.keepAlive)

export function GreetingStatus() {
  const result = useAtomValue(greetingAtom)

  return Result.builder(result)
    .onInitial(() => "Loading")
    .onSuccess((message) => message)
    .render()
}
```

The `render()` call returns `null` for unhandled initial or success states and
throws defects or unhandled failures.
Handle expected error tags before `render()`.

## Runtime Atoms

Use `Atom.runtime(layer)` when an atom needs Effect services.
The runtime atom builds a runtime from the layer and exposes helpers:

- `runtime.atom(effect)` for queries
- `runtime.fn(effectFn)` for mutations and commands
- `runtime.pull(stream)` for incremental streams
- `Atom.withReactivity(keys)` for query invalidation

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect } from "effect"

class Users extends Effect.Service<Users>()("app/Users", {
  succeed: {
    findById: (id: string) => Effect.succeed({ id, name: "Ada" })
  }
}) {}

const runtime = Atom.runtime(Users.Default)

const userAtom = runtime.atom(
  Effect.gen(function* () {
    const users = yield* Users
    return yield* users.findById("u-1")
  })
).pipe(Atom.keepAlive)
```

Do not run effects directly inside React components just to access services.
Let the atom runtime own the Effect execution.

## Primitive Selection

| Need | Use |
|---|---|
| plain writable state | `Atom.make(initial)` |
| derived synchronous value | `Atom.make((get) => ...)` or `Atom.map` |
| effectful query | `Atom.make(effect)` or `runtime.atom(effect)` |
| parameterized atom | `Atom.family((key) => atom)` |
| command or mutation | `Atom.fn` or `runtime.fn` |
| persistent KeyValueStore state | `Atom.kvs` |
| side-effect-only mount | `useAtomMount(atom)` |

## Cross-references

See also: [02 Atom.make](02-atom-make.md), [04 Keep Alive](04-keep-alive.md), [05 React Hooks](05-react-hooks.md), [06 Result Builder](06-result-builder.md), [11 Runtime Bridge](11-effect-runtime-bridge.md).
