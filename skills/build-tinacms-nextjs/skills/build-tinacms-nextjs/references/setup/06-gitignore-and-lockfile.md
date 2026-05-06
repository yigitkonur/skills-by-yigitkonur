# Gitignore and Lockfile

What to commit, what to ignore. Getting this wrong causes bizarre deployment failures and noisy git diffs.

## What you MUST commit

| Path | Why |
|---|---|
| `tina/config.ts` (or `.tsx`/`.js`) | Your schema source of truth |
| `tina/queries/**` | Custom GraphQL queries you wrote |
| `tina/database.ts` (self-hosted) | Backend wiring |
| `tina/tina-lock.json` | **Pinned compiled schema** — runtime needs this |
| `package.json` | Pinned exact TinaCMS versions |
| `pnpm-lock.yaml` | Reproducible installs |
| `content/**` | Your actual CMS-managed content |

## What you MUST gitignore

| Path | Why |
|---|---|
| `tina/__generated__/` | Auto-rebuilt on every `tinacms build` |
| `.tina/__generated__/` | Older path — gitignore both for safety |
| `node_modules/` | Standard |
| `.env.local` | Secrets |

## Required `.gitignore` snippet

Add to your existing `.gitignore` (don't replace; merge):

```gitignore
# TinaCMS
tina/__generated__/
.tina/__generated__/

# Standard Next.js
.next/
node_modules/
.env.local
.env*.local

# Optional: local TinaCMS database snapshot
tina/tina-lock-local.json
```

## Why `tina/tina-lock.json` MUST be committed

`tina/tina-lock.json` is the **compiled schema** — a serialized JSON representation of `tina/config.ts` after esbuild runs. The TinaCMS GraphQL server reads it at runtime to resolve content documents.

If `tina/tina-lock.json` is missing in a deployed environment:

```
ERROR: Schema not found
ERROR: Cannot resolve collection 'page'
```

Always commit it. The git diff is normal whenever you change the schema.

## Why `tina/__generated__/` must NOT be committed

The `__generated__/` folder is **rebuilt every time `tinacms build` runs**. If you commit it:

- Your CI's `tinacms build` produces a different output than your local commit
- You get a stale generated client deployed
- Git diffs become unmanageable (every commit shows churn)
- Production may fail with "type mismatch" errors

`tinacms build` regenerates it — never manually edit or commit it.

## What the build produces

After `pnpm tinacms build` you should see:

```
tina/__generated__/
├── client.{js,ts}          ← TinaCloud client
├── databaseClient.{js,ts}  ← Self-hosted client (only if self-hosted)
├── types.{js,ts}           ← TypeScript types
├── frags.gql               ← Internal fragments
├── queries.gql             ← Generated queries
├── schema.gql              ← Schema in GraphQL format
├── _graphql.json           ← Internal AST
├── _lookup.json            ← Document lookup table
└── _schema.json            ← Internal schema state
```

None of these are checked in. Run `pnpm tinacms build` after a fresh clone to regenerate.

## The fresh-clone workflow

When a teammate clones the repo for the first time:

```bash
git clone <repo>
cd <repo>
pnpm install
pnpm tinacms build   # OR pnpm dev (which also builds)
pnpm dev
```

Without that `tinacms build`, TypeScript shows "Cannot find module '@/tina/__generated__/client'" everywhere.

## CI workflow

CI never has the `__generated__/` folder. Always run `tinacms build` first:

```yaml
- run: pnpm install --frozen-lockfile
- run: pnpm tinacms build       # generates types
- run: pnpm next build          # uses types
```

If your `package.json` `build` script chains them properly (`tinacms build && next build`), `pnpm build` is enough.

## Lockfile rules

- **Use one lockfile.** If you've used both `npm install` and `pnpm install`, delete `package-lock.json` (npm's) and keep `pnpm-lock.yaml`.
- **Commit the lockfile.** Reproducible builds need it.
- **Pin exact TinaCMS versions in `package.json`** (no `^` or `~`):

```json
{
  "dependencies": {
    "tinacms": "3.7.5",
    "@tinacms/cli": "2.2.5"
  }
}
```

The TinaCMS admin SPA assets are CDN-served and may drift if you let caret ranges float.

## Common mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Committed `__generated__/` | CI build produces stale types; type drift | `git rm -r tina/__generated__/`, add to `.gitignore`, recommit |
| Forgot to commit `tina/tina-lock.json` | Production "schema not found" | `git add tina/tina-lock.json && git commit && redeploy` |
| Both `package-lock.json` and `pnpm-lock.yaml` present | Inconsistent installs across team | Delete one, regenerate from package.json |
| `^tinacms` caret range | Admin UI version drifts from local CLI | Pin exact: `"tinacms": "3.7.5"` |
| Committed `.env.local` with real secrets | Token leak | Rotate token; remove from git history |

## Quick verification

```bash
# Should show __generated__ ignored, tina/tina-lock.json tracked
git status
git ls-files tina/tina-lock.json

# Should show pinned versions (no ^ or ~)
grep '"tinacms"\|"@tinacms"' package.json

# Should NOT show __generated__ committed
git ls-files tina/__generated__/  # should output nothing
```
