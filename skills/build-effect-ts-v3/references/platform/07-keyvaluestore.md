# KeyValueStore
Use `KeyValueStore` for typed key-value persistence over memory, file-system, or browser storage backends.

## Service Shape

`KeyValueStore.KeyValueStore` is a service tag. It stores strings or byte arrays
and can derive schema-aware stores.

| Method | Use |
|---|---|
| `get(key)` | Read string as `Option<string>` |
| `getUint8Array(key)` | Read bytes as `Option<Uint8Array>` |
| `set(key, value)` | Store string or bytes |
| `remove(key)` | Delete one key |
| `clear` | Delete all entries |
| `size` | Count entries |
| `modify(key, f)` | Update existing string |
| `has(key)` | Check key presence |
| `isEmpty` | Check whether store is empty |
| `forSchema(schema)` | Create schema store |

## Memory Store

```typescript
import { Effect, Option } from "effect"
import { KeyValueStore } from "@effect/platform"

const program = Effect.gen(function* () {
  const store = yield* KeyValueStore.KeyValueStore

  yield* store.set("theme", "dark")
  const theme = yield* store.get("theme")

  return Option.match(theme, {
    onNone: () => "system",
    onSome: (value) => value
  })
})

export const inMemory = program.pipe(
  Effect.provide(KeyValueStore.layerMemory)
)
```

Use memory storage for tests, caches that reset on restart, and simple process
state.

## File-system Store

```typescript
import { Effect, Layer } from "effect"
import { KeyValueStore } from "@effect/platform"
import { NodeContext, NodeKeyValueStore, NodeRuntime } from "@effect/platform-node"

const StoreLive = NodeKeyValueStore.layerFileSystem(".data").pipe(
  Layer.provide(NodeContext.layer)
)

const program = Effect.gen(function* () {
  const store = yield* KeyValueStore.KeyValueStore
  yield* store.set("last-run", new Date(0).toISOString())
})

program.pipe(
  Effect.provide(StoreLive),
  NodeRuntime.runMain
)
```

The portable `KeyValueStore.layerFileSystem(directory)` requires `FileSystem`
and `Path`. Runtime helpers such as `NodeKeyValueStore.layerFileSystem` package
that for the runtime.

## Prefix Stores

```typescript
import { Effect } from "effect"
import { KeyValueStore } from "@effect/platform"

export const saveUserSetting = (userId: string, name: string, value: string) =>
  Effect.gen(function* () {
    const store = yield* KeyValueStore.KeyValueStore
    const userStore = KeyValueStore.prefix(store, `user:${userId}:`)

    yield* userStore.set(name, value)
  })
```

Prefixing prevents unrelated features from sharing accidental key names.

## Schema Store

```typescript
import { Effect, Option, Schema } from "effect"
import { KeyValueStore } from "@effect/platform"

class UserPrefs extends Schema.Class<UserPrefs>("UserPrefs")({
  theme: Schema.Literal("light", "dark"),
  pageSize: Schema.Number
}) {}

export const loadPrefs = Effect.gen(function* () {
  const store = yield* KeyValueStore.KeyValueStore
  const prefsStore = store.forSchema(UserPrefs)

  const prefs = yield* prefsStore.get("prefs")

  return Option.match(prefs, {
    onNone: () => new UserPrefs({ theme: "light", pageSize: 25 }),
    onSome: (value) => value
  })
})
```

Schema stores validate on read and write, so malformed persisted values become
typed parse failures instead of untrusted values in the domain.

## Dedicated Schema Layer

```typescript
import { Effect, Schema } from "effect"
import { KeyValueStore } from "@effect/platform"

class Session extends Schema.Class<Session>("Session")({
  id: Schema.String,
  createdAt: Schema.String
}) {}

const SessionStore = KeyValueStore.layerSchema(Session, "SessionStore")

export const saveSession = Effect.gen(function* () {
  const store = yield* SessionStore.tag
  yield* store.set("current", new Session({
    id: "session-1",
    createdAt: new Date(0).toISOString()
  }))
}).pipe(
  Effect.provide(SessionStore.layer)
)
```

Provide the returned layer with a base `KeyValueStore` layer.

## Anti-patterns

- Storing JSON without a schema when values cross process boundaries.
- Sharing one flat key namespace across unrelated features.
- Using file-system stores without providing `FileSystem` and `Path`.
- Treating missing keys as empty strings.
- Using key-value storage for relational queries.

## Cross-references

See also: [02-filesystem.md](02-filesystem.md), [03-path.md](03-path.md), [04-url.md](04-url.md), [11-node-context.md](11-node-context.md)
