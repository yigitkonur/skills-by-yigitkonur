# Config Collections
Use collection constructors when one logical configuration value contains repeated values, sets, maps, or nested repeated records.

## Constructors

Effect Config has collection constructors for repeated configuration data.
The element config describes one item.
The collection name describes where the sequence or map lives.

| Constructor | Result type | Use when |
|---|---|---|
| `Config.array(config, name)` | `Array<A>` | Order and duplicates matter |
| `Config.chunk(config, name)` | `Chunk.Chunk<A>` | You want Effect's immutable chunk |
| `Config.hashSet(config, name)` | `HashSet.HashSet<A>` | Uniqueness matters |
| `Config.hashMap(config, name)` | `HashMap.HashMap<string, A>` | Dynamic child keys map to values |
| `Config.repeat(config)` | `Array<A>` | The surrounding config supplies the collection path |

The default flat provider can load simple collections from delimited strings.
`ConfigProvider.fromMap` can also load indexed and nested collection paths.

## Arrays

Use arrays when order and duplicates are meaningful.
Pass the item config without a name when the collection name owns the key.

```typescript
import { Config, Effect } from "effect"

const AllowedOrigins = Config.array(Config.string(), "ALLOWED_ORIGINS")

export const program = Effect.gen(function*() {
  const origins = yield* AllowedOrigins
  yield* Effect.logInfo(`Configured ${origins.length} allowed origins`)
})
```

With the default provider, a simple value can be supplied as a sequence.
With `fromMap`, sequence delimiters and indexed paths are provider concerns.

## Arrays of records

Collection items can be structs.
This is useful for repeated endpoints, workers, accounts, or routing rules.

```typescript
import { Config } from "effect"

const Replica = Config.all({
  host: Config.string("host"),
  port: Config.port("port")
})

const Replicas = Config.array(Replica, "replicas")
```

For map providers, indexed paths look like `replicas[0].host` and `replicas[0].port`.
The source tests for `ConfigProvider` use this shape for arrays of records.

## Chunks

Use `Config.chunk` when the rest of the codebase already works with `Chunk`.
It avoids converting from an array after loading.

```typescript
import { Chunk, Config, Effect } from "effect"

const SeedUrls = Config.chunk(Config.url(), "SEED_URLS").pipe(
  Config.withDefault(Chunk.empty())
)

export const program = Effect.gen(function*() {
  const urls = yield* SeedUrls
  yield* Effect.logInfo(`Loaded ${Chunk.size(urls)} seed URLs`)
})
```

`Chunk` is immutable and efficient for Effect-style collection workflows.
Use arrays when standard JavaScript array APIs are the natural fit.

## Hash sets

Use `Config.hashSet` when duplicates should collapse.
The result is `HashSet.HashSet<A>`.

```typescript
import { Config, Effect, HashSet } from "effect"

const AdminEmails = Config.hashSet(Config.nonEmptyString(), "ADMIN_EMAILS")

export const program = Effect.gen(function*() {
  const emails = yield* AdminEmails
  yield* Effect.logInfo(`Loaded ${HashSet.size(emails)} admin emails`)
})
```

Hash sets make intent clear.
If duplicates are meaningful operationally, use `Config.array` instead.

## Hash maps

Use `Config.hashMap` when the source has dynamic child keys.
The keys are strings.
The values are parsed by the element config.

```typescript
import { Config, Effect, HashMap } from "effect"

const ServicePorts = Config.hashMap(Config.port(), "SERVICE_PORTS")

export const program = Effect.gen(function*() {
  const ports = yield* ServicePorts
  yield* Effect.logInfo(`Loaded ${HashMap.size(ports)} service ports`)
})
```

For a flat map provider, child keys become part of the path.
For example, a map entry can represent `SERVICE_PORTS.api` and `SERVICE_PORTS.web`.
The exact delimiter comes from the provider.

## Validation with collections

Validate after constructing the collection when the constraint applies to the whole collection.
Validate the element config when the constraint applies to each item.

```typescript
import { Config } from "effect"

const Host = Config.nonEmptyString().pipe(
  Config.validate({
    message: "host must include a dot",
    validation: (host) => host.includes(".")
  })
)

const Hosts = Config.array(Host, "HOSTS").pipe(
  Config.validate({
    message: "at least one host is required",
    validation: (hosts) => hosts.length > 0
  })
)
```

Element validation reports the item path.
Collection validation reports the collection path.

## Defaults for collections

Use an empty default only when an empty collection is a valid operating mode.
Do not hide missing required routing tables or credentials behind empty defaults.

```typescript
import { Config } from "effect"

const OptionalOrigins = Config.array(Config.string(), "OPTIONAL_ORIGINS").pipe(
  Config.withDefault([])
)
```

If absence should change behavior, `Config.option` may communicate intent better.

## Checklist

- Use unnamed element configs when the collection name owns the path.
- Use arrays for ordered data.
- Use chunks for Effect collection workflows.
- Use hash sets for uniqueness.
- Use hash maps for dynamic child keys.
- Validate elements and collections at the right level.
- Prefer provider overrides in tests.

## Cross-references

See also: [basic config](02-basic-config.md), [all and nested](05-config-all-nested.md), [validation](06-config-validation.md), [providers](08-config-providers.md).
