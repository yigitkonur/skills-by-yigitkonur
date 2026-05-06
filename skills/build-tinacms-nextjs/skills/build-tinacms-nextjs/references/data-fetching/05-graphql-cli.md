# GraphQL CLI Commands

CLI commands for inspecting, auditing, and rebuilding the TinaCMS GraphQL layer.

## Audit

```bash
pnpm dlx @tinacms/cli@latest audit
```

Checks:

- Schema vs content consistency
- Field name validity (no hyphens, no reserved names)
- Path mismatches between collection `path` and disk
- Missing `_template` in documents from multi-shape collections
- Unsupported GraphQL constructs

Run after every schema change. The audit produces a report; fix issues before deploy.

## Build

```bash
pnpm tinacms build
```

Compiles `tina/config.ts` into:

- `tina/__generated__/{schema,graphql,lookup}.json`
- `tina/__generated__/{client,types}.{js,ts}`
- `tina/__generated__/{frags,queries,schema}.gql`
- `tina/tina-lock.json` (compiled schema)

Run after every schema change. `pnpm dev` does this automatically; for CI you do it manually.

## Build flags

```bash
pnpm tinacms build [options]
```

| Flag | Purpose |
|---|---|
| `--port <port>` | Override Tina GraphQL port (default 4001) |
| `--datalayer-port <port>` | Override datalayer port (default 9000) |
| `--noWatch` | Don't regenerate on file changes (good for CI) |
| `--noSDK` | Don't generate the client SDK |
| `--rootPath <path>` | Run from a different directory |
| `--noTelemetry` | Don't report anonymous telemetry |
| `--tina-graphql-version <ver>` | Pin a specific GraphQL backend version (advanced) |
| `--local` | Use local datalayer (good for static-only sites) |
| `--skip-cloud-checks` | Skip TinaCloud connectivity validation (dangerous) |
| `--skip-search-indexing` | Skip search index build |
| `--no-client-build-cache` | Disable query caching in client build |
| `-v`, `--verbose` | Verbose output |

For most projects, no flags. For CI:

```bash
pnpm tinacms build --noWatch --noTelemetry
```

For CI without TinaCloud connectivity:

```bash
pnpm tinacms build --local
```

## Dev

```bash
pnpm tinacms dev -c "<your-dev-command>"
```

Starts:

1. Tina GraphQL server (default port 4001)
2. The wrapped child command (e.g. `next dev`)

Same flags as `build`, plus:

| Flag | Purpose |
|---|---|
| `-c <cmd>` | Wrap a child command (run alongside) |

## Init / Init backend

```bash
pnpm dlx @tinacms/cli@latest init
```

Bootstrap a new TinaCMS project. Creates `tina/config.ts`, admin route, package scripts.

```bash
pnpm dlx @tinacms/cli@latest init backend
```

Adds self-hosted backend scaffolding — `tina/database.ts`, `app/api/tina/[...routes]/route.ts`. Run after `init` if you're going self-hosted.

## Other useful commands

```bash
# Check installed versions
pnpm list tinacms @tinacms/cli @tinacms/datalayer

# Print schema in GraphQL format
cat tina/__generated__/schema.gql

# Print queries TinaCMS is using internally
cat tina/__generated__/queries.gql
```

## Migration commands (Forestry → TinaCMS)

```bash
# Old, retired. The Forestry migration is no longer documented.
# For migrating from Forestry, see TinaCMS' archived migration guide
# or just rename hyphenated frontmatter fields to snake_case manually.
```

## Versioning

`@tinacms/cli` is versioned alongside `tinacms`. Mismatched majors break the build. Pin both to the same major:

```json
{
  "dependencies": { "tinacms": "3.7.5" },
  "devDependencies": { "@tinacms/cli": "2.2.5" }
}
```

Group them in RenovateBot/Dependabot.

## CI integration

```yaml
# .github/workflows/build.yml
- run: pnpm install --frozen-lockfile
- run: pnpm tinacms build --noTelemetry
- run: pnpm next build
```

Or rely on the `package.json` `build` script:

```yaml
- run: pnpm install --frozen-lockfile
- run: pnpm build  # which runs `tinacms build && next build`
```

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Skipping `tinacms build` in CI | "Cannot find module '../tina/__generated__/client'" | Run `pnpm tinacms build` first |
| Using `tinacms dev` in CI | Loads localhost-pointing admin into production | Always use `tinacms build` for CI |
| Mismatched `tinacms` and `@tinacms/cli` versions | Build errors, schema drift | Pin to matching majors |
| Forgot `--noTelemetry` in CI | Reports build to TinaCloud (no actual issue, just opt-out) | Add the flag |
| Used `--skip-cloud-checks` in production | Deploys with broken cloud config | Don't use in production CI |
