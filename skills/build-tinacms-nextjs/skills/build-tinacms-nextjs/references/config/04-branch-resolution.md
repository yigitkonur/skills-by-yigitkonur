# Branch Resolution

The `branch` field in `tina/config.ts` tells TinaCMS which git branch to read/write. Picking the right value matters for editorial workflow, preview deployments, and multi-environment projects.

## Canonical waterfall

```typescript
import { defineConfig } from 'tinacms'

export default defineConfig({
  branch:
    process.env.NEXT_PUBLIC_TINA_BRANCH ||
    process.env.VERCEL_GIT_COMMIT_REF ||
    process.env.HEAD ||
    'main',
  // ...
})
```

The waterfall handles four scenarios:

| Scenario | Var that matches | Resolved to |
|---|---|---|
| Editorial workflow / explicit branch override | `NEXT_PUBLIC_TINA_BRANCH` | Whatever you set |
| Vercel deploy (preview or prod) | `VERCEL_GIT_COMMIT_REF` | Branch the deploy was triggered from |
| Netlify deploy | `HEAD` | Branch the deploy was triggered from |
| Local dev / no env vars | none | `main` (fallback) |

## Why each var

### `NEXT_PUBLIC_TINA_BRANCH`

Explicit override. Set this to force a specific branch regardless of where the build runs. Useful when:

- Deploying a staging environment that always tracks `staging`
- Running CI builds where you want content from a specific branch
- Locally pointing at a non-default branch

### `VERCEL_GIT_COMMIT_REF`

Set automatically by Vercel for every deployment, including preview deployments per branch. With this fallback:

- Deploying `main` → Tina reads from `main`
- Pushing a feature branch → Vercel preview points Tina at that feature branch automatically
- Editorial workflow branches each get their own Tina view

### `HEAD`

Netlify's equivalent. Same effect.

### `'main'` literal

Last-resort fallback for local dev where no CI env var is set.

## Editorial Workflow: per-branch isolation

When editorial workflow is enabled (TinaCloud Team Plus+), editors create branches like `tina/draft-2026-05-08-abc123`. Each editor gets:

- Their own DB index (TinaCloud namespaces by branch)
- Their own preview URL (via `previewUrl`)
- Their own commit history

For this to work, `branch` must resolve to **the editor's branch**, not a hardcoded value. The waterfall above handles this — `VERCEL_GIT_COMMIT_REF` resolves to the right branch in each preview deployment.

## Self-hosted: namespace per branch

For self-hosted projects, the database adapter should namespace by branch too:

```typescript
// tina/database.ts
const branchName = process.env.GITHUB_BRANCH ||
                   process.env.VERCEL_GIT_COMMIT_REF ||
                   'main'

createDatabase({
  databaseAdapter: new MongodbLevel({
    collectionName: `tinacms-${branchName}`,
    // ...
  }),
  // ...
  namespace: branchName,
})
```

Without `namespace`, all branches share one DB index and step on each other.

## Custom branches

For staging environments:

```bash
# .env on the staging server
NEXT_PUBLIC_TINA_BRANCH=staging
```

Editors hitting `/admin` on the staging deployment write to the `staging` branch. Production deployment uses `main`.

## Multiple environments table

| Environment | Where to set | What |
|---|---|---|
| Local dev | `.env` | Skip — falls through to `main` |
| Staging deploy on Vercel | Vercel env (Preview only) | `NEXT_PUBLIC_TINA_BRANCH=staging` |
| Production deploy on Vercel | Vercel env (Production) | Either set `NEXT_PUBLIC_TINA_BRANCH=main` or omit and rely on `VERCEL_GIT_COMMIT_REF` |
| Per-feature preview | Nothing — Vercel auto | `VERCEL_GIT_COMMIT_REF` matches branch |
| Editorial workflow branch | Nothing — Vercel auto | TinaCloud uses the branch via the same `VERCEL_GIT_COMMIT_REF` |

## Common mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Hardcoded `branch: 'main'` | Editorial workflow edits go to `main` (no branch isolation) | Use the env-var waterfall |
| `NEXT_PUBLIC_TINA_BRANCH=production` (wrong branch name) | "Branch not found" errors | Use actual git branch names |
| Forgot to set in Vercel for staging | Staging writes to `main` | Set in Vercel env scoped to Preview |
| Self-hosted without `namespace` in createDatabase | Two branches share the same DB index, cross-contaminate | Add `namespace: branchName` |

## Verification

```typescript
// Add a temp log to tina/config.ts to see which branch resolved:
const branch =
  process.env.NEXT_PUBLIC_TINA_BRANCH ||
  process.env.VERCEL_GIT_COMMIT_REF ||
  process.env.HEAD ||
  'main'
console.log('[Tina] Resolved branch:', branch)
```

Check the Vercel deploy logs after each deploy to confirm the right branch resolved. Remove the log after verifying.
