# Path
Use `Path` for portable path manipulation, file URL conversion, and runtime-specific path semantics.

## Service Shape

`Path.Path` is a service tag. The service mirrors the stable parts of path
manipulation without tying business code to a host module.

Common operations:

| Method | Use |
|---|---|
| `join(...parts)` | Join path segments |
| `resolve(...parts)` | Build absolute path |
| `dirname(path)` | Parent directory |
| `basename(path, suffix?)` | Final segment |
| `extname(path)` | File extension |
| `relative(from, to)` | Relative path |
| `normalize(path)` | Normalize separators and segments |
| `parse(path)` | Split into root, dir, base, ext, name |
| `format(parsed)` | Build a path from parsed fields |
| `toFileUrl(path)` | Convert path to `URL` |
| `fromFileUrl(url)` | Convert file URL to path |

## Runtime Layers

```typescript
import { Effect } from "effect"
import { Path } from "@effect/platform"
import { NodePath, NodeRuntime } from "@effect/platform-node"

const program = Effect.gen(function* () {
  const path = yield* Path.Path
  const file = path.join("reports", "daily.txt")
  yield* Effect.logInfo(path.resolve(file))
})

program.pipe(
  Effect.provide(NodePath.layer),
  NodeRuntime.runMain
)
```

`Path.layer` from `@effect/platform` is POSIX and works everywhere. Node also
offers `NodePath.layer`, `NodePath.layerPosix`, and `NodePath.layerWin32`.

## Cross-platform Composition

Keep path operations inside the effect so tests can choose the path layer.

```typescript
import { Effect } from "effect"
import { FileSystem, Path } from "@effect/platform"

export const readWorkspaceFile = (workspace: string, name: string) =>
  Effect.gen(function* () {
    const fs = yield* FileSystem.FileSystem
    const path = yield* Path.Path

    const file = path.join(workspace, name)
    const normalized = path.normalize(file)

    return yield* fs.readFileString(normalized)
  })
```

This helper can be tested with `NodePath.layerPosix` or `NodePath.layerWin32`
without changing its implementation.

## File URL Conversion

`toFileUrl` and `fromFileUrl` can fail with `BadArgument`, so they return
effects.

```typescript
import { Effect } from "effect"
import { Path } from "@effect/platform"

export const describeFileUrl = (file: string) =>
  Effect.gen(function* () {
    const path = yield* Path.Path
    const url = yield* path.toFileUrl(file)
    const roundTrip = yield* path.fromFileUrl(url)

    return {
      href: url.href,
      roundTrip
    }
  })
```

Use these methods instead of string-prefixing `file://`.

## Parsing

`parse` returns a structured value. `format` rebuilds from a partial parsed
object.

```typescript
import { Effect } from "effect"
import { Path } from "@effect/platform"

export const withExtension = (file: string, extension: string) =>
  Effect.gen(function* () {
    const path = yield* Path.Path
    const parsed = path.parse(file)

    return path.format({
      dir: parsed.dir,
      name: parsed.name,
      ext: extension
    })
  })
```

Use this when replacing extensions; manual splitting is fragile around hidden
files, multiple dots, and platform separators.

## Testing Path Behavior

```typescript
import { Effect } from "effect"
import { Path } from "@effect/platform"
import { NodePath } from "@effect/platform-node"

const fileName = Effect.gen(function* () {
  const path = yield* Path.Path
  return path.basename(path.join("tmp", "data.json"))
})

export const posixName = fileName.pipe(Effect.provide(NodePath.layerPosix))
export const win32Name = fileName.pipe(Effect.provide(NodePath.layerWin32))
```

If code makes OS-specific assumptions, pin the layer in tests and document the
contract.

## Anti-patterns

- Concatenating path strings with separators.
- Assuming POSIX behavior in reusable libraries.
- Converting file URLs with string replacement.
- Mixing direct host path calls with `Path.Path` in the same module.
- Providing a runtime path layer deep inside helpers.

## Cross-references

See also: [01-overview.md](01-overview.md), [02-filesystem.md](02-filesystem.md), [04-url.md](04-url.md), [11-node-context.md](11-node-context.md)
