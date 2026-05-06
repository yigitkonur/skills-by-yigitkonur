# Config File Anatomy

`tina/config.ts` is the single configuration surface. It's an ESM module that exports a `defineConfig` call. The CLI bundles it with esbuild and runs it in Node.js — so its imports must be Node-safe.

## Top-level structure

```typescript
import { defineConfig } from 'tinacms'

export default defineConfig({
  branch: '...',                   // which git branch to read/write
  clientId: '...',                 // TinaCloud project ID (or empty for self-hosted)
  token: '...',                    // TinaCloud read-only token
  contentApiUrlOverride: undefined, // set to '/api/tina/gql' for self-hosted

  build: {
    outputFolder: 'admin',         // where the admin SPA writes (relative to publicFolder)
    publicFolder: 'public',        // your Next.js public dir
    basePath: undefined,           // sub-path support — known broken; leave undefined
  },

  server: {
    // Optional: dev-server overrides
  },

  schema: {
    collections: [/* ... */],      // your content types
  },

  ui: {
    previewUrl: undefined,         // function returning preview URLs per branch
  },

  client: {
    // Optional: client-side options
  },

  media: {
    tina: {
      mediaRoot: 'uploads',        // where uploads go in publicFolder
      publicFolder: 'public',
    },
    // OR external provider:
    // loadCustomStore: async () => (await import('next-tinacms-cloudinary')).TinaCloudCloudinaryMediaStore,
  },

  search: {
    // TinaCloud only: built-in fuzzy search
    tina: {
      indexerToken: process.env.TINA_SEARCH_INDEXER_TOKEN,
      stopwordLanguages: ['eng'],
    },
  },

  authProvider: undefined,         // self-hosted only
})
```

## Required vs optional

| Field | Required | Notes |
|---|---|---|
| `branch` | yes | The git branch to operate on |
| `clientId` | yes for TinaCloud | Empty string OK for local-only or self-hosted |
| `token` | yes for TinaCloud | Empty string OK for local-only or self-hosted |
| `build` | yes | At minimum `outputFolder` + `publicFolder` |
| `schema` | yes | At least one collection |
| `media` | yes | Default repo-based or an external loader |
| `contentApiUrlOverride` | self-hosted | `/api/tina/gql` to point at your backend |
| `authProvider` | self-hosted | Frontend auth provider instance |
| `ui` | optional | `previewUrl` for editorial workflow links |
| `search` | optional | TinaCloud fuzzy search |
| `server` | optional | Dev-server tweaks |

## Branch resolution waterfall

```typescript
branch:
  process.env.NEXT_PUBLIC_TINA_BRANCH ||
  process.env.VERCEL_GIT_COMMIT_REF ||
  process.env.HEAD ||
  'main',
```

This is the canonical pattern. See `references/config/04-branch-resolution.md`.

## Schema is the meat

Most of `tina/config.ts` is the `schema.collections` array. See `references/schema/`. Keep schema definitions in separate files (`tina/blocks/<name>.ts`, `tina/collections/<name>.ts`) and import them — `tina/config.ts` becomes thin and easy to scan.

## Imports are Node-safe only

The config file is bundled with esbuild and **runs in Node.js**. It must NOT import:

- React components (anything using JSX runtime, `useState`, `useEffect`)
- Browser APIs (`window`, `document`, `localStorage`)
- CSS, SCSS, image, or other non-JS asset imports
- Component libraries that pull in browser-only deps transitively

Safe to import:

- Type-only imports (`import type { Foo }`)
- Pure data and pure functions
- Other schema files you wrote

If you accidentally import something that uses browser APIs, esbuild fails with `Schema Not Successfully Built`. Move the import out and re-run.

## ESM-only

TinaCMS 3.x is **ESM-only**. The config file must use `import` syntax (not `require`). Either:

- Use `.ts`, `.tsx`, or `.mts` extensions, OR
- Set `"type": "module"` in `package.json`

Otherwise you get `require is not defined` or `ERR_REQUIRE_ESM`.

## TypeScript types

`defineConfig` is fully typed. Hover over any property in your IDE for inline docs. The schema fields use a discriminated union — picking `type: 'string'` constrains the rest of the field to string-specific options.

For type narrowing in your own code:

```typescript
import type { Config } from 'tinacms'
```

## Environment-specific config

You can branch on `process.env.NODE_ENV` or `process.env.TINA_PUBLIC_IS_LOCAL`:

```typescript
const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === 'true'

export default defineConfig({
  // ... shared
  authProvider: isLocal ? new LocalAuthProvider() : new ClerkAuthProvider(),
  contentApiUrlOverride: isLocal ? undefined : '/api/tina/gql',
})
```

Just remember that env vars are evaluated at **build time**, not runtime — flipping a flag after `tinacms build` doesn't change the admin.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Importing a React component into `tina/config.ts` | `Schema Not Successfully Built` | Use type-only import or move the import |
| `require('tinacms')` syntax | `ERR_REQUIRE_ESM` | Switch to `import` |
| Hardcoded `branch: 'main'` | Editorial workflow can't switch branches | Use the env-var waterfall |
| `clientId` and `token` swapped | "Invalid project" errors | Re-check from `app.tina.io` |
| `publicFolder` wrong | Admin assets 404 | Match your Next.js `public/` directory name |
| `outputFolder` not in `public/` | Admin not served at `/admin` | Default to `admin` (relative to `publicFolder`) |

## Reading order

For a full pass through the config:

1. `references/config/02-build-and-server.md` — build + server sections
2. `references/config/03-admin-and-ui.md` — admin route, UI, previewUrl
3. `references/config/04-branch-resolution.md` — the env waterfall
4. `references/config/05-client-and-content-api.md` — client + content API URL
5. `references/config/06-typescript-path-aliases.md` — `@/` aliases in config
