# Side Effect Atoms
Use side-effect atoms for browser event listeners and subscriptions, and always register cleanup with `get.addFinalizer`.

## When To Use A Side-Effect Atom

Side-effect atoms are useful when React needs state from an external source:

- browser events
- online or visibility status
- media query matches
- websocket connection state
- interval-driven ticks
- imperative third-party subscriptions

The atom owns the subscription.
React components read or mount it.

## Event Listener Pattern

Use `Atom.make((get) => ...)`.
Register the listener, update self through the atom context, and add a
finalizer.

```typescript
import { Atom } from "@effect-atom/atom-react"

export const scrollYAtom = Atom.make((get) => {
  if (typeof window === "undefined") {
    return 0
  }

  const update = () => get.setSelf(window.scrollY)

  window.addEventListener("scroll", update)
  get.addFinalizer(() =>
    window.removeEventListener("scroll", update)
  )

  return window.scrollY
})
```

If the listener is app-wide, pipe through `Atom.keepAlive`.
If it should run only while a screen is mounted, leave it disposable.

## Mount Without Reading

Some atoms exist for their side effects and do not need to drive render.
Mount them with `useAtomMount`.

```typescript
import { Atom, useAtomMount } from "@effect-atom/atom-react"
import { Effect } from "effect"

const shortcutAtom = Atom.make((get) => {
  if (typeof window === "undefined") {
    return 0
  }

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === "/") {
      get.setSelf(get.self<number>() + 1)
    }
  }

  window.addEventListener("keydown", onKeyDown)
  get.addFinalizer(() =>
    window.removeEventListener("keydown", onKeyDown)
  )

  return 0
}).pipe(Atom.keepAlive)

const shortcutLogAtom = Atom.make((get) =>
  Effect.log("shortcut mounted", { count: get(shortcutAtom) })
)

export function AppShortcuts() {
  useAtomMount(shortcutLogAtom)
  return "shortcuts"
}
```

Use `useAtomMount(atom)` when mounting is the goal.
Use `useAtomValue(atom)` only when render needs the value.

## Finalizers Are Required

Every registration should have a matching finalizer.
The finalizer runs when the atom node is disposed or rebuilt.

Common pairs:

| Register | Finalizer |
|---|---|
| `addEventListener` | `removeEventListener` |
| websocket subscribe | unsubscribe or close |
| timer start | clear timer |
| third-party subscribe | returned unsubscribe |
| Effect scoped resource | Effect finalizer |

Do not rely on component unmount cleanup when the resource belongs to an atom.

## Effect Finalizers

Effectful atoms receive a scope.
Use Effect finalizers for resources acquired in Effect code.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect } from "effect"

const scopedAtom = Atom.make(
  Effect.gen(function* () {
    yield* Effect.addFinalizer(() =>
      Effect.log("atom finalized")
    )
    return "ready"
  })
)
```

Use atom context finalizers for synchronous browser registrations.
Use Effect finalizers for scoped Effect resources.

## SSR Guards

Browser globals are unavailable during server rendering.
Guard side-effect atoms that touch `window`, `document`, storage, or browser
events.

```typescript
import { Atom } from "@effect-atom/atom-react"

export const viewportAtom = Atom.make((get) => {
  if (typeof window === "undefined") {
    return { width: 0, height: 0 }
  }

  const read = () => ({
    width: window.innerWidth,
    height: window.innerHeight
  })

  const update = () => get.setSelf(read())

  window.addEventListener("resize", update)
  get.addFinalizer(() =>
    window.removeEventListener("resize", update)
  )

  return read()
})
```

The server value should be harmless and deterministic.

## Keep Alive Decision

Use keep-alive for app-wide subscriptions:

- online status
- visibility
- authenticated websocket
- global keyboard shortcuts

Leave disposable for screen-specific subscriptions:

- route-local scroll watcher
- details panel resize observer
- preview player events
- one modal's external subscription

Lifecycle should match the resource cost.

## Cross-references

See also: [04 Keep Alive](04-keep-alive.md), [05 React Hooks](05-react-hooks.md), [08 Mutations](08-mutations.md), [09 Cache Invalidation](09-cache-invalidation.md), [10 LocalStorage](10-atoms-with-localstorage.md).
