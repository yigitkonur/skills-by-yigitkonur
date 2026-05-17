# React Hooks
Use the React hooks from `@effect-atom/atom-react` to read, write, mount, refresh, subscribe, and suspend atom values.

## Hook Surface

The React package exposes the core hook set:

| Hook | Use |
|---|---|
| `useAtomValue(atom)` | read a value and subscribe to changes |
| `useAtomValue(atom, f)` | read a mapped value |
| `useAtomSet(atom)` | get a setter for writable atoms |
| `useAtom(atom)` | read and write a writable atom |
| `useAtomMount(atom)` | mount an atom for side effects without reading it |
| `useAtomRefresh(atom)` | get a refresh callback |
| `useAtomSubscribe(atom, f)` | run a callback on atom updates |
| `useAtomSuspense(atom)` | suspend on result atoms |
| `useAtomInitialValues(values)` | seed registry values once |

Use the narrowest hook that matches the component.
Read-only components should not receive setters.
Command-only controls should not subscribe to value updates.

## Read Only

Use `useAtomValue` when a component only needs the current value.

```typescript
import { Atom, useAtomValue } from "@effect-atom/atom-react"

const titleAtom = Atom.make("Dashboard").pipe(Atom.keepAlive)

export function PageTitle() {
  const title = useAtomValue(titleAtom)
  return title.toUpperCase()
}
```

The component rerenders when `titleAtom` changes.

## Read With Projection

Use the second argument when the component needs a derived view of one atom.

```typescript
import { Atom, useAtomValue } from "@effect-atom/atom-react"

type Session = {
  readonly userId: string
  readonly roles: ReadonlyArray<string>
}

const sessionAtom = Atom.make<Session>({
  userId: "u-1",
  roles: ["admin"]
}).pipe(Atom.keepAlive)

export function AdminBadge() {
  return useAtomValue(sessionAtom, (session) =>
    session.roles.includes("admin") ? "admin" : "member"
  )
}
```

For multi-atom derivations, define a derived atom outside the component.

## Write Only

Use `useAtomSet` when the component only dispatches a state transition.

```typescript
import { Atom, useAtomSet } from "@effect-atom/atom-react"

const countAtom = Atom.make(0).pipe(Atom.keepAlive)

export function IncrementButton() {
  const setCount = useAtomSet(countAtom)

  return {
    onClick: () => setCount((count) => count + 1)
  }
}
```

This avoids subscribing the button to the count value.

## Read And Write

Use `useAtom` when the UI needs both the value and the setter.

```typescript
import { Atom, useAtom } from "@effect-atom/atom-react"

const queryAtom = Atom.make("").pipe(Atom.keepAlive)

export function SearchBox() {
  const [query, setQuery] = useAtom(queryAtom)

  return {
    value: query,
    onInput: (value: string) => setQuery(value)
  }
}
```

Keep local React state for DOM-only details.
Use atoms for shared state and Effect-integrated state.

## Mount Without Reading

`useAtomMount(atom)` mounts an atom for side effects without reading its value.
Use it for event listeners, app-wide subscriptions, and resource atoms.

```typescript
import { Atom, useAtomMount } from "@effect-atom/atom-react"

const escapeKeyAtom = Atom.make((get) => {
  if (typeof window === "undefined") {
    return 0
  }

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === "Escape") {
      get.setSelf(get.self<number>() + 1)
    }
  }

  window.addEventListener("keydown", onKeyDown)
  get.addFinalizer(() =>
    window.removeEventListener("keydown", onKeyDown)
  )

  return 0
}).pipe(Atom.keepAlive)

export function AppShell() {
  useAtomMount(escapeKeyAtom)
  return "mounted"
}
```

Use this instead of `useAtomValue` when the component does not need the value.

## Refresh

Use `useAtomRefresh` to manually recompute an atom.

```typescript
import { Atom, useAtomRefresh, useAtomValue } from "@effect-atom/atom-react"
import { Effect } from "effect"

const timestampAtom = Atom.make(
  Effect.sync(() => new Date())
)

export function RefreshableTimestamp() {
  const result = useAtomValue(timestampAtom)
  const refresh = useAtomRefresh(timestampAtom)

  return {
    result,
    refresh
  }
}
```

Prefer `reactivityKeys` for cache invalidation after mutations.
Use manual refresh for explicit user actions.

## Promise Mode For Result Setters

Writable result atoms created by `Atom.fn` or `runtime.fn` can be called in
promise mode.

```typescript
import { Atom, useAtomSet } from "@effect-atom/atom-react"
import { Effect } from "effect"

const saveNameAtom = Atom.fn((name: string) =>
  Effect.succeed({ saved: name })
)

export function SaveButton() {
  const saveName = useAtomSet(saveNameAtom, { mode: "promise" })

  return {
    onClick: () => saveName("Ada")
  }
}
```

The promise resolves with the success value.
For full success or failure `Exit`, use mode `promiseExit`.

## Suspense

Use `useAtomSuspense` when the route intentionally delegates loading and failure
handling to React Suspense and an error boundary.

```typescript
import { Atom, useAtomSuspense } from "@effect-atom/atom-react"
import { Effect } from "effect"

const profileAtom = Atom.make(
  Effect.succeed({ id: "u-1", name: "Ada" })
)

export function SuspendedProfile() {
  const profile = useAtomSuspense(profileAtom).value
  return profile.name
}
```

For most application screens, `Result.builder` is easier to audit because every
state is visible in one chain.

## Initial Values

`useAtomInitialValues` seeds registry values once for the active registry.
Use it for hydration or controlled tests.

```typescript
import { Atom, useAtomInitialValues, useAtomValue } from "@effect-atom/atom-react"

const countAtom = Atom.make(0)

export function SeededCounter() {
  useAtomInitialValues([[countAtom, 10]])
  return useAtomValue(countAtom)
}
```

Do not use it as an everyday setter.
Use normal atom setters after initialization.

## Cross-references

See also: [01 Overview](01-overview.md), [02 Atom.make](02-atom-make.md), [06 Result Builder](06-result-builder.md), [07 Side Effect Atoms](07-side-effect-atoms.md), [08 Mutations](08-mutations.md).
