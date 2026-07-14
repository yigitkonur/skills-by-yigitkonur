# Config All And Nested
Use Config.all to build typed structs or tuples and Config.nested to prefix a group under a provider path.

## Config.all

`Config.all` combines configs.
With a struct input, the result is a typed object.
With an array input, the result is a typed tuple or array.
Use structs for service configuration because named fields are easier to maintain.

```typescript
import { Config } from "effect"

const ServerConfig = Config.all({
  host: Config.string("HOST"),
  port: Config.port("PORT"),
  enableCompression: Config.boolean("ENABLE_COMPRESSION")
})
```

The type is inferred as:

```typescript
{
  readonly host: string
  readonly port: number
  readonly enableCompression: boolean
}
```

The config is still only a description until it is yielded or loaded.

## Struct composition

Compose smaller configs into larger configs when the domain has natural subgroups.
Do not load each subgroup separately and stitch values manually in service code.

```typescript
import { Config } from "effect"

const HttpConfig = Config.all({
  host: Config.string("HOST"),
  port: Config.port("PORT")
})

const MetricsConfig = Config.all({
  enabled: Config.boolean("METRICS_ENABLED"),
  endpoint: Config.url("METRICS_ENDPOINT")
})

const AppConfig = Config.all({
  http: HttpConfig,
  metrics: MetricsConfig
})
```

This preserves the full error structure and allows the provider to load the whole shape consistently.

## Config.nested

`Config.nested("NAME")` adds a path prefix to every primitive inside a config.
It can be used as a pipeable combinator or as a direct two-argument call.

```typescript
import { Config } from "effect"

const DatabaseConfig = Config.all({
  host: Config.string("HOST"),
  port: Config.port("PORT"),
  database: Config.nonEmptyString("NAME")
}).pipe(Config.nested("DATABASE"))
```

With the default environment provider, child names are prefixed as:

- `DATABASE_HOST`
- `DATABASE_PORT`
- `DATABASE_NAME`

That exact prefixing rule is a key point for this mission.

## Multiple nested levels

Multiple nesting calls add multiple path segments.
With the default env provider, the path segments are joined with underscores.
With `ConfigProvider.fromMap`, the default delimiter is a dot.

```typescript
import { Config } from "effect"

const Password = Config.redacted("PASSWORD").pipe(
  Config.nested("PRIMARY"),
  Config.nested("DATABASE")
)
```

For the default env provider, this reads `DATABASE_PRIMARY_PASSWORD`.
For a map provider with default settings, this reads `DATABASE.PRIMARY.PASSWORD`.

## Mixing nested and root fields

Use nested configs for grouped fields while leaving root fields at the root.
This is common for service configs that combine server settings with database settings.

```typescript
import { Config } from "effect"

const DatabaseConfig = Config.all({
  host: Config.string("HOST"),
  port: Config.port("PORT")
}).pipe(Config.nested("DATABASE"))

const AppConfig = Config.all({
  serviceName: Config.nonEmptyString("SERVICE_NAME"),
  database: DatabaseConfig,
  logLevel: Config.logLevel("LOG_LEVEL")
})
```

This expects root keys for `SERVICE_NAME` and `LOG_LEVEL`.
It expects database keys below the `DATABASE` prefix.

## Nested collections

Nesting works with collections too.
Apply nesting to the collection config when the whole collection is under a prefix.

```typescript
import { Config } from "effect"

const Replica = Config.all({
  host: Config.string("host"),
  port: Config.port("port")
})

const ReadReplicas = Config.array(Replica, "replicas").pipe(
  Config.nested("database")
)
```

For a map provider, indexed keys can look like `database.replicas[0].host`.
For environment variables, choose a provider path and casing strategy deliberately.

## Error paths

`Config.nested` preserves useful error paths.
If a nested database port is invalid, the error path includes the nested segments.
That makes startup failures actionable.

```typescript
import { Config } from "effect"

const PositivePort = Config.integer("PORT").pipe(
  Config.validate({
    message: "PORT must be positive",
    validation: (port) => port > 0
  }),
  Config.nested("DATABASE")
)
```

An invalid value reports the path as `DATABASE` then `PORT`.
Do not flatten names manually if you want nested error paths.

## Naming guidance

- Use uppercase names for default environment keys.
- Use camel case or lower case when your map or JSON source uses those names.
- Prefer `Config.nested("DATABASE")` over repeating `"DATABASE_HOST"` and `"DATABASE_PORT"` manually.
- Keep a nested struct's internal names local to that group.
- Use provider transforms when the source convention differs.

## Avoid manual prefixing

This works but loses the structural intent:

```typescript
import { Config } from "effect"

const DatabaseConfig = Config.all({
  host: Config.string("DATABASE_HOST"),
  port: Config.port("DATABASE_PORT")
})
```

Prefer:

```typescript
import { Config } from "effect"

const DatabaseConfig = Config.all({
  host: Config.string("HOST"),
  port: Config.port("PORT")
}).pipe(Config.nested("DATABASE"))
```

Both can read the same environment keys.
Only the nested version states that `HOST` and `PORT` belong to one database group.

## Cross-references

See also: [overview](01-overview.md), [basic config](02-basic-config.md), [collections](04-config-collections.md), [providers](08-config-providers.md), [test provider layer](09-layer-set-config-provider.md).
