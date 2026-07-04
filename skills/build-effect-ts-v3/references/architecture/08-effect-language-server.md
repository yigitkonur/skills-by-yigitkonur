# Effect Language Server
Install the Effect Language Service so architecture mistakes in effects, services, and layers surface while editing.

## Why It Belongs In Architecture

The Effect Language Service is not just editor polish. It understands Effect
types and can show requirement leaks, layer graphs, service dependencies,
floating effects, unnecessary generators, and version conflicts. That makes it a
guardrail for architecture, especially around `Layer.provide` versus
`Layer.provideMerge`.

The official examples include `@effect/language-service` in development
dependencies and add the TypeScript plugin in `tsconfig.base.json`.

## Install

Install in the package that owns the TypeScript project. In a monorepo, install
at the root if the root `tsconfig` owns project references.

```bash
pnpm add -D @effect/language-service
```

Equivalent package manager commands are fine. The important part is that the
package is installed in the workspace where TypeScript loads plugins.

## tsconfig.json Plugin Setup

Add the plugin under `compilerOptions.plugins`:

```json
{
  "compilerOptions": {
    "strict": true,
    "moduleResolution": "NodeNext",
    "module": "NodeNext",
    "target": "ES2022",
    "plugins": [
      {
        "name": "@effect/language-service"
      }
    ]
  }
}
```

If the project uses a base config, put the plugin in the base config so every
referenced project inherits it:

```json
{
  "compilerOptions": {
    "strict": true,
    "exactOptionalPropertyTypes": true,
    "noUncheckedIndexedAccess": false,
    "plugins": [
      {
        "name": "@effect/language-service"
      }
    ]
  }
}
```

This matches the shape used by the official examples.

## Editor Requirement

Configure the editor to use the workspace TypeScript version. The plugin runs
inside TypeScript, so an editor-bundled TypeScript server will not load the
project plugin reliably.

For VS Code-compatible editors:

1. Open a TypeScript file.
2. Select the TypeScript version in the status bar.
3. Choose the workspace TypeScript version.

## What It Catches

The language service helps with:

- Effect values that are created but not yielded, returned, or run at the edge;
- layer requirement leaks;
- service dependency graphs;
- layer composition graphs;
- catch handlers on effects that cannot fail;
- redundant `Effect.gen` or `pipe` usage;
- multiple Effect versions in one project.

Use it together with `tsc -b`; do not treat it as a replacement for tests.

## Layer.provide Versus Layer.provideMerge

The most expensive architecture mistake in large Effect apps is losing a layer
output that another part of the app still needs.

```typescript
import { Context, Layer } from "effect"

class Config extends Context.Tag("Config")<Config, { readonly port: number }>() {}
class Logger extends Context.Tag("Logger")<Logger, { readonly name: string }>() {}
class Database extends Context.Tag("Database")<Database, { readonly connected: boolean }>() {}

declare const ConfigLive: Layer.Layer<Config>
declare const LoggerLive: Layer.Layer<Logger, never, Config>
declare const DatabaseLive: Layer.Layer<Database, never, Config>

const LoggerWithConfig = LoggerLive.pipe(Layer.provideMerge(ConfigLive))
const DatabaseWithConfig = DatabaseLive.pipe(Layer.provide(LoggerWithConfig))
```

`LoggerWithConfig` still outputs `Config`, so `DatabaseLive` can receive it.
If `Layer.provide` is used where `Layer.provideMerge` is needed, `Config` may be
removed from the output and the next layer will still require it. The language
service can show the remaining requirement at edit time instead of leaving the
mistake until a later type-check.

## Floating Effect Diagnostic

A common architecture bug is constructing an Effect in a handler and not
returning or yielding it:

```typescript
import { Effect } from "effect"

export const handler = Effect.gen(function* () {
  yield* Effect.logInfo("starting handler")
  return "ok"
})
```

If `Effect.logInfo("starting handler")` is written without `yield*`, the
language service reports a floating Effect. That matters because unexecuted
effects often hide missing persistence, missing logging, or missing policy
checks.

## Build-Time Diagnostics

The language service can also patch the local TypeScript installation so
diagnostics appear during type-checking:

```bash
effect-language-service patch
```

Teams that want this consistently can add a prepare script:

```json
{
  "scripts": {
    "prepare": "effect-language-service patch"
  }
}
```

Keep this as a team decision because it modifies the local TypeScript package in
the workspace.

## Cross-references

See also: [overview.md](01-overview.md), [hexagonal-architecture.md](03-hexagonal-architecture.md), [../services-layers/11-layer-providemerge.md](../services-layers/11-layer-providemerge.md), [../anti-patterns/13-layer-provide-confusion.md](../anti-patterns/13-layer-provide-confusion.md), [../core/05-generators.md](../core/05-generators.md).
