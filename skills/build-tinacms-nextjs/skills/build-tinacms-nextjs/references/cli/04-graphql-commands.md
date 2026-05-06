# GraphQL Commands

The CLI exposes a few GraphQL-specific commands beyond `dev` and `build`.

## `audit`

```bash
pnpm dlx @tinacms/cli@latest audit
```

Validates schema vs content. Reports:

- Field-name violations (hyphens, reserved names)
- Path mismatches (collection `path` doesn't match disk)
- Missing `_template` in multi-shape collection docs
- Unsupported GraphQL constructs
- Documents that don't match their collection schema

Run after every schema change or content migration.

## `admin reindex` (self-hosted only)

```bash
pnpm tinacms admin reindex
```

Force reindex from git into the DB. Use when:

- Git changed outside the admin (manual push, automation)
- DB index drifted from git
- Migrated to a new DB adapter

## Schema introspection

After `tinacms build`, the schema is dumped to `tina/__generated__/schema.gql`:

```bash
cat tina/__generated__/schema.gql
```

Use this for:

- IDE plugins (GraphQL extensions like Apollo or GraphQL.tools)
- Schema-first tooling (codegen, documentation generators)
- Debugging "what does my schema actually look like"

## Query inspection

`tina/__generated__/queries.gql` shows the queries TinaCMS uses internally:

```bash
cat tina/__generated__/queries.gql
```

Useful for:

- Understanding what fields the auto-generated client selects
- Copying queries into custom queries
- Performance tuning (selecting fewer fields)

## Init

```bash
pnpm dlx @tinacms/cli@latest init
```

Bootstraps a new project. Creates:

- `tina/config.ts`
- `app/admin/[[...index]]/page.tsx`
- Updates `package.json` scripts

## Init backend (self-hosted)

```bash
pnpm dlx @tinacms/cli@latest init backend
```

Adds:

- `tina/database.ts`
- `app/api/tina/[...routes]/route.ts`
- Required dependencies for self-hosted

Run after `init` if you're going self-hosted.

## Migration commands (Forestry)

Forestry migration tooling has been retired. For Forestry → TinaCMS:

- Manually rename hyphenated frontmatter (`hero-image:` → `hero_image:`)
- Recreate the schema in `tina/config.ts`
- See [TinaCMS Forestry migration archive](https://tina.io/docs/forestry/) (if still available)

## CLI version

```bash
pnpm dlx @tinacms/cli@latest --version
# 2.2.5
```

Pin the same major as `tinacms`:

```json
{
  "dependencies": { "tinacms": "3.7.5" },
  "devDependencies": { "@tinacms/cli": "2.2.5" }
}
```

Mismatched majors = obscure errors.

## Common mistakes

| Mistake | Fix |
|---|---|
| Skipped `audit` after schema changes | Run regularly to catch issues early |
| Used `admin reindex` on TinaCloud project | TinaCloud handles indexing automatically — only for self-hosted |
| Mismatched `tinacms` and `@tinacms/cli` majors | Pin to same major |
| Tried to migrate from Forestry without renaming fields | Schema fails | Rename hyphenated fields first |
