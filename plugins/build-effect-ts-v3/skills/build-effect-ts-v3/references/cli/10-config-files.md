# Config Files
Load JSON, YAML, INI, or TOML configuration into Effect `Config` with `ConfigFile.layer`.

## Purpose

`ConfigFile.layer` installs a `ConfigProvider` that reads configuration files.
Options and args can then use `withFallbackConfig` to read from that provider
when CLI input is missing.

```typescript
import { ConfigFile } from "@effect/cli"
```

The source supports these formats:

| Format | Extension family |
|---|---|
| JSON | `json` |
| YAML | `yaml`, `yml` |
| INI | `ini` |
| TOML | `toml` |

## Layer

```typescript
import { ConfigFile } from "@effect/cli"
import { NodeContext, NodeRuntime } from "@effect/platform-node"
import { Effect, Layer } from "effect"

declare const cli: (args: ReadonlyArray<string>) => Effect.Effect<void, unknown, unknown>

Effect.suspend(() => cli(process.argv)).pipe(
  Effect.provide(Layer.mergeAll(
    NodeContext.layer,
    ConfigFile.layer("myapp")
  )),
  NodeRuntime.runMain
)
```

`ConfigFile.layer("myapp")` searches for supported files named from `myapp`.
The exact selected file becomes the active config provider for `Config`.

## Formats

Limit formats when your app documents only a subset:

```typescript
import { ConfigFile } from "@effect/cli"

const AppConfig = ConfigFile.layer("myapp", {
  formats: ["json", "yaml", "toml"]
})
```

This satisfies the common JSON/YAML/TOML application shape while still using the
v3 source API.

## Search Paths

Use `searchPaths` to restrict lookup:

```typescript
import { ConfigFile } from "@effect/cli"

const AppConfig = ConfigFile.layer("myapp", {
  searchPaths: [".", "./config"],
  formats: ["json", "yaml"]
})
```

Prefer explicit search paths in application CLIs. They make support requests
easier because the lookup behavior is documented in code.

## withFallbackConfig

Config files matter only when an option or arg asks for `Config`:

```typescript
import { Args, Command, Options } from "@effect/cli"
import { Config, Effect } from "effect"

const profile = Options.text("profile").pipe(
  Options.withFallbackConfig(Config.string("PROFILE")),
  Options.withDefault("dev")
)

const repository = Args.text({ name: "repository" }).pipe(
  Args.withFallbackConfig(Config.string("REPOSITORY"))
)

const command = Command.make("clone", { profile, repository }, (config) =>
  Effect.logInfo(`profile=${config.profile} repository=${config.repository}`)
)
```

If the CLI value is present, config-file lookup is not used for that value.

## Config File Shape

For the keys above, a JSON file can look like this:

```json
{
  "PROFILE": "prod",
  "REPOSITORY": "effect"
}
```

Use the same key names as the `Config` descriptors unless you intentionally
nest or transform providers.

## makeProvider

Use `ConfigFile.makeProvider` when you need the provider as a value:

```typescript
import { ConfigFile } from "@effect/cli"
import { Config, Effect } from "effect"

const program = Effect.gen(function*() {
  const provider = yield* ConfigFile.makeProvider("myapp", {
    formats: ["json", "yaml"]
  })
  return yield* Config.string("PROFILE").pipe(
    Effect.withConfigProvider(provider)
  )
})
```

Most applications should prefer `ConfigFile.layer` at the runtime edge.

## Errors

Config-file loading can fail with `ConfigFileError` if the file cannot be read
or parsed. Keep that failure at startup; do not hide it behind a broad default
unless the configuration is genuinely optional.

```typescript
import { ConfigFile } from "@effect/cli"

const layer = ConfigFile.layer("optional-app", {
  formats: ["json"]
})
```

When a config file is optional, document the behavior with fallback defaults on
individual options.

## Cross-references

See also: [04 Options Combinators](04-options-combinators.md), [06 Args Combinators](06-args-combinators.md), [09 Providing Services](09-providing-services.md), [11 Fallbacks](11-fallbacks.md)
