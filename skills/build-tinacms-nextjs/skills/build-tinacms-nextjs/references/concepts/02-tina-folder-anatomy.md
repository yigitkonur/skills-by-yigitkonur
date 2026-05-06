# The /tina Folder Anatomy

The `tina/` folder at your project root is the entire CMS configuration surface. Everything outside `tina/` (your content, your renderers, your Next.js code) is yours.

## Structure

```
tina/
├── config.{ts,tsx,js}       ← You write this
├── queries/                 ← Optional — custom GraphQL queries
│   └── *.gql
├── database.ts              ← Self-hosted only — DB + git provider config
├── __generated__/           ← Auto-generated — gitignore this
│   ├── _graphql.json        ← GraphQL AST
│   ├── _lookup.json         ← Document name resolution
│   ├── _schema.json         ← Schema AST
│   ├── client.{js,ts}       ← TinaCloud GraphQL client
│   ├── databaseClient.{js,ts}  ← Self-hosted client (only if self-hosted)
│   ├── types.{js,ts}        ← TypeScript types for your schema
│   ├── frags.gql            ← GraphQL fragments
│   ├── queries.gql          ← GraphQL queries
│   └── schema.gql           ← GraphQL variant of your schema
└── tina-lock.json           ← MUST commit — pinned compiled schema
```

## What to commit vs gitignore

| Path | Commit? | Why |
|---|---|---|
| `tina/config.ts` | yes | Your schema source of truth |
| `tina/queries/*` | yes | Custom queries you authored |
| `tina/database.ts` | yes (if self-hosted) | Backend wiring |
| `tina/tina-lock.json` | **YES** | Pinned compiled schema for resolution |
| `tina/__generated__/` | **NO** | Rebuilt on every `tinacms build` |

`.gitignore` snippet:

```gitignore
tina/__generated__/
.tina/__generated__/
```

If you commit `__generated__/` by accident, the next `tinacms build` may produce a diff that fights with whatever you committed. Always exclude the folder.

## What each generated file does

### `client.{ts,js}`

The auto-generated GraphQL client used in your app code. Import as:

```ts
import { client } from '@/tina/__generated__/client'
const result = await client.queries.page({ relativePath: 'home.md' })
```

- For TinaCloud projects this is the only client.
- For self-hosted projects there is also `databaseClient.{ts,js}` which talks directly to your self-hosted backend; use it when calling from server components or API routes.

### `types.{ts,js}`

TypeScript types generated from your schema. Import them for typed renderer props:

```ts
import type { PageQuery } from '@/tina/__generated__/types'
```

### `frags.gql`, `queries.gql`, `schema.gql`

Raw GraphQL the client uses internally. Useful for debugging when a query is wrong — open `queries.gql` to see exactly what is sent. You should not edit these directly.

### `_graphql.json`, `_lookup.json`, `_schema.json`

Internal representations the GraphQL server uses. Don't read or edit them.

## `tina/tina-lock.json`

This file is the **compiled schema** — a serialized representation of `tina/config.ts` after esbuild compiles it. Tina uses it to resolve document content. Commit it.

When you change the schema and run `tinacms dev`, this file regenerates. The git diff is normal. Don't manually edit it.

If `tina/tina-lock.json` is missing from a deployed environment, queries will return errors like "schema not found" or "collection unknown."

## When to read `tina/queries/`

The `queries/` folder is optional. Most queries you need are auto-generated from your schema and live in `__generated__/queries.gql`. You add files here when:

- You need a query that selects fewer fields than the auto-generated one (perf)
- You want a named query for reuse across your app
- You're writing a custom data-fetching function not covered by `client.queries.*`

Files in `queries/` get attached to the same client as the auto-generated ones, so they appear under `client.queries.*` after the next build.

## File location alternatives

The `/tina` folder normally sits at the project root. You can move it (`tinaDirectory` parameter to `createDatabase` in self-hosted, or `--rootPath` flag on the CLI) but most projects keep the default. Keep it at the root unless you have a strong reason.

## Quick verification

After `pnpm tinacms build`:

```bash
ls tina/__generated__/
# Should show: client.ts types.ts frags.gql queries.gql schema.gql + 3 .json files

cat tina/tina-lock.json | head -3
# Should be valid JSON with version + schema metadata
```

If `__generated__/` is missing, the build never ran. If `tina/tina-lock.json` is missing, the schema didn't compile — read `tinacms build` output for the actual error.
