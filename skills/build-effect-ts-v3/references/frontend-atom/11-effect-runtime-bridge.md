# Effect Runtime Bridge
Use Atom runtimes for React state, and capture Effect runtimes only at explicit integration edges.

## Two Runtime Bridges

React frontends meet Effect in two common places:

- Effect Atom runtime: `Atom.runtime(layer)` for atoms and hooks
- explicit Effect runtime capture: `Effect.runtime<Deps>()` for non-atom APIs

Use the Atom runtime for stateful React queries and mutations.
Use explicit runtime capture for APIs that demand a Promise callback, such as
AI SDK tool execution.

## Atom.runtime For React State

`Atom.runtime(layer)` builds a runtime atom from a layer.
Its helpers run effects under Atom ownership.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect } from "effect"

class Projects extends Effect.Service<Projects>()("app/Projects", {
  succeed: {
    list: Effect.succeed([
      { id: "p-1", name: "Compiler" }
    ])
  }
}) {}

const runtime = Atom.runtime(Projects.Default)

export const projectsAtom = runtime.atom(
  Effect.gen(function* () {
    const projects = yield* Projects
    return yield* projects.list
  })
).pipe(Atom.keepAlive)
```

Components read `projectsAtom` through `useAtomValue`.
They do not run the Effect directly.

## runtime.fn For Commands

Use `runtime.fn` for commands that need services.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { Effect } from "effect"

class Projects extends Effect.Service<Projects>()("app/Projects", {
  succeed: {
    rename: (id: string, name: string) =>
      Effect.succeed({ id, name })
  }
}) {}

const runtime = Atom.runtime(Projects.Default)

export const renameProjectAtom = runtime.fn(
  (input: { readonly id: string; readonly name: string }) =>
    Effect.gen(function* () {
      const projects = yield* Projects
      return yield* projects.rename(input.id, input.name)
    }),
  { reactivityKeys: ["projects"] }
)
```

The result atom carries waiting and failure state.

## Registry Providers

Most apps can use the default registry.
Use `RegistryProvider` when you need scoped state, test isolation, or initial
values.

```typescript
import { Atom, RegistryProvider, useAtomValue } from "@effect-atom/atom-react"
import { Layer } from "effect"
import * as React from "react"

type ProjectsService = {
  readonly _tag: "ProjectsService"
}

declare const runtime: Atom.AtomRuntime<ProjectsService>
declare const ProjectsLayer: Layer.Layer<ProjectsService>
declare const projectsAtom: Atom.Atom<ReadonlyArray<string>>

function ProjectsText() {
  const projects = useAtomValue(projectsAtom)
  return projects.join(",")
}

export function TestHarness() {
  return React.createElement(RegistryProvider, {
    initialValues: [
      Atom.initialValue(runtime.layer, ProjectsLayer)
    ],
    children: React.createElement(ProjectsText)
  })
}
```

Prefer the package's provider components in actual React code.
The key idea is that the registry is the unit of atom state isolation.

## Explicit Runtime Capture

Some libraries do not know about atoms.
They ask for an async callback.
At that boundary, build a factory that captures an Effect runtime.

```typescript
import { Effect, Runtime } from "effect"

class Inventory extends Effect.Service<Inventory>()("app/Inventory", {
  succeed: {
    reserve: (sku: string) =>
      Effect.succeed({ sku, reserved: true })
  }
}) {}

export const makeReserve = Effect.gen(function* () {
  const runtime = yield* Effect.runtime<Inventory>()

  return (sku: string) =>
    Runtime.runPromise(runtime)(
      Effect.gen(function* () {
        const inventory = yield* Inventory
        return yield* inventory.reserve(sku)
      })
    )
})
```

The runtime capture satisfies the service requirement once.
The returned callback is safe to give to Promise-based APIs.

## Do Not Capture Runtime In Render

Runtime capture is an Effect workflow.
Do it in a service factory, route loader, server action, tool factory, or module
initialization Effect.

Do not start building runtimes in React render.
For React state, use Atom runtime helpers.
For Promise callback APIs, capture the runtime before constructing callbacks.

## Choosing The Bridge

| Need | Bridge |
|---|---|
| React reads query result | `runtime.atom` plus `useAtomValue` |
| React dispatches command | `runtime.fn` plus `useAtomSet` |
| side-effect-only atom | `useAtomMount` |
| Vercel AI SDK tool execute callback | `Effect.runtime<Deps>()` plus `Runtime.runPromise` |
| test-specific service layer | registry initial values or test layer |

## Cross-references

See also: [01 Overview](01-overview.md), [05 React Hooks](05-react-hooks.md), [08 Mutations](08-mutations.md), [09 Cache Invalidation](09-cache-invalidation.md), [12 Vercel AI SDK](12-vercel-ai-sdk.md).
