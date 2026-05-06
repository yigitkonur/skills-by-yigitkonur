# CLI Overview

The `tinacms` CLI from `@tinacms/cli`. Two main commands plus init helpers.

## Main commands

| Command | Purpose |
|---|---|
| `tinacms dev` | Local dev — start the GraphQL server alongside your app |
| `tinacms build` | Compile schema + generate client |

## Init helpers

| Command | Purpose |
|---|---|
| `pnpm dlx @tinacms/cli@latest init` | Bootstrap a new TinaCMS project in current dir |
| `pnpm dlx @tinacms/cli@latest init backend` | Add self-hosted backend scaffolding |

## Common options (across dev + build)

| Flag | Purpose |
|---|---|
| `-c <cmd>` | Wrap a child command |
| `--port <port>` | Tina GraphQL port (default 4001) |
| `--datalayer-port <port>` | Datalayer port (default 9000) |
| `--noWatch` | Don't regenerate on file changes (CI) |
| `--noSDK` | Don't generate the client SDK |
| `--rootPath <path>` | Run from different directory |
| `--noTelemetry` | Don't report anonymous telemetry |
| `-v` / `--verbose` | Verbose output |

## `tinacms build` specific

| Flag | Purpose |
|---|---|
| `--tina-graphql-version <ver>` | Pin GraphQL backend version |
| `--local` | Use local datalayer (good for static-only sites) |
| `--skip-cloud-checks` | Skip TinaCloud connectivity (dangerous) |
| `--skip-search-indexing` | Skip search index build |
| `--no-client-build-cache` | Disable query caching in client build |
| `--clean` | Run schema-strict GraphQL mutations against content files; **purges fields not in the current schema** (commit first) |

## Reading order

| File | Topic |
|---|---|
| `references/cli/02-tinacms-dev.md` | dev command, options |
| `references/cli/03-tinacms-build.md` | build command, flags |
| `references/cli/04-graphql-commands.md` | graphql audit, schema dumps |
| `references/cli/05-init-and-init-backend.md` | init flows |

## Audit / introspection

```bash
pnpm dlx @tinacms/cli@latest audit
```

Schema vs content consistency check. Run after schema changes.

## Verifying

```bash
pnpm tinacms --version
# 2.2.5 or current

pnpm tinacms --help
# Lists all commands and options
```

## Common mistakes

| Mistake | Fix |
|---|---|
| Mismatched `tinacms` and `@tinacms/cli` versions | Pin to matching majors |
| Forgot `-c` to wrap child command | `tinacms dev -c "next dev"` |
| Used in CI without `--noTelemetry` | Add the flag |
| `--skip-cloud-checks` in production | Don't — it skips important validation |
