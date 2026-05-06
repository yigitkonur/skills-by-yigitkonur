# Atoms With LocalStorage
Use `Atom.kvs` with `BrowserKeyValueStore.layerLocalStorage` when browser localStorage should be schema-backed Effect state.

## Preferred Persistence Path

Effect Atom provides `Atom.kvs` for persistent atom state backed by
`KeyValueStore`.
In browser React apps, use the platform browser localStorage layer.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { BrowserKeyValueStore } from "@effect/platform-browser"
import { Schema } from "effect"

const storageRuntime = Atom.runtime(
  BrowserKeyValueStore.layerLocalStorage
)

export const sidebarOpenAtom = Atom.kvs({
  runtime: storageRuntime,
  key: "app.sidebar.open",
  schema: Schema.Boolean,
  defaultValue: () => true
}).pipe(Atom.keepAlive)
```

This keeps parsing and encoding at the storage boundary.
The UI works with a typed atom value.

## Structured Values

Use an Effect Schema for structured preferences.

```typescript
import { Atom } from "@effect-atom/atom-react"
import { BrowserKeyValueStore } from "@effect/platform-browser"
import { Schema } from "effect"

const Preferences = Schema.Struct({
  density: Schema.Literal("compact", "comfortable"),
  showHints: Schema.Boolean
})

type Preferences = typeof Preferences.Type

const runtime = Atom.runtime(BrowserKeyValueStore.layerLocalStorage)

export const preferencesAtom = Atom.kvs({
  runtime,
  key: "app.preferences",
  schema: Preferences,
  defaultValue: (): Preferences => ({
    density: "comfortable",
    showHints: true
  })
}).pipe(Atom.keepAlive)
```

The default value should be cheap and deterministic.

## Reading And Writing

`Atom.kvs` returns a writable atom.
Use the normal hooks.

```typescript
import { useAtom } from "@effect-atom/atom-react"

export function PreferencesPanel() {
  const [preferences, setPreferences] = useAtom(preferencesAtom)

  return {
    preferences,
    setCompact: () =>
      setPreferences((current) => ({
        ...current,
        density: "compact"
      }))
  }
}
```

Do not add a second local state mirror.
The atom is already the state source.

## Keep Alive And Persistence

Persistence and keep-alive solve different problems.

| Concern | Tool |
|---|---|
| keep current value in the registry | `Atom.keepAlive` |
| write value to browser storage | `Atom.kvs` |
| validate stored value | `Schema` |
| share state between components | React hooks over the atom |

Use both for global preferences:

```typescript
import { Atom } from "@effect-atom/atom-react"

const persistedThemeAtom = Atom.kvs({
  runtime: storageRuntime,
  key: "app.theme",
  schema: Schema.Literal("light", "dark"),
  defaultValue: () => "dark"
}).pipe(Atom.keepAlive)
```

The storage read happens through the Effect runtime.
The keep-alive rule prevents route transitions from resetting the registry
node.

## Avoid Manual Storage Parsing

Do not put raw storage parsing in components.
Do not duplicate schema validation after the value has reached the atom.

Manual storage access is only appropriate when a codebase has no platform
KeyValueStore layer available.
Even then, keep parsing at the boundary and expose a typed atom.

## SSR Notes

Browser localStorage is a browser-only resource.
The platform browser layer should be provided only in browser runtimes.
For server rendering, seed initial values or render a stable default until the
client registry mounts.

Do not read browser globals during module evaluation.
Let the atom runtime and platform layer own storage access.

## Review Checklist

- Persistent browser atoms use `Atom.kvs`.
- Schemas come from `import { Schema } from "effect"`.
- Global persisted preferences use `Atom.keepAlive`.
- Components read and write through normal atom hooks.
- Stored values are not parsed ad hoc in React components.
- Storage keys are stable and namespaced.

## Cross-references

See also: [04 Keep Alive](04-keep-alive.md), [05 React Hooks](05-react-hooks.md), [07 Side Effect Atoms](07-side-effect-atoms.md), [09 Cache Invalidation](09-cache-invalidation.md), [11 Runtime Bridge](11-effect-runtime-bridge.md).
