# `tinacms build`

Compile schema, generate client + types, validate config. Run before any framework build.

## Standard usage

```bash
tinacms build
```

Or in `package.json`:

```json
{
  "scripts": {
    "build": "tinacms build && next build"
  }
}
```

`tinacms build` MUST run before `next build` — it generates types the framework build needs.

## What it does

1. Bundles `tina/config.ts` with esbuild
2. Validates the schema
3. Generates `tina/__generated__/`:
   - `client.{ts,js}` (TinaCloud GraphQL client)
   - `databaseClient.{ts,js}` (self-hosted client, if applicable)
   - `types.{ts,js}` (TypeScript types)
   - `frags.gql`, `queries.gql`, `schema.gql`
   - `_graphql.json`, `_lookup.json`, `_schema.json`
4. Updates `tina-lock.json` (compiled schema)
5. (Optional) Validates against TinaCloud
6. (Optional) Builds search index

## Common flags

```bash
tinacms build [options]
```

| Flag | Purpose |
|---|---|
| `--noWatch` | Don't watch files (good for CI) |
| `--noSDK` | Skip client generation |
| `--noTelemetry` | Skip anonymous telemetry |
| `--local` | Use local datalayer only (offline build) |
| `--skip-cloud-checks` | Don't validate against TinaCloud (dangerous in production) |
| `--skip-search-indexing` | Skip search index |
| `--no-client-build-cache` | Disable query caching |
| `--tina-graphql-version <ver>` | Pin API version |
| `-v` | Verbose |

## CI usage

```yaml
# GitHub Actions
- run: pnpm install --frozen-lockfile
- run: pnpm tinacms build --noTelemetry
- run: pnpm next build
  env:
    NEXT_PUBLIC_TINA_CLIENT_ID: ${{ secrets.TINA_CLIENT_ID }}
    TINA_TOKEN: ${{ secrets.TINA_TOKEN }}
```

For multi-step CI, separate the commands. For monolithic Vercel-style builds, rely on the package.json `build` script.

## `--local` mode

```bash
tinacms build --local
```

Use when:

- Building for static-only sites that don't connect to TinaCloud at runtime
- CI without TinaCloud credentials
- Air-gapped environments

`--local` skips TinaCloud connectivity check and generates a local-only client. Pages are pre-rendered from local content files.

## `--skip-cloud-checks`

```bash
tinacms build --skip-cloud-checks
```

Skips:

- TinaCloud connectivity validation
- Project ID validation
- Token validation

**Don't use in production** — these checks catch misconfigurations early. Only use for local dev offline builds.

## Build failures

| Error | Cause | Fix |
|---|---|---|
| `Schema Not Successfully Built` | Frontend imports in `tina/config.ts` | Keep config Node-safe |
| `Cannot find module '../tina/__generated__/client'` | `tinacms build` didn't run | Run before framework build |
| `Project not found` | Wrong `NEXT_PUBLIC_TINA_CLIENT_ID` | Re-check |
| `ESM error` (`require is not defined`) | Using CommonJS syntax | Switch to ESM (`import`) |
| Field name invalid | Hyphen or reserved name | Fix per `references/schema/03-naming-rules.md` |

## Verifying

```bash
pnpm tinacms build

# After:
ls tina/__generated__/
# client.ts  databaseClient.ts  types.ts  frags.gql  queries.gql  schema.gql  _graphql.json  ...

cat tina-lock.json | head -3
# Should be valid JSON
```

If any of these is missing, the build didn't complete — read the output for the actual error.

## Performance

For typical projects (< 100 collections, < 5k docs): 5-30 seconds.

For very large schemas (500+ collections): minutes. Consider running schema validation locally first to catch errors early.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgot to run before `next build` | "Cannot find module '../tina/__generated__/client'" | Add to `build` script |
| Used `--skip-cloud-checks` in production | Misconfigurations missed | Remove flag |
| `--noWatch` in dev | Schema changes don't apply | Use only in CI |
| Dev's `__generated__/` committed accidentally | Build runs in CI but commits stale state | Gitignore the folder |
| Used `tinacms build` instead of `tinacms dev` for local dev | Local dev no longer hot-reloads | Use `dev` for development |
