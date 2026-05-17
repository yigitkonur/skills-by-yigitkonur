# TinaCloud API Versioning

TinaCloud's GraphQL API is versioned. By default, you get the current stable version. For long-term compatibility, you can pin to a specific version.

## Default behavior

Without configuration, your app uses the latest stable GraphQL API version. Most projects don't need to think about this.

## When to pin

Pin a version when:

- You're deploying to a long-lived environment (e.g. enterprise project that won't be touched for a year)
- You want to avoid surprise breaking changes
- You're running an older version of TinaCMS that's not compatible with the latest API

## How to pin

In the build flag:

```bash
pnpm tinacms build --tina-graphql-version 1.5.0
```

Or in CI:

```yaml
- run: pnpm tinacms build --tina-graphql-version 1.5.0
```

Replace `1.5.0` with the version you want.

## Where to find versions

TinaCloud documents available versions in **Project Settings → Configuration → API Version**. They release new versions periodically; old versions remain available for backward compatibility.

## Semver compatibility

API versions follow semver. Updates within the same major version are backward compatible:

- `1.5.0` → `1.5.1` — patch (safe)
- `1.5.0` → `1.6.0` — minor (additive features)
- `1.0.0` → `2.0.0` — **major** (potentially breaking)

When a new major version drops, TinaCloud announces a deprecation timeline for the old one.

## Migration between versions

To upgrade from one major to another:

1. Read the migration guide for that version
2. Update `tinacms` and `@tinacms/cli` packages to the matching version
3. Test in a non-production environment
4. Update `--tina-graphql-version` in CI
5. Deploy

## Self-hosted: pin in `database.ts`

For self-hosted projects, pin via `@tinacms/graphql`:

```typescript
// tina/database.ts
import { createDatabase } from '@tinacms/datalayer'
// ...
```

The `@tinacms/datalayer` package version determines the GraphQL backend version. Pin in `package.json`.

## Most projects: don't pin

If you're upgrading TinaCMS regularly (RenovateBot grouping `tinacms*`), the API version stays in sync automatically. Pinning is a defensive measure for slow-moving projects.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Pinned to a version that's been deprecated | Build fails after deprecation date | Migrate to a newer version |
| Mismatched `tinacms` package version and pinned API version | Schema validation errors | Match major versions |
| Used `--skip-cloud-checks` in production | Skips version verification | Don't use in production |
| Forgot to update CI when bumping version | Stale pinned version in CI | Sync local + CI |
