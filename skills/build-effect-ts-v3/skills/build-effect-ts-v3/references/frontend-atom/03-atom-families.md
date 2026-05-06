# Atom Families
Use `Atom.family` when one atom definition must produce stable per-key atom instances.

## Why Families Exist

Atoms are reference values.
If a screen needs one atom per entity, route, tab, modal, or query key, creating
new atoms ad hoc breaks reuse.

`Atom.family` turns a key into a stable atom factory.
The same key returns the same atom identity while it is retained.

```typescript
import { Atom } from "@effect-atom/atom-react"

const modalOpenAtom = Atom.family((id: string) =>
  Atom.make(false)
)
```

Use a family instead of a component-local atom when keyed state must survive
re-renders.

## Per-Entity State

The common case is entity-specific UI state.

```typescript
import { Atom, useAtom } from "@effect-atom/atom-react"

type DrawerState = {
  readonly open: boolean
  readonly selectedTab: "details" | "history"
}

const drawerAtom = Atom.family((userId: string) =>
  Atom.make<DrawerState>({
    open: false,
    selectedTab: "details"
  })
)

export function UserDrawerButton(props: { readonly userId: string }) {
  const [state, setState] = useAtom(drawerAtom(props.userId))

  return {
    open: state.open,
    toggle: () =>
      setState((current) => ({
        ...current,
        open: !current.open
      }))
  }
}
```

The family key appears in the component props.
The atom definition remains outside the component.

## Effectful Family Queries

Use a family around `runtime.atom` for service-backed per-key queries.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect } from "effect"

type User = {
  readonly id: string
  readonly name: string
}

class Users extends Effect.Service<Users>()("app/Users", {
  succeed: {
    findById: (id: string) => Effect.succeed<User>({ id, name: "Ada" })
  }
}) {}

const runtime = Atom.runtime(Users.Default)

export const userAtom = Atom.family((id: string) =>
  runtime.atom(
    Effect.gen(function* () {
      const users = yield* Users
      return yield* users.findById(id)
    })
  )
)
```

The result type is per-key but the implementation is shared.

## Key Design

Choose keys that are stable and equality-friendly.

Good keys:

- primitive ids
- `Data.Class` values
- stable records normalized before construction
- strings that encode route or query identity

Risky keys:

- object literals created during render
- arrays constructed inline
- values containing functions
- values containing mutable class instances

When the key is structured, make it explicit.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Data } from "effect"

class ProjectQuery extends Data.Class<{
  readonly orgId: string
  readonly projectId: string
}> {}

const projectPanelAtom = Atom.family((query: ProjectQuery) =>
  Atom.make({ expanded: false })
)
```

This makes equality and hashing behavior intentional.

## Keep Alive Per Key

Keep-alive rules still apply inside a family.
If each key represents long-lived global state, pipe each created atom through
`Atom.keepAlive`.

```typescript
import { Atom } from "@effect-atom/atom-react"

const draftAtom = Atom.family((documentId: string) =>
  Atom.make("").pipe(Atom.keepAlive)
)
```

Use this sparingly.
A family of keep-alive atoms can retain a large number of entries.
Prefer disposable family atoms for ephemeral rows, popovers, and temporary
screen state.

## Family With Derived State

Families can return derived atoms.
This is useful for slices of a global collection.

```typescript
import { Atom } from "@effect-atom/atom-react"

type Todo = {
  readonly id: string
  readonly title: string
}

const todosAtom = Atom.make<ReadonlyArray<Todo>>([]).pipe(
  Atom.keepAlive
)

const todoByIdAtom = Atom.family((id: string) =>
  Atom.make((get) =>
    get(todosAtom).find((todo) => todo.id === id)
  )
)
```

If absence is domain-significant, prefer an `Option.Option<Todo>` result in the
domain type.

## Family With Commands

Families work for command atoms too.
Use this when the command is naturally keyed.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect } from "effect"

const saveFieldAtom = Atom.family((fieldName: string) =>
  Atom.fn((value: string) =>
    Effect.log(`saving ${fieldName}`, { value })
  )
)
```

For service-backed mutations, use `runtime.fn` inside the family.

## Review Checklist

- The family is defined outside components.
- The key is primitive or intentionally comparable.
- Long-lived per-key atoms use `Atom.keepAlive`.
- Short-lived per-key atoms stay disposable.
- Service-backed family queries use `runtime.atom`.
- Mutation families expose setters through `useAtomSet`.
- The family does not hide ad hoc object literals from render.

## Cross-references

See also: [02 Atom.make](02-atom-make.md), [04 Keep Alive](04-keep-alive.md), [05 React Hooks](05-react-hooks.md), [08 Mutations](08-mutations.md), [09 Cache Invalidation](09-cache-invalidation.md).
