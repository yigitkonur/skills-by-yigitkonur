# Keep Alive
Use `Atom.keepAlive` whenever atom state or resources must outlive the current set of mounted consumers.

## Default Disposal

Atoms are disposable by default.
When no mounted consumer needs an atom, Effect Atom can dispose the atom node and
run finalizers.

This is correct for many UI-local atoms:

- temporary route state
- expandable row state
- one dialog's local draft
- event listener active only on one screen
- effectful queries that should stop when the screen unmounts

It is wrong for shared app state.
If losing the last mounted component should not reset the value, use
`Atom.keepAlive`.

## Canonical Pattern

Pipe a long-lived atom through `Atom.keepAlive` at definition time.

```typescript
import { Atom } from "@effect-atom/atom-react"

type Preferences = {
  readonly density: "compact" | "comfortable"
  readonly colorScheme: "light" | "dark"
}

export const preferencesAtom = Atom.make<Preferences>({
  density: "comfortable",
  colorScheme: "dark"
}).pipe(Atom.keepAlive)
```

Do not apply keep-alive from the component.
The lifecycle is part of the atom definition.

## Global State Rule

For long-lived global state, always pipe through `Atom.keepAlive`.

Use it for:

- authenticated user summary
- feature-flag snapshots
- organization or workspace selection
- app preferences
- persistent websocket state
- runtime layers shared by many screens
- cache entries intended to survive route transitions

Skip it for:

- field state owned by a mounted form
- a hover or popover atom
- row expansion state in a virtualized table
- a side-effect atom that should stop when the screen leaves

## Keep Alive In Families

Families create atoms per key.
Each returned atom can be keep-alive or disposable.

```typescript
import { Atom } from "@effect-atom/atom-react"

const workspaceSelectionAtom = Atom.family((accountId: string) =>
  Atom.make({ workspaceId: "default" }).pipe(Atom.keepAlive)
)
```

This retains values per account id.
Only use this when retaining every touched key is intentional.

## Keep Alive With Runtime Queries

Effectful global queries should use keep-alive when their successful value is
shared across route changes.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect } from "effect"

class Session extends Effect.Service<Session>()("app/Session", {
  succeed: {
    currentUser: Effect.succeed({ id: "u-1", name: "Ada" })
  }
}) {}

const runtime = Atom.runtime(Session.Default)

export const currentUserAtom = runtime.atom(
  Effect.gen(function* () {
    const session = yield* Session
    return yield* session.currentUser
  })
).pipe(Atom.keepAlive)
```

The component still handles `Result` states.
Keep-alive only controls lifetime.

## Keep Alive Is Not Persistence

`Atom.keepAlive` keeps an atom node alive in the registry.
It does not write to browser storage, a database, or a server.

Use:

- `Atom.keepAlive` for in-memory lifetime
- `Atom.kvs` for platform KeyValueStore persistence
- `Atom.searchParam` for URL persistence
- server-backed queries for durable remote state

Do not describe keep-alive as local storage.

## Side-Effect Resources

Keep-alive side-effect atoms keep their resource mounted as long as the registry
lives.
That can be correct for app-wide keyboard shortcuts or online status.

```typescript
import { Atom } from "@effect-atom/atom-react"

export const onlineStatusAtom = Atom.make((get) => {
  if (typeof window === "undefined") {
    return true
  }

  const update = () => get.setSelf(window.navigator.onLine)

  window.addEventListener("online", update)
  window.addEventListener("offline", update)
  get.addFinalizer(() => {
    window.removeEventListener("online", update)
    window.removeEventListener("offline", update)
  })

  return window.navigator.onLine
}).pipe(Atom.keepAlive)
```

Even with keep-alive, finalizers still matter.
They run when the registry tears down or the atom is rebuilt.

## Review Checklist

- Shared state uses keep-alive at definition time.
- Disposable screen state does not use keep-alive by habit.
- Family keep-alive is justified per key.
- Persistence is implemented with `Atom.kvs` or another storage boundary.
- Side-effect atoms still register finalizers.
- Result handling is not skipped because the atom is keep-alive.

## Cross-references

See also: [01 Overview](01-overview.md), [03 Atom Families](03-atom-families.md), [07 Side Effect Atoms](07-side-effect-atoms.md), [10 LocalStorage](10-atoms-with-localstorage.md), [11 Runtime Bridge](11-effect-runtime-bridge.md).
